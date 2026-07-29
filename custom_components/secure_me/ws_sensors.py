"""WebSocket API — Sensor, Zone and User commands for Secure Me."""
# VERSION = "1.5.3"
from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

from .ws_helpers import _get_store, _get_coordinator


# SENSOR GROUPS (anti-masking) — v1.2.0
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_sensor_groups",
})
@websocket_api.async_response
async def ws_get_sensor_groups(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all sensor groups."""
    store = hass.data.get(DOMAIN, {}).get("store")
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    connection.send_result(msg["id"], {"sensor_groups": store.get_sensor_groups()})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_sensor_group",
    vol.Optional("group_id"): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_sensor_group(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Create or update a sensor group."""
    store = hass.data.get(DOMAIN, {}).get("store")
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    group_id = await store.async_save_sensor_group(
        msg.get("group_id"), msg["config"]
    )
    # Reload sensor groups into active zone manager
    coordinator = _get_coordinator(hass)
    if coordinator:
        coordinator.zone_manager.load_sensor_groups(store.get_sensor_groups())
    connection.send_result(msg["id"], {"success": True, "group_id": group_id})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_sensor_group",
    vol.Required("group_id"): str,
})
@websocket_api.async_response
async def ws_delete_sensor_group(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a sensor group."""
    store = hass.data.get(DOMAIN, {}).get("store")
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    success = await store.async_delete_sensor_group(msg["group_id"])
    coordinator = _get_coordinator(hass)
    if coordinator:
        coordinator.zone_manager.load_sensor_groups(store.get_sensor_groups())
    connection.send_result(msg["id"], {"success": success})


#
# ALARM STATE
# 

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


# 
# SENSORS
# 

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


#
# ZONES
#

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

    config = msg["config"]
    # Ensure arm_modes has a valid default
    config.setdefault("arm_modes", ["away"])
    await store.async_save_zone(msg["zone_id"], config)

    # Sync with zone manager — reload all zones so arm_modes take effect
    coordinator = _get_coordinator(hass)
    if coordinator and hasattr(coordinator, "zone_manager"):
        _reload_zones_into_coordinator(coordinator, store)
        _LOGGER.info("Zone %s saved and reloaded into zone manager", msg["zone_id"])

    connection.send_result(msg["id"], {"success": True})


def _reload_zones_into_coordinator(coordinator, store) -> None:
    """Rebuild zone_manager zones from store data."""
    zm = coordinator.zone_manager
    # Remove all existing zones cleanly
    for zone_id in list(zm._zones.keys()):
        zm.remove_zone(zone_id)
    # Re-add from store
    for zone_id, zone_cfg in store.get_zones().items():
        zm.add_zone(
            zone_id=zone_id,
            zone_type=zone_cfg.get("zone_type", "entry"),
            sensors=zone_cfg.get("sensors", []),
            enabled=zone_cfg.get("enabled", True),
            arm_modes=zone_cfg.get("arm_modes", ["away"]),
        )

    # v1.4.0: Re-merge Home Alone per-sensor config into zone manager sensor_configs
    sensor_configs = store.get_sensors()
    for zone_cfg in store.get_zones().values():
        ha_cfg = zone_cfg.get("home_alone_sensor_config", {})
        for eid, ha_fields in ha_cfg.items():
            if eid not in sensor_configs:
                sensor_configs[eid] = {}
            sensor_configs[eid].update(ha_fields)
    zm.load_sensor_configs(sensor_configs)


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

    # v1.4.3 fix: Sync coordinator's zone_manager so the deleted zone
    # disappears from runtime state immediately. Previously the zone
    # stayed alive in zone_manager._zones until HA restart, and could
    # still be triggered by sensor events.
    if success:
        coordinator = _get_coordinator(hass)
        if coordinator and hasattr(coordinator, "zone_manager"):
            _reload_zones_into_coordinator(coordinator, store)
            _LOGGER.info("Zone %s deleted and zone manager reloaded", msg["zone_id"])

    connection.send_result(msg["id"], {"success": success})


#
# USERS
#

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
        masked[uid] = {**user, "code": "********" if user.get("code") else ""}
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
    # store.async_save_user handles bcrypt hashing automatically
    # Do NOT pass code_hashed=True from frontend - let store manage it
    config = dict(msg["config"])
    config.pop("code_hashed", None)  # strip any frontend-supplied flag
    await store.async_save_user(user_id, config)

    # Refresh presence monitor so tracker_entity edits take effect without
    # requiring a Home Assistant restart.
    coordinator = _get_coordinator(hass)
    if coordinator is not None and getattr(coordinator, "_presence_monitor", None) is not None:
        coordinator._presence_monitor.async_refresh()

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

    # Refresh presence monitor so removed users' trackers are unsubscribed
    # without requiring a Home Assistant restart.
    if success:
        coordinator = _get_coordinator(hass)
        if coordinator is not None and getattr(coordinator, "_presence_monitor", None) is not None:
            coordinator._presence_monitor.async_refresh()

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


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_persons",
})
@websocket_api.async_response
async def ws_get_persons(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all person entities from HA for user-tracker binding."""
    persons = []
    for state in hass.states.async_all("person"):
        persons.append({
            "entity_id": state.entity_id,
            "name": state.attributes.get("friendly_name", state.entity_id),
            "state": state.state,
        })
    connection.send_result(msg["id"], {"persons": persons})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/hide_sensor",
    vol.Required("entity_id"): str,
    vol.Optional("hidden", default=True): bool,
})
@websocket_api.async_response
async def ws_hide_sensor(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Mark a sensor as excluded (hidden) from the panel."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    entity_id = msg["entity_id"]
    sensors = dict(store.get_sensors())
    if msg["hidden"]:
        sensors[entity_id] = {**sensors.get(entity_id, {}), "excluded": True, "enabled": False}
    else:
        cfg = dict(sensors.get(entity_id, {}))
        cfg.pop("excluded", None)
        sensors[entity_id] = cfg
    await store.async_save_sensors_bulk(sensors)
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/unmark_environmental",
    vol.Required("entity_id"): str,
})
@websocket_api.async_response
async def ws_unmark_environmental(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Remove environmental classification from a sensor (user corrected mis-classification)."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    entity_id = msg["entity_id"]
    sensors = dict(store.get_sensors())
    sensors[entity_id] = {
        **sensors.get(entity_id, {}),
        "env_unmarked": True,
        "is_environmental": False,
        "excluded": True,
        "enabled": False,
    }
    await store.async_save_sensors_bulk(sensors)
    connection.send_result(msg["id"], {"success": True})


#
# MODULES
#

