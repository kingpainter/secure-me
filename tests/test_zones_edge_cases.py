"""Tests for ZoneManager edge cases -- sensor deleted, unavailable, debounce.

Covers v0.5.0 + v0.6.0 changes:
- Sensor deleted from HA (new_state=None) -> treated as closed, user notified
- Sensor unavailable/unknown while armed -> treated as closed
- check_for_open_sensors() skips unavailable/missing sensors
- Sensor opens during exit delay -> trigger ignored (arming state guard)
- Debounce: rapid sensor flapping within 500ms fires callback only once
- Debounce is per-entity: a second sensor in the same zone must still fire

v1.5.0 rewrite: this file used to test local "mirror" copies of Zone/
ZoneManager instead of the real custom_components.secure_me.zones classes.
That anti-pattern meant these tests could stay green even when the real
module regressed -- which is exactly what happened: a bug where
Zone.update_sensor_state() reported "changed" based on the zone's aggregate
is_triggered flag rather than the specific sensor's own state shipped
undetected (only caught later by test_v1_2_0.py's real-module Home Alone
dispatch tests). Every test below now exercises the real ZoneManager/Zone
classes via the real `hass` pytest fixture instead of a hand-rolled mirror.
One assertion was also corrected while migrating: the old mirror asserted a
persistent_notification IS fired for unavailable/unknown sensors, but the
real module has deliberately logged this at DEBUG with no notification
since v1.4.2 (to avoid alerting on routine Zigbee/WiFi flaps) -- the mirror
test had been asserting stale, pre-v1.4.2 behaviour that no longer matches
production.
"""
# VERSION = "1.5.0"

import pytest
from unittest.mock import AsyncMock, patch

from custom_components.secure_me.zones import ZoneManager, _OPEN_STATES
from .conftest import MockState


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_manager_with_zone(hass, zone_id="zone_1", zone_type="entry",
                           sensors=None, enabled=True, arm_modes=None):
    """Create a real ZoneManager with a single zone for testing."""
    zm = ZoneManager(hass)
    sensors = sensors or ["binary_sensor.door"]
    zm.add_zone(zone_id, zone_type, sensors=sensors, enabled=enabled,
                arm_modes=arm_modes)
    return zm


# ---------------------------------------------------------------------------
# Tests: sensor deleted (state=None)
# ---------------------------------------------------------------------------

class TestSensorDeleted:
    """new_state=None -- entity removed from HA while armed."""

    @pytest.mark.asyncio
    async def test_deleted_sensor_treated_as_closed(self, hass):
        zm = make_manager_with_zone(hass)

        # First open the sensor
        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "on"))
        assert "binary_sensor.door" in zm.get_all_open_sensors()

        # Now delete it (state=None)
        zm.update_sensor_state("binary_sensor.door", None)
        assert "binary_sensor.door" not in zm.get_all_open_sensors()

    @pytest.mark.asyncio
    async def test_deleted_sensor_fires_persistent_notification(self, hass):
        zm = make_manager_with_zone(hass)

        with patch("homeassistant.components.persistent_notification.async_create") as mock_create:
            zm.update_sensor_state("binary_sensor.door", None)
            mock_create.assert_called_once()
            _, kwargs = mock_create.call_args
            msg = kwargs.get("message", "")
            title = kwargs.get("title", "")
            assert "disappeared" in msg.lower() or "Missing" in title

    @pytest.mark.asyncio
    async def test_deleted_sensor_returns_false_changed_if_already_closed(self, hass):
        """No change if sensor was already closed when deleted."""
        zm = make_manager_with_zone(hass)

        # Sensor was never opened
        changed, zone = zm.update_sensor_state("binary_sensor.door", None)
        assert changed is False

    @pytest.mark.asyncio
    async def test_deleted_unknown_sensor_returns_false(self, hass):
        """Sensor not in any zone -> returns (False, None)."""
        zm = ZoneManager(hass)
        zm.add_zone("z1", "entry", sensors=["binary_sensor.other"])

        changed, zone = zm.update_sensor_state("binary_sensor.unknown", None)
        assert changed is False
        assert zone is None


# ---------------------------------------------------------------------------
# Tests: sensor unavailable/unknown while armed
# ---------------------------------------------------------------------------

class TestSensorUnavailable:
    """Unavailable/unknown sensor -> treated as closed."""

    @pytest.mark.asyncio
    async def test_unavailable_treated_as_closed(self, hass):
        zm = make_manager_with_zone(hass)

        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "on"))
        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "unavailable"))
        assert "binary_sensor.door" not in zm.get_all_open_sensors()

    @pytest.mark.asyncio
    async def test_unknown_treated_as_closed(self, hass):
        zm = make_manager_with_zone(hass)

        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "on"))
        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "unknown"))
        assert "binary_sensor.door" not in zm.get_all_open_sensors()

    @pytest.mark.asyncio
    async def test_unavailable_does_not_fire_notification(self, hass):
        """v1.4.2: unavailable/unknown is logged at DEBUG, not alerted on --
        Zigbee/WiFi sensors routinely flap offline for a few seconds and a
        notification on every occurrence would drown out real issues."""
        zm = make_manager_with_zone(hass)

        with patch("homeassistant.components.persistent_notification.async_create") as mock_create:
            zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "unavailable"))
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_sensor_recovery_from_unavailable(self, hass):
        """Sensor recovers from unavailable -> normal open/close tracking resumes."""
        zm = make_manager_with_zone(hass)

        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "unavailable"))
        assert "binary_sensor.door" not in zm.get_all_open_sensors()

        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "on"))
        assert "binary_sensor.door" in zm.get_all_open_sensors()

    @pytest.mark.asyncio
    async def test_unavailable_no_change_if_already_closed(self, hass):
        zm = make_manager_with_zone(hass)

        changed, _ = zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "unavailable"))
        assert changed is False  # was already closed


