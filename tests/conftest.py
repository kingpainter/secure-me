"""Pytest configuration for Secure Me tests."""
# VERSION = "0.3.0"

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    yield


@pytest.fixture
def mock_config_entry():
    """Mock a config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.domain = "secure_me"
    entry.title = "Test Alarm"
    entry.data = {
        "name": "Test Alarm",
        "code": "1234",
        "exit_delay": 30,
        "entry_delay": 30,
    }
    entry.options = {}
    entry.add_update_listener = MagicMock(return_value=lambda: None)
    return entry


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.states = MagicMock()
    hass.config_entries = MagicMock()
    hass.bus = MagicMock()
    return hass


@pytest.fixture
def mock_coordinator():
    """Mock SecureMeCoordinator."""
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.last_update_success = True
    coordinator.async_config_entry_first_refresh = AsyncMock()
    coordinator.async_shutdown = AsyncMock()
    return coordinator


@pytest.fixture
def mock_store():
    """Mock SecureMeStore."""
    store = MagicMock()
    store.data = {
        "zones": {},
        "users": {},
        "modules": {},
    }
    store.async_load = AsyncMock()
    store.async_save = AsyncMock()
    return store


@pytest.fixture
def mock_module():
    """Mock BaseModule."""
    module = MagicMock()
    module.enabled = True
    module.async_arm = AsyncMock()
    module.async_disarm = AsyncMock()
    module.async_triggered = AsyncMock()
    module.async_shutdown = AsyncMock()
    module.async_health_check = AsyncMock(return_value={"healthy": True})
    return module
