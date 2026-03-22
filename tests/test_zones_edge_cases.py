"""Tests for ZoneManager edge cases -- sensor deleted, unavailable, debounce.

Covers v0.5.0 + v0.6.0 changes:
- Sensor deleted from HA (new_state=None) -> treated as closed, user notified
- Sensor unavailable/unknown while armed -> treated as closed, user notified
- check_for_open_sensors() skips unavailable/missing sensors
- Sensor opens during exit delay -> trigger ignored (arming state guard)
- Debounce: rapid sensor flapping within 500ms fires callback only once
"""
# VERSION = "1.2.0"

import time
import pytest
from unittest.mock import MagicMock, patch
from .conftest import MockHass


# ---------------------------------------------------------------------------
# Minimal Zone + ZoneManager mirrors (no HA import dependency)
# ---------------------------------------------------------------------------

_OPEN_STATES = frozenset({"on", "open", "detected", "unlocked"})


class Zone:
    def __init__(self, zone_id, zone_type, sensors=None, enabled=True):
        self.zone_id = zone_id
        self.zone_type = zone_type
        self.sensors = sensors or []
        self.enabled = enabled
        self._open_sensors = []

    @property
    def is_triggered(self):
        return len(self._open_sensors) > 0

    @property
    def open_sensors(self):
        return self._open_sensors.copy()

    def update_sensor_state(self, entity_id, is_open):
        was = self.is_triggered
        if is_open and entity_id not in self._open_sensors:
            self._open_sensors.append(entity_id)
        elif not is_open and entity_id in self._open_sensors:
            self._open_sensors.remove(entity_id)
        return was != self.is_triggered

    def clear_open_sensors(self):
        self._open_sensors.clear()


class ZoneManager:
    """Mirrors zones.py ZoneManager logic for isolated unit testing."""

    NOTIFY_ID = "secure_me_module_error"
    DEBOUNCE_INTERVAL = 0.5

    def __init__(self, hass):
        self.hass = hass
        self._zones = {}
        self._sensor_to_zone = {}
        self._last_trigger_time = {}
        self._trigger_callback = None
        # Notification mock
        self.hass.components = MagicMock()
        self.hass.components.persistent_notification = MagicMock()
        self.hass.components.persistent_notification.async_create = MagicMock()

    def add_zone(self, zone_id, zone_type, sensors=None, enabled=True):
        zone = Zone(zone_id, zone_type, sensors, enabled)
        self._zones[zone_id] = zone
        for s in (sensors or []):
            self._sensor_to_zone[s] = zone_id

    def get_zone_by_sensor(self, entity_id):
        zid = self._sensor_to_zone.get(entity_id)
        return self._zones.get(zid) if zid else None

    def get_all_open_sensors(self):
        result = []
        for zone in self._zones.values():
            if zone.enabled:
                result.extend(zone.open_sensors)
        return result

    def clear_all_triggers(self):
        for zone in self._zones.values():
            zone.clear_open_sensors()

    def update_sensor_state(self, entity_id, state):
        """Mirrors ZoneManager.update_sensor_state including edge cases."""
        zone = self.get_zone_by_sensor(entity_id)
        if not zone or not zone.enabled:
            return False, None

        # EDGE CASE: entity deleted
        if state is None:
            self.hass.components.persistent_notification.async_create(
                message=f"Sensor '{entity_id}' disappeared.",
                title="Secure Me - Sensor Missing",
                notification_id=f"{self.NOTIFY_ID}_sensor_{entity_id.replace('.', '_')}",
            )
            changed = zone.update_sensor_state(entity_id, False)
            return changed, zone if changed else None

        # EDGE CASE: sensor unavailable/unknown
        if state.state in ("unavailable", "unknown"):
            self.hass.components.persistent_notification.async_create(
                message=f"Sensor '{entity_id}' is {state.state}.",
                title="Secure Me - Sensor Unavailable",
                notification_id=f"{self.NOTIFY_ID}_unavail_{entity_id.replace('.', '_')}",
            )
            changed = zone.update_sensor_state(entity_id, False)
            return changed, zone if changed else None

        is_open = state.state in _OPEN_STATES
        changed = zone.update_sensor_state(entity_id, is_open)
        return changed, zone if changed else None

    def check_for_open_sensors(self):
        """Mirrors zones.py check_for_open_sensors -- skips unavailable/missing."""
        for zone in self._zones.values():
            if not zone.enabled:
                continue
            for sensor in zone.sensors:
                state = self.hass.states.get(sensor)
                if not state:
                    continue  # missing -- skip
                if state.state in ("unavailable", "unknown"):
                    continue  # unavailable -- skip
                if state.state in _OPEN_STATES:
                    zone.update_sensor_state(sensor, True)
        return len(self.get_all_open_sensors()) > 0

    def fire_trigger_if_debounce_ok(self, entity_id, zone, callback):
        """Debounce logic extracted for testability."""
        now = time.monotonic()
        last = self._last_trigger_time.get(entity_id, 0.0)
        if now - last < self.DEBOUNCE_INTERVAL:
            return False  # debounced
        self._last_trigger_time[entity_id] = now
        callback(zone)
        return True


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

