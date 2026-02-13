"""Pytest configuration for Secure Me tests."""
# VERSION = "0.3.0"

import pytest
from unittest.mock import patch, MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    yield


@pytest.fixture
def mock_config_entry():
    """Mock a config entry."""
    from homeassistant.config_entries import ConfigEntry
    from custom_components.secure_me.const import DOMAIN
    
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.title = "Test Alarm"
    entry.data = {
        "name": "Test Alarm",
        "code": "1234",
        "exit_delay": 30,
        "entry_delay": 30,
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_hass():
    """Mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.states = MagicMock()
    hass.config_entries = MagicMock()
    return hass


@pytest.fixture
def mock_coordinator():
    """Mock SecureMeCoordinator."""
    from custom_components.secure_me.coordinator import SecureMeCoordinator
    
    coordinator = MagicMock(spec=SecureMeCoordinator)
    coordinator.data = {}
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_store():
    """Mock SecureMeStore."""
    from custom_components.secure_me.store import SecureMeStore
    
    store = MagicMock(spec=SecureMeStore)
    store.data = {
        "zones": {},
        "users": {},
        "modules": {},
    }
    return store
