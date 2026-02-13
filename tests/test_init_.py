"""Tests for Secure Me integration initialization."""
# VERSION = "0.3.0"

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.setup import async_setup_component

from custom_components.secure_me.const import DOMAIN, PLATFORMS, COORDINATOR


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.domain = DOMAIN
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


@pytest.mark.asyncio
async def test_setup_entry(hass: HomeAssistant, mock_config_entry):
    """Test successful integration setup."""
    from custom_components.secure_me import async_setup_entry
    
    # Mock dependencies
    with patch("custom_components.secure_me.SecureMeStore") as mock_store_class, \
         patch("custom_components.secure_me.SecureMeCoordinator") as mock_coordinator_class, \
         patch("custom_components.secure_me.async_register_websocket_api"), \
         patch("custom_components.secure_me._async_register_panel"):
        
        # Setup mock store
        mock_store = AsyncMock()
        mock_store.async_load = AsyncMock()
        mock_store_class.return_value = mock_store
        
        # Setup mock coordinator
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        # Mock platform setup
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        
        # Run setup
        result = await async_setup_entry(hass, mock_config_entry)
        
        # Assertions
        assert result is True
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert COORDINATOR in hass.data[DOMAIN][mock_config_entry.entry_id]


@pytest.mark.asyncio
async def test_setup_entry_creates_coordinator(hass: HomeAssistant, mock_config_entry):
    """Test that setup creates a coordinator."""
    from custom_components.secure_me import async_setup_entry
    
    with patch("custom_components.secure_me.SecureMeStore") as mock_store_class, \
         patch("custom_components.secure_me.SecureMeCoordinator") as mock_coordinator_class, \
         patch("custom_components.secure_me.async_register_websocket_api"), \
         patch("custom_components.secure_me._async_register_panel"):
        
        mock_store = AsyncMock()
        mock_store.async_load = AsyncMock()
        mock_store_class.return_value = mock_store
        
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        
        await async_setup_entry(hass, mock_config_entry)
        
        # Verify coordinator was created
        mock_coordinator_class.assert_called_once_with(hass, mock_config_entry)
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_setup_entry_registers_platforms(hass: HomeAssistant, mock_config_entry):
    """Test that setup registers all platforms."""
    from custom_components.secure_me import async_setup_entry
    
    with patch("custom_components.secure_me.SecureMeStore") as mock_store_class, \
         patch("custom_components.secure_me.SecureMeCoordinator") as mock_coordinator_class, \
         patch("custom_components.secure_me.async_register_websocket_api"), \
         patch("custom_components.secure_me._async_register_panel"):
        
        mock_store = AsyncMock()
        mock_store.async_load = AsyncMock()
        mock_store_class.return_value = mock_store
        
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        
        await async_setup_entry(hass, mock_config_entry)
        
        # Verify platforms were registered
        hass.config_entries.async_forward_entry_setups.assert_called_once_with(
            mock_config_entry, PLATFORMS
        )


@pytest.mark.asyncio
async def test_unload_entry(hass: HomeAssistant, mock_config_entry):
    """Test successful integration unload."""
    from custom_components.secure_me import async_unload_entry
    
    # Setup mock data
    mock_coordinator = AsyncMock()
    mock_coordinator.async_shutdown = AsyncMock()
    mock_undo_listener = MagicMock()
    
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            COORDINATOR: mock_coordinator,
            "undo_update_listener": mock_undo_listener,
        }
    }
    
    # Mock platform unload
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    
    # Run unload
    with patch("custom_components.secure_me.async_remove_panel"):
        result = await async_unload_entry(hass, mock_config_entry)
    
    # Assertions
    assert result is True
    mock_coordinator.async_shutdown.assert_called_once()
    mock_undo_listener.assert_called_once()
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_unload_entry_removes_panel_on_last_entry(hass: HomeAssistant, mock_config_entry):
    """Test that panel is removed when last entry is unloaded."""
    from custom_components.secure_me import async_unload_entry
    
    # Setup as last entry
    mock_coordinator = AsyncMock()
    mock_coordinator.async_shutdown = AsyncMock()
    
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            COORDINATOR: mock_coordinator,
        },
        "store": MagicMock(),
        "_websocket_registered": True,
        "_panel_registered": True,
    }
    
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    
    with patch("custom_components.secure_me.async_remove_panel") as mock_remove_panel:
        await async_unload_entry(hass, mock_config_entry)
        
        # Verify panel removal was attempted
        mock_remove_panel.assert_called_once()


@pytest.mark.asyncio
async def test_reload_entry(hass: HomeAssistant, mock_config_entry):
    """Test config entry reload."""
    from custom_components.secure_me import async_reload_entry
    
    with patch("custom_components.secure_me.async_unload_entry") as mock_unload, \
         patch("custom_components.secure_me.async_setup_entry") as mock_setup:
        
        mock_unload.return_value = True
        mock_setup.return_value = True
        
        await async_reload_entry(hass, mock_config_entry)
        
        # Verify reload sequence
        mock_unload.assert_called_once_with(hass, mock_config_entry)
        mock_setup.assert_called_once_with(hass, mock_config_entry)


@pytest.mark.asyncio
async def test_setup_registers_websocket_once(hass: HomeAssistant, mock_config_entry):
    """Test that WebSocket API is only registered once."""
    from custom_components.secure_me import async_setup_entry
    
    with patch("custom_components.secure_me.SecureMeStore") as mock_store_class, \
         patch("custom_components.secure_me.SecureMeCoordinator") as mock_coordinator_class, \
         patch("custom_components.secure_me.async_register_websocket_api") as mock_register_ws, \
         patch("custom_components.secure_me._async_register_panel"):
        
        mock_store = AsyncMock()
        mock_store.async_load = AsyncMock()
        mock_store_class.return_value = mock_store
        
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        
        # First setup
        await async_setup_entry(hass, mock_config_entry)
        assert mock_register_ws.call_count == 1
        
        # Second setup (simulate multiple entries)
        mock_config_entry.entry_id = "second_entry"
        await async_setup_entry(hass, mock_config_entry)
        
        # WebSocket should still only be registered once
        assert mock_register_ws.call_count == 1


@pytest.mark.asyncio
async def test_setup_registers_panel_once(hass: HomeAssistant, mock_config_entry):
    """Test that panel is only registered once."""
    from custom_components.secure_me import async_setup_entry
    
    with patch("custom_components.secure_me.SecureMeStore") as mock_store_class, \
         patch("custom_components.secure_me.SecureMeCoordinator") as mock_coordinator_class, \
         patch("custom_components.secure_me.async_register_websocket_api"), \
         patch("custom_components.secure_me._async_register_panel") as mock_register_panel:
        
        mock_store = AsyncMock()
        mock_store.async_load = AsyncMock()
        mock_store_class.return_value = mock_store
        
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_class.return_value = mock_coordinator
        
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        
        # First setup
        await async_setup_entry(hass, mock_config_entry)
        assert mock_register_panel.call_count == 1
        
        # Second setup
        mock_config_entry.entry_id = "second_entry"
        await async_setup_entry(hass, mock_config_entry)
        
        # Panel should still only be registered once
        assert mock_register_panel.call_count == 1
