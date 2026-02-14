# VERSION = "0.3.1"
"""The Secure Me integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    COORDINATOR,
    UNDO_UPDATE_LISTENER,
    DEFAULT_NAME,
)
from .coordinator import SecureMeCoordinator
from .store import SecureMeStore
from .websocket_api import async_register_websocket_api

if TYPE_CHECKING:
    from homeassistant.components import system_health

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Secure Me component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Secure Me from a config entry."""
    _LOGGER.debug("Setting up Secure Me integration")
    
    # Initialize domain data if not exists
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    # Initialize store (global, shared across entries)
    if "store" not in hass.data[DOMAIN]:
        store = SecureMeStore(hass)
        await store.async_load()
        hass.data[DOMAIN]["store"] = store
    else:
        store = hass.data[DOMAIN]["store"]
    
    # Create coordinator for this entry
    coordinator = SecureMeCoordinator(hass, entry)
    
    # Initial data fetch
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Error during initial data fetch: %s", err)
        raise ConfigEntryNotReady from err
    
    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }
    
    # Register device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get("name", DEFAULT_NAME),
        manufacturer="KingPainter",
        model="Secure Me",
        sw_version=entry.data.get("version", "0.3.1"),
    )
    
    # Register WebSocket API (global, once)
    if not hass.data[DOMAIN].get("_websocket_registered", False):
        async_register_websocket_api(hass)
        hass.data[DOMAIN]["_websocket_registered"] = True
        _LOGGER.debug("WebSocket API registered")
    
    # Register frontend panel (Alarmo-style - using panel.py module)
    if not hass.data[DOMAIN].get("_panel_registered", False):
        from .panel import async_register_panel
        
        try:
            await async_register_panel(hass)
            hass.data[DOMAIN]["_panel_registered"] = True
        except Exception as err:
            _LOGGER.error(f"Panel registration failed: {err}")
            # Continue setup even if panel fails
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # System health is auto-registered via system_health.py
    _LOGGER.debug("System health available via system_health.py")
    
    # Register update listener
    undo_listener = entry.add_update_listener(async_update_options)
    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER] = undo_listener
    
    _LOGGER.info("Secure Me integration setup complete")
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Secure Me integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove update listener
        entry_data = hass.data[DOMAIN][entry.entry_id]
        undo_listener = entry_data[UNDO_UPDATE_LISTENER]
        undo_listener()
        
        # Remove coordinator
        hass.data[DOMAIN].pop(entry.entry_id)
        
        _LOGGER.info("Secure Me integration unloaded")
    
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    _LOGGER.debug("Removing Secure Me integration")
    
    # Clean up store data if last entry
    remaining_entries = [
        e for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id
    ]
    
    if not remaining_entries:
        # Last entry being removed
        store = hass.data[DOMAIN].get("store")
        if store:
            # Optionally clear all data
            # await store.async_remove()
            pass
        
        # Unregister panel
        from .panel import async_unregister_panel
        async_unregister_panel(hass)
        
        # Clear global data
        hass.data[DOMAIN].pop("store", None)
        hass.data[DOMAIN].pop("_websocket_registered", None)
        hass.data[DOMAIN].pop("_panel_registered", None)
        hass.data[DOMAIN].pop("_system_health_registered", None)
        
        _LOGGER.info("Secure Me integration removed (last entry)")
