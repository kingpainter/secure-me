# VERSION = "1.2.0"
"""The Secure Me integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr, config_validation as cv

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

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

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
    await coordinator.async_load_store_config(store)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Error during initial data fetch: %s", err)
        raise ConfigEntryNotReady from err

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
        sw_version=entry.data.get("version", "1.2.0"),
    )

    # Register WebSocket API (global, once)
    if not hass.data[DOMAIN].get("_websocket_registered", False):
        async_register_websocket_api(hass)
        hass.data[DOMAIN]["_websocket_registered"] = True
        _LOGGER.debug("WebSocket API registered")

    # Register frontend panel (global, once) — lazy import avoids HA HTTP
    # import errors in test environments.
    if not hass.data[DOMAIN].get("_panel_registered", False):
        try:
            from . import panel as _panel
            await _panel.async_register_panel(hass)
            hass.data[DOMAIN]["_panel_registered"] = True
        except Exception as err:
            _LOGGER.error("Panel registration failed: %s", err)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].get(entry.entry_id, {})

        # Shutdown coordinator
        coordinator = entry_data.get(COORDINATOR)
        if coordinator:
            await coordinator.async_shutdown()

        # Remove update listener
        undo_listener = entry_data.get(UNDO_UPDATE_LISTENER)
        if undo_listener:
            undo_listener()

        # Unregister panel if last entry
        remaining = [k for k in hass.data[DOMAIN] if k not in (
            entry.entry_id, "store", "_websocket_registered",
            "_panel_registered", "_notification_dispatcher",
        )]
        if not remaining:
            try:
                from . import panel as _panel
                _panel.async_unregister_panel(hass)
            except Exception:
                pass
            hass.data[DOMAIN]["_panel_registered"] = False

        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Secure Me integration unloaded successfully")

    return unload_ok
