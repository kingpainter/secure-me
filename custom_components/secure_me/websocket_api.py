"""WebSocket API for Secure Me panel."""
# VERSION = "0.3.0"

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register all websocket commands."""
    websocket_api.async_register_command(hass, ws_get_sensors)
    websocket_api.async_register_command(hass, ws_save_sensors)
    websocket_api.async_register_command(hass, ws_get_zones)
    websocket_api.async_register_command(hass, ws_save_zone)
    websocket_api.async_register_command(hass, ws_delete_zone)
    websocket_api.async_register_command(hass, ws_get_users)
    websocket_api.async_register_command(hass, ws_save_user)
    websocket_api.async_register_command(hass, ws_delete_user)
    websocket_api.async_register_command(hass, ws_get_nfc_tags)
    websocket_api.async_register_command(hass, ws_get_modules)
    websocket_api.async_register_command(hass, ws_save_module)
    websocket_api.async_register_command(hass, ws_get_module_entities)
    websocket_api.async_register_command(hass, ws_get_notifications)
    websocket_api.async_register_command(hass, ws_save_notification)
    websocket_api.async_register_command(hass, ws_delete_notification)
    websocket_api.async_register_command(hass, ws_test_notification)
    websocket_api.async_register_command(hass, ws_get_automations)
    websocket_api.async_register_command(hass, ws_save_automation)
    websocket_api.async_register_command(hass, ws_delete_automation)
    websocket_api.async_register_command(hass, ws_test_automation)
    websocket_api.async_register_command(hass, ws_get_alarm_state)
    websocket_api.async_register_command(hass, ws_get_health_summary)
    websocket_api.async_register_command(hass, ws_run_test)
    websocket_api.async_register_command(hass, ws_get_test_results)

    _LOGGER.info("Secure Me WebSocket API registered")


def _get_store(hass: HomeAssistant):
    """Get the store instance."""
    return hass.data[DOMAIN].get("store")


def _get_coordinator(hass: HomeAssistant):
    """Get the coordinator instance.
    
    The coordinator is stored per config entry under entry.entry_id.
    We iterate to find the first valid coordinator.
    """
    domain_data = hass.data.get(DOMAIN, {})
    for key, value in domain_data.items():
        if isinstance(value, dict) and "coordinator" in value:
            return value["coordinator"]
    return None


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# ALARM STATE
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_alarm_state",
})
@websocket_api.async_response
async def ws_get_alarm_state(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get current alarm state."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_result(msg["id"], {
            "state": "unknown",
            "countdown": 0,
        })
        return

    connection.send_result(msg["id"], {
        "state": coordinator.alarm_state,
        "countdown": coordinator.delay_countdown,
        "armed_by": coordinator.armed_by,
        "disarmed_by": coordinator.disarmed_by,
        "open_sensors": coordinator.open_sensors,
    })


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# SENSORS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_sensors",
})
@websocket_api.async_response
async def ws_get_sensors(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all available sensors."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    sensors = store.get_available_sensors()
    connection.send_result(msg["id"], {"sensors": sensors})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_sensors",
    vol.Required("sensors"): dict,
})
@websocket_api.async_response
async def ws_save_sensors(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save sensor configurations (bulk)."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    await store.async_save_sensors_bulk(msg["sensors"])

    # Update zone manager with new sensor config
    coordinator = _get_coordinator(hass)
    if coordinator:
        _LOGGER.info("Sensors updated, syncing with zone manager")

    connection.send_result(msg["id"], {"success": True})


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# ZONES
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_zones",
})
@websocket_api.async_response
async def ws_get_zones(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all zones."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    zones = store.get_zones()
    connection.send_result(msg["id"], {"zones": zones})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_zone",
    vol.Required("zone_id"): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_zone(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save a zone."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    await store.async_save_zone(msg["zone_id"], msg["config"])

    # Sync with zone manager
    coordinator = _get_coordinator(hass)
    if coordinator and hasattr(coordinator, "zone_manager"):
        _LOGGER.info("Zone %s saved, syncing with zone manager", msg["zone_id"])

    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_zone",
    vol.Required("zone_id"): str,
})
@websocket_api.async_response
async def ws_delete_zone(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a zone."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    success = await store.async_delete_zone(msg["zone_id"])
    connection.send_result(msg["id"], {"success": success})


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# USERS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_users",
})
@websocket_api.async_response
async def ws_get_users(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all users."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    users = store.get_users()
    # Don't send plaintext codes to frontend - mask them
    masked = {}
    for uid, user in users.items():
        masked[uid] = {**user, "code": "Ã¢â‚¬Â¢Ã¢â‚¬Â¢Ã¢â‚¬Â¢Ã¢â‚¬Â¢" if user.get("code") else ""}
    connection.send_result(msg["id"], {"users": masked})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_user",
    vol.Required("user_id"): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_user(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save a user."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    # Generate user_id if new
    user_id = msg["user_id"] or str(uuid.uuid4())[:8]
    await store.async_save_user(user_id, msg["config"])
    connection.send_result(msg["id"], {"success": True, "user_id": user_id})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_user",
    vol.Required("user_id"): str,
})
@websocket_api.async_response
async def ws_delete_user(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a user."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    success = await store.async_delete_user(msg["user_id"])
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_nfc_tags",
})
@websocket_api.async_response
async def ws_get_nfc_tags(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get available NFC tags from HA."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    tags = store.get_nfc_tags()
    connection.send_result(msg["id"], {"tags": tags})


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# MODULES
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_modules",
})
@websocket_api.async_response
async def ws_get_modules(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all module configurations."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    modules = store.get_modules()
    connection.send_result(msg["id"], {"modules": modules})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_module",
    vol.Required("module_id"): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_module(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save module configuration."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    await store.async_save_module(msg["module_id"], msg["config"])

    # Sync with coordinator modules
    coordinator = _get_coordinator(hass)
    if coordinator:
        module_id = msg["module_id"]
        if msg["config"].get("enabled"):
            coordinator.enable_module(module_id)
        else:
            coordinator.disable_module(module_id)
        _LOGGER.info("Module %s config updated", module_id)

    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_module_entities",
    vol.Required("domain"): str,
})
@websocket_api.async_response
async def ws_get_module_entities(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get available entities for a module domain."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    entities = store.get_available_entities(msg["domain"])
    connection.send_result(msg["id"], {"entities": entities})


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# NOTIFICATIONS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_notifications",
})
@websocket_api.async_response
async def ws_get_notifications(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all notifications."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    notifications = store.get_notifications()
    connection.send_result(msg["id"], {"notifications": notifications})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_notification",
    vol.Required("notification_id"): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_notification(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save a notification."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    notif_id = msg["notification_id"] or str(uuid.uuid4())[:8]
    await store.async_save_notification(notif_id, msg["config"])
    connection.send_result(msg["id"], {"success": True, "notification_id": notif_id})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_notification",
    vol.Required("notification_id"): str,
})
@websocket_api.async_response
async def ws_delete_notification(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a notification."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    success = await store.async_delete_notification(msg["notification_id"])
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/test_notification",
    vol.Required("notification_id"): str,
})
@websocket_api.async_response
async def ws_test_notification(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Test a notification by sending it."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    notifications = store.get_notifications()
    notif = notifications.get(msg["notification_id"])
    if not notif:
        connection.send_error(msg["id"], "not_found", "Notification not found")
        return

    # Try to send test notification via notify service
    try:
        service_target = notif.get("service", "notify.notify")
        domain, service = service_target.split(".", 1)

        service_data = {
            "message": notif.get("message", "Test notification from Secure Me"),
            "title": f"Ã°Å¸â€ºÂ¡Ã¯Â¸Â Secure Me Test: {notif.get('name', 'Test')}",
        }

        # Add action buttons if configured
        if notif.get("actions"):
            service_data["data"] = {"actions": notif["actions"]}

        await hass.services.async_call(domain, service, service_data, blocking=True)
        connection.send_result(msg["id"], {"success": True})
    except Exception as err:
        _LOGGER.error("Failed to test notification: %s", err)
        connection.send_result(msg["id"], {"success": False, "error": str(err)})


# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â
# AUTOMATIONS
# Ã¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢ÂÃ¢â€¢Â

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_automations",
})
@websocket_api.async_response
async def ws_get_automations(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all automations."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    automations = store.get_automations()
    connection.send_result(msg["id"], {"automations": automations})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_automation",
    vol.Required("automation_id"): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_automation(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save an automation."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    auto_id = msg["automation_id"] or str(uuid.uuid4())[:8]
    await store.async_save_automation(auto_id, msg["config"])
    connection.send_result(msg["id"], {"success": True, "automation_id": auto_id})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_automation",
    vol.Required("automation_id"): str,
})
@websocket_api.async_response
async def ws_delete_automation(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete an automation."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    success = await store.async_delete_automation(msg["automation_id"])
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/test_automation",
    vol.Required("automation_id"): str,
})
@websocket_api.async_response
async def ws_test_automation(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Test an automation by executing its actions."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    automations = store.get_automations()
    auto = automations.get(msg["automation_id"])
    if not auto:
        connection.send_error(msg["id"], "not_found", "Automation not found")
        return

    # Execute the automation's actions
    try:
        actions = auto.get("actions", [])
        for action in actions:
            service_target = action.get("service", "")
            if "." in service_target:
                domain, service = service_target.split(".", 1)
                service_data = action.get("data", {})
                await hass.services.async_call(
                    domain, service, service_data, blocking=True
                )

        connection.send_result(msg["id"], {"success": True})
    except Exception as err:
        _LOGGER.error("Failed to test automation: %s", err)
        connection.send_result(msg["id"], {"success": False, "error": str(err)})


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# HEALTH SUMMARY
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def _discover_batteries(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Discover all battery sensors in HA."""
    batteries = []
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != "battery":
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


