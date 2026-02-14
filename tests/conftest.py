"""Shared fixtures for Secure Me tests."""
# VERSION = "0.3.0"

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import Any


class MockState:
    """Mock HA state object."""

    def __init__(self, entity_id: str, state: str, attributes: dict | None = None):
        self.entity_id = entity_id
        self.state = state
        self.attributes = attributes or {}


class MockHass:
    """Minimal mock of HomeAssistant for unit tests."""

    def __init__(self):
        self.data: dict[str, Any] = {}
        self.bus = MagicMock()
        self.bus.async_fire = MagicMock()
        self.services = MagicMock()
        self.services.async_call = AsyncMock()
        self.config_entries = MagicMock()
        self.config_entries.async_update_entry = MagicMock()
        self.http = MagicMock()
        self.http.async_register_static_paths = AsyncMock()
        self.config = MagicMock()
        self.config.path = MagicMock(return_value="/config")
        self._states: dict[str, MockState] = {}
        self.states = MagicMock()
        self.states.get = self._states_get
        self.states.async_all = self._states_async_all

    def _states_get(self, entity_id: str) -> MockState | None:
        return self._states.get(entity_id)

    def _states_async_all(self, domain: str | None = None) -> list[MockState]:
        if domain is None:
            return list(self._states.values())
        return [s for s in self._states.values() if s.entity_id.startswith(f"{domain}.")]

    def set_state(self, entity_id: str, state: str, attributes: dict | None = None):
        """Helper to add a mock state."""
        self._states[entity_id] = MockState(entity_id, state, attributes or {})


class MockConfigEntry:
    """Mock HA config entry."""

    def __init__(self, data: dict | None = None, options: dict | None = None):
        self.entry_id = "test_entry_id_12345"
        self.title = "Secure Me"
        self.data = data or {
            "code": "1234",
            "exit_delay": 30,
            "entry_delay": 30,
        }
        self.options = options or {}
        self.source = "user"
        self.unique_id = "secure_me"
        self.add_update_listener = MagicMock(return_value=MagicMock())


class MockModule:
    """Mock alarm module for testing."""

    def __init__(self, enabled: bool = True, name: str = "Test"):
        self._enabled = enabled
        self._name = name
        self.config = {}
        self.poe_switches: list[str] = []
        self.cameras: list[str] = []
        self.recording_entities: list[str] = []
        self.locks: list[str] = []
        self.lights: list[str] = []
        self.climates: list[str] = []
        self.media_players: list[str] = []
        self.door_sensors: dict[str, str] = {}
        self.battery_sensors: dict[str, str] = {}
        self.gateway_light: str | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def module_name(self) -> str:
        return self._name

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    async def async_arm_away(self):
        pass

    async def async_arm_home(self):
        pass

    async def async_arm_night(self):
        pass

    async def async_disarm(self):
        pass

    async def async_trigger(self):
        pass

    async def async_test(self) -> dict:
        return {"success": True, "message": "Test passed"}

    async def async_cleanup(self):
        pass


@pytest.fixture
def mock_hass() -> MockHass:
    """Create a mock Home Assistant instance."""
    return MockHass()


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry()


@pytest.fixture
def mock_module() -> MockModule:
    """Create a mock module."""
    return MockModule()


@pytest.fixture
def mock_hass_with_batteries(mock_hass: MockHass) -> MockHass:
    """Create mock HA with battery sensor states."""
    mock_hass.set_state("sensor.door_lock_battery", "85", {
        "device_class": "battery",
        "friendly_name": "Door Lock Battery",
    })
    mock_hass.set_state("sensor.motion_sensor_battery", "15", {
        "device_class": "battery",
        "friendly_name": "Motion Sensor Battery",
    })
    mock_hass.set_state("sensor.window_sensor_battery", "5", {
        "device_class": "battery",
        "friendly_name": "Window Sensor Battery",
    })
    mock_hass.set_state("sensor.temp_sensor_battery", "60", {
        "device_class": "battery",
        "friendly_name": "Temp Sensor Battery",
    })
    # Non-battery sensor (should be ignored)
    mock_hass.set_state("sensor.temperature", "22.5", {
        "device_class": "temperature",
        "friendly_name": "Temperature",
    })
    return mock_hass


@pytest.fixture
def mock_hass_with_binary_sensors(mock_hass: MockHass) -> MockHass:
    """Create mock HA with binary sensor states for alarm sensors."""
    mock_hass.set_state("binary_sensor.front_door", "off", {
        "device_class": "door",
        "friendly_name": "Front Door",
    })
    mock_hass.set_state("binary_sensor.back_door", "on", {
        "device_class": "door",
        "friendly_name": "Back Door",
    })
    mock_hass.set_state("binary_sensor.living_room_motion", "off", {
        "device_class": "motion",
        "friendly_name": "Living Room Motion",
    })
    mock_hass.set_state("binary_sensor.kitchen_window", "off", {
        "device_class": "window",
        "friendly_name": "Kitchen Window",
    })
    mock_hass.set_state("binary_sensor.smoke_detector", "off", {
        "device_class": "smoke",
        "friendly_name": "Smoke Detector",
    })
    return mock_hass

@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = MagicMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.async_shutdown = MagicMock()
    return coordinator


@pytest.fixture
def mock_store():
    """Create a mock store."""
    store = MagicMock()
    store.async_load = AsyncMock()
    return store
