"""Tests for Secure Me integration initialization."""
# VERSION = "1.2.0"

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry


@pytest.mark.asyncio
async def test_setup_entry_success(hass: HomeAssistant, mock_config_entry, mock_coordinator, mock_store):
    """Test successful integration setup."""
    from custom_components.secure_me import async_setup_entry

    mock_coordinator.async_load_store_config = AsyncMock()

    with patch("custom_components.secure_me.SecureMeStore", return_value=mock_store), \
         patch("custom_components.secure_me.SecureMeCoordinator", return_value=mock_coordinator), \
         patch("custom_components.secure_me.async_register_websocket_api"), \
         patch("custom_components.secure_me.panel.async_register_panel", new_callable=AsyncMock), \
         patch("custom_components.secure_me.dr.async_get") as mock_dr:

        mock_dr.return_value = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        assert "secure_me" in hass.data


@pytest.mark.asyncio
async def test_setup_entry_creates_coordinator(hass: HomeAssistant, mock_config_entry, mock_coordinator, mock_store):
    """Test that setup creates a coordinator."""
    from custom_components.secure_me import async_setup_entry

    mock_coordinator.async_load_store_config = AsyncMock()

    with patch("custom_components.secure_me.SecureMeStore", return_value=mock_store), \
         patch("custom_components.secure_me.SecureMeCoordinator", return_value=mock_coordinator) as mock_coordinator_class, \
         patch("custom_components.secure_me.async_register_websocket_api"), \
         patch("custom_components.secure_me.panel.async_register_panel", new_callable=AsyncMock), \
         patch("custom_components.secure_me.dr.async_get") as mock_dr:

        mock_dr.return_value = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        await async_setup_entry(hass, mock_config_entry)

        mock_coordinator_class.assert_called_once()
        mock_coordinator.async_config_entry_first_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_setup_entry_registers_platforms(hass: HomeAssistant, mock_config_entry, mock_coordinator, mock_store):
    """Test that setup registers all platforms."""
    from custom_components.secure_me import async_setup_entry
    from custom_components.secure_me.const import PLATFORMS

    mock_coordinator.async_load_store_config = AsyncMock()

    with patch("custom_components.secure_me.SecureMeStore", return_value=mock_store), \
         patch("custom_components.secure_me.SecureMeCoordinator", return_value=mock_coordinator), \
         patch("custom_components.secure_me.async_register_websocket_api"), \
         patch("custom_components.secure_me.panel.async_register_panel", new_callable=AsyncMock), \
         patch("custom_components.secure_me.dr.async_get") as mock_dr:

        mock_dr.return_value = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        await async_setup_entry(hass, mock_config_entry)

        hass.config_entries.async_forward_entry_setups.assert_called_once_with(
            mock_config_entry, PLATFORMS
        )


@pytest.mark.asyncio
async def test_unload_entry_success(hass: HomeAssistant, mock_config_entry, mock_coordinator):
    """Test successful integration unload."""
    from custom_components.secure_me import async_unload_entry
    from custom_components.secure_me.const import COORDINATOR

    mock_coordinator.async_shutdown = AsyncMock()

    hass.data["secure_me"] = {
        mock_config_entry.entry_id: {
            COORDINATOR: mock_coordinator,
            "undo_update_listener": MagicMock(),
        }
    }

    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    with patch("custom_components.secure_me.panel.async_unregister_panel"):
        result = await async_unload_entry(hass, mock_config_entry)

    assert result is True
    mock_coordinator.async_shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_unload_entry_cleans_up(hass: HomeAssistant, mock_config_entry, mock_coordinator):
    """Test that unload cleans up properly."""
    from custom_components.secure_me import async_unload_entry
    from custom_components.secure_me.const import COORDINATOR

    mock_coordinator.async_shutdown = AsyncMock()
    mock_listener = MagicMock()

    hass.data["secure_me"] = {
        mock_config_entry.entry_id: {
            COORDINATOR: mock_coordinator,
            "undo_update_listener": mock_listener,
        }
    }

    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    with patch("custom_components.secure_me.panel.async_unregister_panel"):
        await async_unload_entry(hass, mock_config_entry)

    mock_listener.assert_called_once()
    assert mock_config_entry.entry_id not in hass.data["secure_me"]


@pytest.mark.asyncio
async def test_reload_entry(hass: HomeAssistant, mock_config_entry):
    """Test config entry reload via async_update_options."""
    from custom_components.secure_me import async_update_options

    with patch.object(
        hass.config_entries, "async_reload", new_callable=AsyncMock
    ) as mock_reload:
        mock_reload.return_value = True
        await async_update_options(hass, mock_config_entry)
        mock_reload.assert_called_once_with(mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_setup_registers_websocket_once(hass: HomeAssistant, mock_config_entry, mock_coordinator, mock_store):
    """Test that WebSocket API is only registered once."""
    from custom_components.secure_me import async_setup_entry

    mock_coordinator.async_load_store_config = AsyncMock()

    with patch("custom_components.secure_me.SecureMeStore", return_value=mock_store), \
         patch("custom_components.secure_me.SecureMeCoordinator", return_value=mock_coordinator), \
         patch("custom_components.secure_me.async_register_websocket_api") as mock_register_ws, \
         patch("custom_components.secure_me.panel.async_register_panel", new_callable=AsyncMock), \
         patch("custom_components.secure_me.dr.async_get") as mock_dr:

        mock_dr.return_value = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

        await async_setup_entry(hass, mock_config_entry)
        assert mock_register_ws.call_count == 1

        mock_config_entry2 = MagicMock(spec=ConfigEntry)
        mock_config_entry2.entry_id = "second_entry"
        mock_config_entry2.data = mock_config_entry.data
        mock_config_entry2.add_update_listener = MagicMock(return_value=lambda: None)

        mock_coordinator2 = MagicMock()
        mock_coordinator2.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator2.async_load_store_config = AsyncMock()

        with patch("custom_components.secure_me.SecureMeCoordinator", return_value=mock_coordinator2):
            await async_setup_entry(hass, mock_config_entry2)

        assert mock_register_ws.call_count == 1


@pytest.mark.asyncio
async def test_setup_registers_panel_once(hass: HomeAssistant, mock_config_entry, mock_coordinator, mock_store):
    """Test that panel is only registered once."""
    from custom_components.secure_me import async_setup_entry

    mock_coordinator.async_load_store_config = AsyncMock()

    with patch("custom_components.secure_me.SecureMeStore", return_value=mock_store), \
         patch("custom_components.secure_me.SecureMeCoordinator", return_value=mock_coordinator), \
         patch("custom_components.secure_me.async_register_websocket_api"), \
         patch("custom_components.secure_me.panel.async_register_panel", new_callable=AsyncMock) as mock_register_panel, \
         patch("custom_components.secure_me.dr.async_get") as mock_dr:

        mock_dr.return_value = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)

        await async_setup_entry(hass, mock_config_entry)
        assert mock_register_panel.call_count == 1

        mock_config_entry2 = MagicMock(spec=ConfigEntry)
        mock_config_entry2.entry_id = "second_entry"
        mock_config_entry2.data = mock_config_entry.data
        mock_config_entry2.add_update_listener = MagicMock(return_value=lambda: None)

        mock_coordinator2 = MagicMock()
        mock_coordinator2.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator2.async_load_store_config = AsyncMock()

        with patch("custom_components.secure_me.SecureMeCoordinator", return_value=mock_coordinator2):
            await async_setup_entry(hass, mock_config_entry2)

        assert mock_register_panel.call_count == 1