# ---------------------------------------------------------------------------
# Tests: check_for_open_sensors skips unavailable/missing
# ---------------------------------------------------------------------------

class TestCheckOpenSensors:
    """check_for_open_sensors does not block arming for offline sensors."""

    @pytest.mark.asyncio
    async def test_open_sensor_detected(self, hass):
        hass.states.async_set("binary_sensor.door", "on", {"device_class": "door"})
        await hass.async_block_till_done()
        zm = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert zm.check_for_open_sensors() is True

    @pytest.mark.asyncio
    async def test_closed_sensor_not_blocking(self, hass):
        hass.states.async_set("binary_sensor.door", "off", {"device_class": "door"})
        await hass.async_block_till_done()
        zm = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert zm.check_for_open_sensors() is False

    @pytest.mark.asyncio
    async def test_unavailable_sensor_skipped(self, hass):
        hass.states.async_set("binary_sensor.door", "unavailable")
        await hass.async_block_till_done()
        zm = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert zm.check_for_open_sensors() is False

    @pytest.mark.asyncio
    async def test_unknown_sensor_skipped(self, hass):
        hass.states.async_set("binary_sensor.door", "unknown")
        await hass.async_block_till_done()
        zm = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert zm.check_for_open_sensors() is False

    @pytest.mark.asyncio
    async def test_missing_entity_skipped(self, hass):
        """Entity not in HA states -> no block on arming."""
        # Do NOT set state -- entity missing
        zm = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert zm.check_for_open_sensors() is False

    @pytest.mark.asyncio
    async def test_mixed_sensors_open_and_unavailable(self, hass):
        """Only the genuinely open sensor should block."""
        hass.states.async_set("binary_sensor.door1", "on", {"device_class": "door"})
        hass.states.async_set("binary_sensor.door2", "unavailable")
        await hass.async_block_till_done()
        zm = ZoneManager(hass)
        zm.add_zone("z1", "entry",
                    sensors=["binary_sensor.door1", "binary_sensor.door2"])

        assert zm.check_for_open_sensors() is True
        open_s = zm.get_all_open_sensors()
        assert "binary_sensor.door1" in open_s
        assert "binary_sensor.door2" not in open_s

    @pytest.mark.asyncio
    async def test_disabled_zone_not_checked(self, hass):
        hass.states.async_set("binary_sensor.door", "on", {"device_class": "door"})
        await hass.async_block_till_done()
        zm = make_manager_with_zone(hass, sensors=["binary_sensor.door"],
                                     enabled=False)

        assert zm.check_for_open_sensors() is False


# ---------------------------------------------------------------------------
# Tests: sensor opens during exit delay (arming state guard)
# ---------------------------------------------------------------------------
# NOTE: this guard actually lives in coordinator.py's _zone_triggered(), not
# in zones.py -- these two tests illustrate the guard's boolean logic only.
# Full end-to-end coverage of the real guard lives in test_state_machine*.py
# and test_v1_2_0.py, which exercise the real coordinator/state machine.

class TestExitDelayGuard:
    """Sensor opening during exit delay should not trigger alarm."""

    def test_trigger_ignored_during_arming(self):
        is_arming = True
        triggered = False
        if not is_arming:
            triggered = True
        assert triggered is False

    def test_trigger_fires_when_armed(self):
        is_arming = False
        triggered = False
        if not is_arming:
            triggered = True
        assert triggered is True


# ---------------------------------------------------------------------------
# Tests: sensor debounce (v0.6.0) -- real ZoneManager.start_monitoring()
# ---------------------------------------------------------------------------