def _get_module_entity_ids(module) -> list[str]:
    """Extract entity IDs from a module."""
    entities = []
    for attr in ("poe_switches", "cameras", "recording_entities",
                 "locks", "lights", "climates", "media_players"):
        val = getattr(module, attr, None)
        if isinstance(val, list):
            entities.extend(val)
    for attr in ("door_sensors", "battery_sensors"):
        val = getattr(module, attr, None)
        if isinstance(val, dict):
            entities.extend(val.values())
    for attr in ("gateway_light",):
        val = getattr(module, attr, None)
        if isinstance(val, str) and "." in val:
            entities.append(val)
    return entities


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_health_summary",
})
@websocket_api.async_response
async def ws_get_health_summary(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get comprehensive health summary for the testing dashboard."""
    coordinator = _get_coordinator(hass)

    # Module health
    modules_health = {}
    total_entities = 0
    available_entities = 0

    if coordinator:
        for mod_id, module in coordinator.modules.items():
            entities = _get_module_entity_ids(module)
            avail = []
            unavail = []
            for eid in entities:
                state = hass.states.get(eid)
                if state and state.state not in ("unavailable", "unknown"):
                    avail.append(eid)
                    available_entities += 1
                else:
                    unavail.append(eid)
                total_entities += 1

            modules_health[mod_id] = {
                "enabled": module.enabled,
                "total": len(entities),
                "available": len(avail),
                "unavailable": unavail,
                "status": "disabled" if not module.enabled else (
                    "problem" if unavail else "ok"
                ),
            }

    health_score = round((available_entities / total_entities) * 100) if total_entities > 0 else 100

    # Battery summary
    batteries = _discover_batteries(hass)
    low_batteries = [b for b in batteries if b["available"] and b["level"] is not None and b["level"] < 20]
    critical_batteries = [b for b in batteries if b["available"] and b["level"] is not None and b["level"] < 10]

    # Alarm state
    alarm_state = coordinator.alarm_state if coordinator else "unknown"

    connection.send_result(msg["id"], {
        "health_score": health_score,
        "total_entities": total_entities,
        "available_entities": available_entities,
        "modules": modules_health,
        "alarm_state": alarm_state,
        "batteries": batteries,
        "low_battery_count": len(low_batteries),
        "critical_battery_count": len(critical_batteries),
    })


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# RUN TEST
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/run_test",
    vol.Required("test_type"): str,  # "quick", "standard", "full", or module name
})
@websocket_api.async_response
async def ws_run_test(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run a system test and return results.

    test_type:
        "quick"    - Entity availability + battery check (vital checks only)
        "standard" - Quick + call async_test() on all enabled modules
        "full"     - Standard + sensor signal test, POE test, zone verify
        "<module>" - Test a specific module (camera, lock, etc.)
    """
    import time
    coordinator = _get_coordinator(hass)
    store = _get_store(hass)

    if not coordinator:
        connection.send_error(msg["id"], "not_ready", "Coordinator not initialized")
        return

    test_type = msg["test_type"]
    start_time = time.time()
    results: dict[str, Any] = {
        "test_type": test_type,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modules": {},
        "batteries": {},
        "sensors": {},
        "overall": "pass",
    }

    # --- Entity availability check (all test types) ---
    for mod_id, module in coordinator.modules.items():
        if not module.enabled:
            results["modules"][mod_id] = {
                "status": "skipped",
                "reason": "disabled",
            }
            continue

        entities = _get_module_entity_ids(module)
        unavail = []
        for eid in entities:
            state = hass.states.get(eid)
            if not state or state.state in ("unavailable", "unknown"):
                unavail.append(eid)

        mod_result = {
            "status": "pass" if not unavail else "fail",
            "entities_total": len(entities),
            "entities_available": len(entities) - len(unavail),
            "unavailable": unavail,
        }

        # --- Standard & Full test: also call async_test() ---
        if test_type in ("standard", "full") or test_type == mod_id:
            try:
                test_out = await module.async_test()
                mod_result["test_result"] = test_out
                if not test_out.get("success", False):
                    mod_result["status"] = "fail"
            except Exception as err:
                mod_result["test_result"] = {
                    "success": False,
                    "message": str(err),
                }
                mod_result["status"] = "error"

        # Skip modules not requested in single-module mode
        if test_type not in ("quick", "standard", "full") and test_type != mod_id:
            mod_result["status"] = "skipped"
            mod_result["reason"] = "not selected"

        results["modules"][mod_id] = mod_result

    # --- Full test: Sensor signal verification ---
    if test_type == "full":
        sensor_results = {}
        if store:
            configured_sensors = store.get_available_sensors()
            enabled_sensors = [s for s in configured_sensors if s.get("enabled")]
            for sensor in enabled_sensors:
                eid = sensor.get("entity_id", "")
                state = hass.states.get(eid)
                sensor_ok = state and state.state not in ("unavailable", "unknown")
                sensor_results[eid] = {
                    "name": sensor.get("name", eid),
                    "type": sensor.get("sensor_type", "unknown"),
                    "online": sensor_ok,
                    "state": state.state if state else "missing",
                    "status": "pass" if sensor_ok else "fail",
                }
            results["sensors"] = {
                "total": len(enabled_sensors),
                "online": sum(1 for s in sensor_results.values() if s["online"]),
                "offline": sum(1 for s in sensor_results.values() if not s["online"]),
                "details": sensor_results,
                "status": "fail" if any(not s["online"] for s in sensor_results.values()) else "pass",
            }

    # --- Overall result (batteries excluded - they are info only) ---
    duration = round(time.time() - start_time, 1)
    results["duration_seconds"] = duration

    any_fail = any(
        m.get("status") == "fail" or m.get("status") == "error"
        for m in results["modules"].values()
    )
    sensor_fail = results.get("sensors", {}).get("status") == "fail"
    if any_fail or sensor_fail:
        results["overall"] = "fail"

    # Compute summary counts
    passed = sum(1 for m in results["modules"].values() if m.get("status") == "pass")
    failed = sum(1 for m in results["modules"].values() if m.get("status") in ("fail", "error"))
    skipped = sum(1 for m in results["modules"].values() if m.get("status") == "skipped")
    results["summary"] = {
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }

    # --- Store result ---
    if store:
        test_history = store._data.get("test_history", [])
        # Keep last 10 results
        test_history.insert(0, results)
        test_history = test_history[:10]
        store._data["test_history"] = test_history
        await store.async_save()

    connection.send_result(msg["id"], results)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# TEST RESULTS
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_test_results",
})
@websocket_api.async_response
async def ws_get_test_results(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get stored test result history."""
    store = _get_store(hass)
    if not store:
        connection.send_result(msg["id"], {"results": []})
        return

    results = store._data.get("test_history", [])
    connection.send_result(msg["id"], {"results": results})
