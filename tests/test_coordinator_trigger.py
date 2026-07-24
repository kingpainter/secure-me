"""Integration tests for real (sensor-caused) alarm trigger -> module dispatch.

Covers a v1.5.0 production bug: when the alarm was triggered by a real
sensor breach while armed (ZoneManager -> coordinator._zone_triggered ->
state_machine.trigger_entry_delay -> STATE_ALARM_TRIGGERED), the state
machine transitioned correctly, but _execute_modules_trigger() -- which
actually calls siren.async_trigger(), camera.async_trigger(), etc. -- was
NEVER invoked. It was only ever called from coordinator.async_trigger(),
which nothing in the real sensor-breach path calls. Result: on an actual
break-in the alarm state went to "triggered" and the notification fired,
but the siren never sounded, cameras never activated, lights never
flashed, and locks never engaged.

These tests exercise the REAL ZoneManager, AlarmStateMachine and
SecureMeCoordinator classes together (per the project's own testing rule:
no "mirror" re-implementations that can silently drift from production
behaviour), covering both trigger paths:

  1. An instant zone (ZONE_TYPE_INSTANT) -- alarm fires immediately.
  2. An entry zone (ZONE_TYPE_ENTRY) -- alarm fires after the entry-delay
     countdown completes in the background task.

Also covers the related fix: self._triggered_by and self._last_triggered
must be populated correctly for a real sensor trigger (previously only
set for a manual secure_me.trigger service call), and the module dispatch
must run exactly once per triggered cycle even though _state_changed can
be invoked from multiple code paths.
"""
# VERSION = "1.5.0"

import asyncio

import pytest
from unittest.mock import AsyncMock

from custom_components.secure_me.coordinator import SecureMeCoordinator
from custom_components.secure_me.const import (
    ZONE_TYPE_INSTANT,
    ZONE_TYPE_ENTRY,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_TRIGGERED,
)

from .conftest import MockConfigEntry


@pytest.fixture
async def coordinator(hass):
    """Build a real SecureMeCoordinator with short delays for fast tests."""
    config_entry = MockConfigEntry(data={
        "code": "1234",
        "exit_delay": 0,     # arm immediately, no exit-delay countdown to wait for
        "entry_delay": 1,    # short entry delay so the countdown path is fast
    })
    coord = SecureMeCoordinator(hass, config_entry)

    # Replace the siren module's async_trigger with a spy so we can assert
    # it was actually called, without depending on real HA siren services.
    coord.modules["siren"].async_trigger = AsyncMock(return_value=True)

    yield coord

    await coord.async_shutdown()


def _add_zone(coord, zone_id, zone_type, sensor="binary_sensor.test_sensor"):
    coord.zone_manager.add_zone(
        zone_id=zone_id,
        zone_type=zone_type,
        sensors=[sensor],
        enabled=True,
        arm_modes=["away"],
    )


@pytest.mark.asyncio
async def test_instant_zone_trigger_dispatches_siren(hass, coordinator):
    """A real sensor breach on an instant zone must call siren.async_trigger()."""
    _add_zone(coordinator, "zone_instant", ZONE_TYPE_INSTANT)
    armed = await coordinator.async_arm_away(skip_delay=True)
    assert armed is True
    assert coordinator.alarm_state == STATE_ALARM_ARMED_AWAY

    zone = coordinator.zone_manager.get_zone("zone_instant")
    zone.update_sensor_state("binary_sensor.test_sensor", True)

    await coordinator._zone_triggered(zone)

    assert coordinator.alarm_state == STATE_ALARM_TRIGGERED
    coordinator.modules["siren"].async_trigger.assert_awaited_once()


@pytest.mark.asyncio
async def test_instant_zone_trigger_sets_triggered_by_and_timestamp(hass, coordinator):
    """triggered_by must reflect the real zone, not be stale/empty, and
    last_triggered must be populated -- both previously only worked for a
    manual secure_me.trigger service call.
    """
    _add_zone(coordinator, "zone_instant", ZONE_TYPE_INSTANT)
    await coordinator.async_arm_away(skip_delay=True)

    zone = coordinator.zone_manager.get_zone("zone_instant")
    zone.update_sensor_state("binary_sensor.test_sensor", True)

    assert coordinator.last_triggered is None
    await coordinator._zone_triggered(zone)

    assert coordinator.triggered_by is not None
    assert "zone_instant" in coordinator.triggered_by
    assert "binary_sensor.test_sensor" in coordinator.triggered_by
    assert coordinator.last_triggered is not None


@pytest.mark.asyncio
async def test_entry_delay_trigger_dispatches_siren_after_countdown(hass, coordinator):
    """An entry zone must still dispatch modules once the entry-delay
    countdown completes in the background -- this is the trickier path,
    since the transition to TRIGGERED happens later, outside the call that
    started the countdown.
    """
    _add_zone(coordinator, "zone_entry", ZONE_TYPE_ENTRY)
    await coordinator.async_arm_away(skip_delay=True)

    zone = coordinator.zone_manager.get_zone("zone_entry")
    zone.update_sensor_state("binary_sensor.test_sensor", True)

    await coordinator._zone_triggered(zone)
    # Entry delay is 1s in this fixture -- state should be "pending" now,
    # and the siren must NOT have fired yet.
    coordinator.modules["siren"].async_trigger.assert_not_awaited()

    await asyncio.sleep(1.3)

    assert coordinator.alarm_state == STATE_ALARM_TRIGGERED
    coordinator.modules["siren"].async_trigger.assert_awaited_once()
    assert coordinator.triggered_by is not None
    assert "zone_entry" in coordinator.triggered_by


@pytest.mark.asyncio
async def test_module_dispatch_fires_exactly_once_per_trigger_cycle(hass, coordinator):
    """_state_changed can be invoked more than once while state stays
    TRIGGERED (e.g. countdown/health events) -- module dispatch must not
    re-fire every time.
    """
    _add_zone(coordinator, "zone_instant", ZONE_TYPE_INSTANT)
    await coordinator.async_arm_away(skip_delay=True)

    zone = coordinator.zone_manager.get_zone("zone_instant")
    zone.update_sensor_state("binary_sensor.test_sensor", True)
    await coordinator._zone_triggered(zone)

    # Calling _state_changed again with the same TRIGGERED state (simulating
    # e.g. a re-entrant notify) must not dispatch the siren a second time.
    await coordinator._state_changed(STATE_ALARM_TRIGGERED, 0)

    coordinator.modules["siren"].async_trigger.assert_awaited_once()


@pytest.mark.asyncio
async def test_manual_trigger_service_still_dispatches_siren(hass, coordinator):
    """Regression guard: the manual secure_me.trigger path (async_trigger())
    must keep working exactly as before, now routed through the same
    _state_changed dispatch point instead of calling modules directly.
    """
    await coordinator.async_arm_away(skip_delay=True)

    success = await coordinator.async_trigger(source="manual_test")

    assert success is True
    assert coordinator.alarm_state == STATE_ALARM_TRIGGERED
    coordinator.modules["siren"].async_trigger.assert_awaited_once()
    assert coordinator.triggered_by == "manual_test"
    assert coordinator.last_triggered is not None