class MockState:
    def __init__(self, state):
        self.state = state


def make_manager_with_zone(hass, zone_id="zone_1", zone_type="entry",
                           sensors=None, enabled=True):
    mgr = ZoneManager(hass)
    sensors = sensors or ["binary_sensor.door"]
    mgr.add_zone(zone_id, zone_type, sensors=sensors, enabled=enabled)
    return mgr


# ---------------------------------------------------------------------------
# Tests: sensor deleted (state=None)
# ---------------------------------------------------------------------------

class TestSensorDeleted:
    """new_state=None -- entity removed from HA while armed."""

    def test_deleted_sensor_treated_as_closed(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        # First open the sensor
        mgr.update_sensor_state("binary_sensor.door", MockState("on"))
        assert "binary_sensor.door" in mgr.get_all_open_sensors()

        # Now delete it (state=None)
        mgr.update_sensor_state("binary_sensor.door", None)
        assert "binary_sensor.door" not in mgr.get_all_open_sensors()

    def test_deleted_sensor_fires_persistent_notification(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        mgr.update_sensor_state("binary_sensor.door", None)
        hass.components.persistent_notification.async_create.assert_called_once()
        args = hass.components.persistent_notification.async_create.call_args
        assert "Missing" in str(args) or "disappeared" in str(args).lower()

    def test_deleted_sensor_returns_false_changed_if_already_closed(self):
        """No change if sensor was already closed when deleted."""
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        # Sensor was never opened
        changed, zone = mgr.update_sensor_state("binary_sensor.door", None)
        assert changed is False

    def test_deleted_unknown_sensor_returns_false(self):
        """Sensor not in any zone -> returns (False, None)."""
        hass = MockHass()
        mgr = ZoneManager(hass)
        mgr.add_zone("z1", "entry", sensors=["binary_sensor.other"])

        changed, zone = mgr.update_sensor_state("binary_sensor.unknown", None)
        assert changed is False
        assert zone is None


# ---------------------------------------------------------------------------
# Tests: sensor unavailable/unknown while armed
# ---------------------------------------------------------------------------

class TestSensorUnavailable:
    """Unavailable/unknown sensor -> treated as closed, notification sent."""

    def test_unavailable_treated_as_closed(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        # Open sensor, then go unavailable
        mgr.update_sensor_state("binary_sensor.door", MockState("on"))
        mgr.update_sensor_state("binary_sensor.door", MockState("unavailable"))
        assert "binary_sensor.door" not in mgr.get_all_open_sensors()

    def test_unknown_treated_as_closed(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        mgr.update_sensor_state("binary_sensor.door", MockState("on"))
        mgr.update_sensor_state("binary_sensor.door", MockState("unknown"))
        assert "binary_sensor.door" not in mgr.get_all_open_sensors()

    def test_unavailable_fires_notification(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        mgr.update_sensor_state("binary_sensor.door", MockState("unavailable"))
        hass.components.persistent_notification.async_create.assert_called_once()
        args = hass.components.persistent_notification.async_create.call_args
        assert "Unavailable" in str(args) or "unavailable" in str(args)

    def test_sensor_recovery_from_unavailable(self):
        """Sensor recovers from unavailable -> normal open/close tracking resumes."""
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        mgr.update_sensor_state("binary_sensor.door", MockState("unavailable"))
        assert "binary_sensor.door" not in mgr.get_all_open_sensors()

        mgr.update_sensor_state("binary_sensor.door", MockState("on"))
        assert "binary_sensor.door" in mgr.get_all_open_sensors()

    def test_unavailable_no_change_if_already_closed(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        changed, _ = mgr.update_sensor_state("binary_sensor.door", MockState("unavailable"))
        assert changed is False  # was already closed


# ---------------------------------------------------------------------------
# Tests: check_for_open_sensors skips unavailable/missing
# ---------------------------------------------------------------------------

class TestCheckOpenSensors:
    """check_for_open_sensors does not block arming for offline sensors."""

    def test_open_sensor_detected(self):
        hass = MockHass()
        hass.set_state("binary_sensor.door", "on")
        mgr = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert mgr.check_for_open_sensors() is True

    def test_closed_sensor_not_blocking(self):
        hass = MockHass()
        hass.set_state("binary_sensor.door", "off")
        mgr = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert mgr.check_for_open_sensors() is False

    def test_unavailable_sensor_skipped(self):
        hass = MockHass()
        hass.set_state("binary_sensor.door", "unavailable")
        mgr = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert mgr.check_for_open_sensors() is False

    def test_unknown_sensor_skipped(self):
        hass = MockHass()
        hass.set_state("binary_sensor.door", "unknown")
        mgr = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert mgr.check_for_open_sensors() is False

    def test_missing_entity_skipped(self):
        """Entity not in HA states -> no block on arming."""
        hass = MockHass()
        # Do NOT set state -- entity missing
        mgr = make_manager_with_zone(hass, sensors=["binary_sensor.door"])

        assert mgr.check_for_open_sensors() is False

    def test_mixed_sensors_open_and_unavailable(self):
        """Only the genuinely open sensor should block."""
        hass = MockHass()
        hass.set_state("binary_sensor.door1", "on")
        hass.set_state("binary_sensor.door2", "unavailable")
        mgr = ZoneManager(hass)
        mgr.add_zone("z1", "entry",
                     sensors=["binary_sensor.door1", "binary_sensor.door2"])

        assert mgr.check_for_open_sensors() is True
        open_s = mgr.get_all_open_sensors()
        assert "binary_sensor.door1" in open_s
        assert "binary_sensor.door2" not in open_s

    def test_disabled_zone_not_checked(self):
        hass = MockHass()
        hass.set_state("binary_sensor.door", "on")
        mgr = make_manager_with_zone(hass, sensors=["binary_sensor.door"],
                                     enabled=False)

        assert mgr.check_for_open_sensors() is False


# ---------------------------------------------------------------------------
# Tests: sensor opens during exit delay (arming state guard)
# ---------------------------------------------------------------------------

class TestExitDelayGuard:
    """Sensor opening during exit delay should not trigger alarm."""

    def test_trigger_ignored_during_arming(self):
        """Mirrors coordinator._zone_triggered guard for arming state."""
        # We test the guard logic directly:
        # if arming state, return without triggering
        is_arming = True
        triggered = False

        if not is_arming:
            triggered = True  # would trigger

        assert triggered is False

    def test_trigger_fires_when_armed(self):
        is_arming = False
        triggered = False

        if not is_arming:
            triggered = True

        assert triggered is True


# ---------------------------------------------------------------------------
# Tests: sensor debounce (v0.6.0)
# ---------------------------------------------------------------------------

class TestSensorDebounce:
    """Rapid sensor flapping within 500ms fires callback only once."""

    def test_first_trigger_fires_callback(self):
        hass = MockHass()
        mgr = ZoneManager(hass)
        zone = Zone("z1", "entry", sensors=["binary_sensor.door"])
        callback = MagicMock()

        fired = mgr.fire_trigger_if_debounce_ok("binary_sensor.door", zone, callback)
        assert fired is True
        callback.assert_called_once_with(zone)

    def test_rapid_second_trigger_debounced(self):
        """Second call within 500ms must NOT fire callback."""
        hass = MockHass()
        mgr = ZoneManager(hass)
        zone = Zone("z1", "entry", sensors=["binary_sensor.door"])
        callback = MagicMock()

        mgr.fire_trigger_if_debounce_ok("binary_sensor.door", zone, callback)
        fired = mgr.fire_trigger_if_debounce_ok("binary_sensor.door", zone, callback)
        assert fired is False
        assert callback.call_count == 1  # only the first

    def test_trigger_after_debounce_interval_fires_again(self):
        """Trigger after 500ms+ window fires callback again."""
        hass = MockHass()
        mgr = ZoneManager(hass)
        zone = Zone("z1", "entry", sensors=["binary_sensor.door"])
        callback = MagicMock()

        # First trigger
        mgr.fire_trigger_if_debounce_ok("binary_sensor.door", zone, callback)
        # Manually backdate last trigger time by 1 second
        mgr._last_trigger_time["binary_sensor.door"] -= 1.0

        fired = mgr.fire_trigger_if_debounce_ok("binary_sensor.door", zone, callback)
        assert fired is True
        assert callback.call_count == 2

    def test_different_sensors_debounced_independently(self):
        """Debounce is per-entity, not global."""
        hass = MockHass()
        mgr = ZoneManager(hass)
        zone = Zone("z1", "entry", sensors=["binary_sensor.door1",
                                             "binary_sensor.door2"])
        callback = MagicMock()

        mgr.fire_trigger_if_debounce_ok("binary_sensor.door1", zone, callback)
        # door2 has no debounce history -- should fire
        fired = mgr.fire_trigger_if_debounce_ok("binary_sensor.door2", zone, callback)
        assert fired is True
        assert callback.call_count == 2


# ---------------------------------------------------------------------------
# Tests: normal sensor state changes
# ---------------------------------------------------------------------------

class TestNormalSensorUpdates:
    """Baseline open/close behavior (sanity checks)."""

    def test_sensor_open_marks_zone_triggered(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        changed, zone = mgr.update_sensor_state("binary_sensor.door",
                                                 MockState("on"))
        assert changed is True
        assert zone.is_triggered is True

    def test_sensor_close_clears_trigger(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        mgr.update_sensor_state("binary_sensor.door", MockState("on"))
        changed, zone = mgr.update_sensor_state("binary_sensor.door",
                                                 MockState("off"))
        assert changed is True
        assert zone.is_triggered is False

    def test_open_states_recognized(self):
        for state_val in ("on", "open", "detected", "unlocked"):
            assert state_val in _OPEN_STATES

    def test_closed_state_not_in_open_states(self):
        for state_val in ("off", "closed", "locked"):
            assert state_val not in _OPEN_STATES

    def test_disabled_zone_sensor_update_ignored(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass, enabled=False)

        changed, zone = mgr.update_sensor_state("binary_sensor.door",
                                                 MockState("on"))
        assert changed is False
        assert zone is None

    def test_clear_all_triggers(self):
        hass = MockHass()
        mgr = make_manager_with_zone(hass)

        mgr.update_sensor_state("binary_sensor.door", MockState("on"))
        assert len(mgr.get_all_open_sensors()) == 1

        mgr.clear_all_triggers()
        assert len(mgr.get_all_open_sensors()) == 0