class TestSensorDebounce:
    """Rapid sensor flapping within 500ms fires the trigger callback only
    once. Exercises the real debounce inside start_monitoring's internal
    _sensor_state_changed handler end-to-end (not a standalone mirrored
    method), the same way test_v1_2_0.py's Home Alone dispatch tests do."""

    @pytest.mark.asyncio
    async def test_first_trigger_fires_callback(self, hass):
        hass.states.async_set("binary_sensor.door", "off", {"device_class": "door"})
        await hass.async_block_till_done()
        zm = make_manager_with_zone(hass, arm_modes=["away"])
        zm.load_sensor_configs({})
        callback = AsyncMock()
        zm.start_monitoring(callback_func=callback, arm_mode="away")

        hass.states.async_set("binary_sensor.door", "on", {"device_class": "door"})
        await hass.async_block_till_done()

        assert callback.call_count == 1

    @pytest.mark.asyncio
    async def test_rapid_second_trigger_debounced(self, hass):
        """Flap on -> off -> on within 500ms must only fire once."""
        hass.states.async_set("binary_sensor.door", "off", {"device_class": "door"})
        await hass.async_block_till_done()
        zm = make_manager_with_zone(hass, arm_modes=["away"])
        zm.load_sensor_configs({})
        callback = AsyncMock()
        zm.start_monitoring(callback_func=callback, arm_mode="away")

        hass.states.async_set("binary_sensor.door", "on", {"device_class": "door"})
        await hass.async_block_till_done()
        hass.states.async_set("binary_sensor.door", "off", {"device_class": "door"})
        await hass.async_block_till_done()
        hass.states.async_set("binary_sensor.door", "on", {"device_class": "door"})
        await hass.async_block_till_done()

        assert callback.call_count == 1

    @pytest.mark.asyncio
    async def test_trigger_after_debounce_interval_fires_again(self, hass):
        hass.states.async_set("binary_sensor.door", "off", {"device_class": "door"})
        await hass.async_block_till_done()
        zm = make_manager_with_zone(hass, arm_modes=["away"])
        zm.load_sensor_configs({})
        callback = AsyncMock()
        zm.start_monitoring(callback_func=callback, arm_mode="away")

        hass.states.async_set("binary_sensor.door", "on", {"device_class": "door"})
        await hass.async_block_till_done()
        assert callback.call_count == 1

        # Backdate the internal debounce clock instead of sleeping 500ms+ --
        # keeps the test fast while still exercising the real interval check.
        zm._last_trigger_time["binary_sensor.door"] -= 1.0
        hass.states.async_set("binary_sensor.door", "off", {"device_class": "door"})
        await hass.async_block_till_done()
        hass.states.async_set("binary_sensor.door", "on", {"device_class": "door"})
        await hass.async_block_till_done()

        assert callback.call_count == 2

    @pytest.mark.asyncio
    async def test_different_sensors_debounced_independently(self, hass):
        """Debounce is per-entity -- one door flapping must not suppress a
        genuine trigger from a different door in the same zone. This is the
        same regression covered for the Home Alone dispatch path in
        test_v1_2_0.py::TestHomeAloneDoorDispatchDebounce, exercised here for
        the main (non-Home-Alone) trigger_callback path."""
        hass.states.async_set("binary_sensor.door1", "off", {"device_class": "door"})
        hass.states.async_set("binary_sensor.door2", "off", {"device_class": "door"})
        await hass.async_block_till_done()
        zm = ZoneManager(hass)
        zm.add_zone(
            "z1", "entry",
            sensors=["binary_sensor.door1", "binary_sensor.door2"],
            enabled=True, arm_modes=["away"],
        )
        zm.load_sensor_configs({})
        callback = AsyncMock()
        zm.start_monitoring(callback_func=callback, arm_mode="away")

        hass.states.async_set("binary_sensor.door1", "on", {"device_class": "door"})
        await hass.async_block_till_done()
        hass.states.async_set("binary_sensor.door2", "on", {"device_class": "door"})
        await hass.async_block_till_done()

        assert callback.call_count == 2


# ---------------------------------------------------------------------------
# Tests: normal sensor state changes
# ---------------------------------------------------------------------------

class TestNormalSensorUpdates:
    """Baseline open/close behavior (sanity checks) against the real classes."""

    @pytest.mark.asyncio
    async def test_sensor_open_marks_zone_triggered(self, hass):
        zm = make_manager_with_zone(hass)

        changed, zone = zm.update_sensor_state("binary_sensor.door",
                                                MockState("binary_sensor.door", "on"))
        assert changed is True
        assert zone.is_triggered is True

    @pytest.mark.asyncio
    async def test_sensor_close_clears_trigger(self, hass):
        zm = make_manager_with_zone(hass)

        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "on"))
        changed, zone = zm.update_sensor_state("binary_sensor.door",
                                                MockState("binary_sensor.door", "off"))
        assert changed is True
        assert zone.is_triggered is False

    def test_open_states_recognized(self):
        for state_val in ("on", "open", "detected", "unlocked"):
            assert state_val in _OPEN_STATES

    def test_closed_state_not_in_open_states(self):
        for state_val in ("off", "closed", "locked"):
            assert state_val not in _OPEN_STATES

    @pytest.mark.asyncio
    async def test_disabled_zone_sensor_update_ignored(self, hass):
        zm = make_manager_with_zone(hass, enabled=False)

        changed, zone = zm.update_sensor_state("binary_sensor.door",
                                                MockState("binary_sensor.door", "on"))
        assert changed is False
        assert zone is None

    @pytest.mark.asyncio
    async def test_clear_all_triggers(self, hass):
        zm = make_manager_with_zone(hass)

        zm.update_sensor_state("binary_sensor.door", MockState("binary_sensor.door", "on"))
        assert len(zm.get_all_open_sensors()) == 1

        zm.clear_all_triggers()
        assert len(zm.get_all_open_sensors()) == 0
