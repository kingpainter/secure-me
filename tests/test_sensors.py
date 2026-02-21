"""Tests for Secure Me sensor platform — battery discovery and health metrics."""
# VERSION = "0.9.0"

import pytest
from .conftest import MockHass, MockState


def _discover_battery_sensors(hass) -> list[dict]:
    """Replicate the discovery logic from sensor.py for testing."""
    batteries = []
    for state in hass.states.async_all("sensor"):
        device_class = state.attributes.get("device_class", "")
        if device_class != "battery":
            continue
        level = None
        try:
            level = int(float(state.state))
        except (ValueError, TypeError):
            pass
        batteries.append({
            "entity_id": state.entity_id,
            "name": state.attributes.get("friendly_name", state.entity_id),
            "level": level,
            "available": state.state not in ("unavailable", "unknown", None),
        })
    return batteries


def _get_battery_summary(hass) -> dict:
    """Replicate summary logic from sensor.py for testing."""
    batteries = _discover_battery_sensors(hass)
    lowest_level = None
    lowest_name = "none"
    lowest_entity = "none"
    low_count = 0
    critical_count = 0
    unavailable_count = 0

    for bat in batteries:
        level = bat["level"]
        if not bat["available"] or level is None:
            unavailable_count += 1
            continue
        if lowest_level is None or level < lowest_level:
            lowest_level = level
            lowest_name = bat["name"]
            lowest_entity = bat["entity_id"]
        if level < 20:
            low_count += 1
        if level < 10:
            critical_count += 1

    return {
        "batteries": batteries,
        "lowest_level": lowest_level,
        "lowest_name": lowest_name,
        "lowest_entity": lowest_entity,
        "low_count": low_count,
        "critical_count": critical_count,
        "total": len(batteries),
        "unavailable_count": unavailable_count,
    }


class TestBatteryDiscovery:
    """Test battery sensor auto-discovery."""

    def test_discovers_battery_sensors(self, mock_hass_with_batteries):
        batteries = _discover_battery_sensors(mock_hass_with_batteries)
        assert len(batteries) == 4  # Should not include temperature sensor

    def test_ignores_non_battery(self, mock_hass_with_batteries):
        batteries = _discover_battery_sensors(mock_hass_with_batteries)
        entity_ids = [b["entity_id"] for b in batteries]
        assert "sensor.temperature" not in entity_ids

    def test_parses_battery_levels(self, mock_hass_with_batteries):
        batteries = _discover_battery_sensors(mock_hass_with_batteries)
        levels = {b["entity_id"]: b["level"] for b in batteries}
        assert levels["sensor.door_lock_battery"] == 85
        assert levels["sensor.motion_sensor_battery"] == 15
        assert levels["sensor.window_sensor_battery"] == 5

    def test_handles_unavailable_battery(self, mock_hass):
        mock_hass.set_state("sensor.dead_battery", "unavailable", {
            "device_class": "battery",
            "friendly_name": "Dead Battery",
        })
        batteries = _discover_battery_sensors(mock_hass)
        assert len(batteries) == 1
        assert batteries[0]["available"] is False
        assert batteries[0]["level"] is None

    def test_handles_unknown_battery(self, mock_hass):
        mock_hass.set_state("sensor.unknown_battery", "unknown", {
            "device_class": "battery",
            "friendly_name": "Unknown Battery",
        })
        batteries = _discover_battery_sensors(mock_hass)
        assert batteries[0]["available"] is False

    def test_empty_hass_returns_empty(self, mock_hass):
        batteries = _discover_battery_sensors(mock_hass)
        assert batteries == []


class TestBatterySummary:
    """Test battery summary calculations."""

    def test_finds_lowest_battery(self, mock_hass_with_batteries):
        summary = _get_battery_summary(mock_hass_with_batteries)
        assert summary["lowest_level"] == 5
        assert summary["lowest_entity"] == "sensor.window_sensor_battery"

    def test_counts_low_batteries(self, mock_hass_with_batteries):
        # 15% and 5% are below 20%
        summary = _get_battery_summary(mock_hass_with_batteries)
        assert summary["low_count"] == 2

    def test_counts_critical_batteries(self, mock_hass_with_batteries):
        # Only 5% is below 10%
        summary = _get_battery_summary(mock_hass_with_batteries)
        assert summary["critical_count"] == 1

    def test_total_count(self, mock_hass_with_batteries):
        summary = _get_battery_summary(mock_hass_with_batteries)
        assert summary["total"] == 4

    def test_empty_returns_none_lowest(self, mock_hass):
        summary = _get_battery_summary(mock_hass)
        assert summary["lowest_level"] is None
        assert summary["total"] == 0

    def test_all_healthy(self, mock_hass):
        mock_hass.set_state("sensor.bat1", "90", {
            "device_class": "battery", "friendly_name": "Bat1"
        })
        mock_hass.set_state("sensor.bat2", "80", {
            "device_class": "battery", "friendly_name": "Bat2"
        })
        summary = _get_battery_summary(mock_hass)
        assert summary["low_count"] == 0
        assert summary["critical_count"] == 0
        assert summary["lowest_level"] == 80


class TestHealthLogic:
    """Test entity availability checking logic."""

    def test_available_entity(self, mock_hass):
        mock_hass.set_state("switch.test", "on")
        state = mock_hass.states.get("switch.test")
        assert state is not None
        assert state.state not in ("unavailable", "unknown")

    def test_unavailable_entity(self, mock_hass):
        mock_hass.set_state("switch.test", "unavailable")
        state = mock_hass.states.get("switch.test")
        assert state.state == "unavailable"

    def test_nonexistent_entity(self, mock_hass):
        state = mock_hass.states.get("switch.does_not_exist")
        assert state is None

    def test_unknown_entity(self, mock_hass):
        mock_hass.set_state("switch.test", "unknown")
        state = mock_hass.states.get("switch.test")
        assert state.state == "unknown"
