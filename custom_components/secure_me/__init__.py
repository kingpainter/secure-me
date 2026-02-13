"""The Secure Me integration."""
# VERSION = "0.3.0"

import logging
import os
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig

from .const import (
    DOMAIN,
    PLATFORMS,
    VERSION,
    COORDINATOR,
    UNDO_UPDATE_LISTENER,
    CONF_CODE,
    CONF_EXIT_DELAY,
    CONF_ENTRY_DELAY,
)
from .coordinator import SecureMeCoordinator
from .store import SecureMeStore
from .websocket_api import async_register_websocket_api

_LOGGER = logging.getLogger(__name__)

# Path to frontend files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
PANEL_URL = "/secure-me-panel"
PANEL_TITLE = "Secure Me"
PANEL_ICON = "mdi:shield-home"
PANEL_FRONTEND_URL_PATH = "secureme"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Secure Me from a config entry."""
    _LOGGER.info("Setting up Secure Me integration version %s", VERSION)

    hass.data.setdefault(DOMAIN, {})

    # ─── Initialize store ───
    store = SecureMeStore(hass)
    await store.async_load()
    
    # Store globally (shared across all entries if needed)
    if "store" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["store"] = store

    # ─── Initialize coordinator (PER ENTRY) ───
    coordinator = SecureMeCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    # Create entry-specific data structure
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    # ─── Register WebSocket API (once) ───
    if not hasattr(hass.data[DOMAIN], "_websocket_registered"):
        async_register_websocket_api(hass)
        hass.data[DOMAIN]["_websocket_registered"] = True

    # ─── Register frontend panel (once) ───
    if not hasattr(hass.data[DOMAIN], "_panel_registered"):
        await _async_register_panel(hass)
        hass.data[DOMAIN]["_panel_registered"] = True

    # ─── Set up platforms ───
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ─── Listen for option updates ───
    undo_listener = entry.add_update_listener(_async_update_options)
    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER] = undo_listener

    _LOGGER.info("Secure Me integration setup completed (v%s)", VERSION)
    return True


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the Secure Me frontend panel."""
    try:
        # Serve frontend static files
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                url_path=PANEL_URL,
                path=FRONTEND_DIR,
                cache_headers=False,
            )
        ])

        # Register the panel in sidebar
        async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=PANEL_TITLE,
            sidebar_icon=PANEL_ICON,
            frontend_url_path=PANEL_FRONTEND_URL_PATH,
            config={
                "_panel_custom": {
                    "name": "secure-me-panel",
                    "module_url": f"{PANEL_URL}/secure-me-panel.js",
                }
            },
            require_admin=False,
        )
        _LOGGER.info("Secure Me panel registered at /%s", PANEL_FRONTEND_URL_PATH)
    except Exception as err:
        _LOGGER.error("Failed to register Secure Me panel: %s", err)


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.info("Options updated, reloading Secure Me")
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    if coordinator:
        coordinator.update_config(entry.data)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Secure Me integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Get entry data
        entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
        
        # Shutdown coordinator
        coordinator = entry_data.get(COORDINATOR)
        if coordinator:
            await coordinator.async_shutdown()

        # Remove update listener
        undo_listener = entry_data.get(UNDO_UPDATE_LISTENER)
        if undo_listener:
            undo_listener()

        # Remove entry data
        hass.data[DOMAIN].pop(entry.entry_id, None)
        
        # Only remove panel if this is the last entry
        remaining_entries = [
            entry_id for entry_id in hass.data[DOMAIN]
            if entry_id not in ["store", "_websocket_registered", "_panel_registered"]
        ]
        
        if not remaining_entries:
            # Last entry - clean up global resources
            try:
                # Remove panel using modern API
                from homeassistant.components.frontend import async_remove_panel
                async_remove_panel(hass, PANEL_FRONTEND_URL_PATH)
                _LOGGER.info("Secure Me panel removed")
            except Exception as err:
                _LOGGER.warning("Failed to remove panel: %s", err)
            
            # Clean up remaining global data
            hass.data.pop(DOMAIN, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
