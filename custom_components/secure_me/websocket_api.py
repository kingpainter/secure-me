"""WebSocket API for Secure Me panel."""
# VERSION = "1.5.0"

import asyncio
import base64
import binascii
import logging
import os
import struct
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .ws_helpers import _discover_batteries  # avoids circular import with coordinator
from .const import (
    DOMAIN,
    FLOORPLAN_DIR_NAME,
    FLOORPLAN_IMAGE_NAME,
    FLOORPLAN_MAX_BYTES,
    FLOORPLAN_URL_PATH,
    ATTR_FLOORPLAN_IMAGE_URL,
    ATTR_FLOORPLAN_WIDTH,
    ATTR_FLOORPLAN_HEIGHT,
    ATTR_FLOORPLAN_MARKERS,
    ATTR_MARKER_X_PCT,
    ATTR_MARKER_Y_PCT,
    ATTR_MARKER_LABEL,
    ATTR_MARKER_KIND,
    CONF_AUTO_ACTIONS,
    FP_ACTIVE,
    FP_BLOCK_ALARM,
    FP_BLOCK_LOCKS,
    FP_BLOCK_CAMERAS,
)
from .notification_dispatcher import async_setup_dispatcher

_LOGGER = logging.getLogger(__name__)


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register all websocket commands and start the notification dispatcher."""
    websocket_api.async_register_command(hass, ws_get_sensors)
    websocket_api.async_register_command(hass, ws_save_sensors)
    websocket_api.async_register_command(hass, ws_hide_sensor)
    websocket_api.async_register_command(hass, ws_unmark_environmental)
    # Arm / disarm commands (used by alarm card for custom modes)
    websocket_api.async_register_command(hass, ws_arm_away)
    websocket_api.async_register_command(hass, ws_arm_home)
    websocket_api.async_register_command(hass, ws_arm_night)
    websocket_api.async_register_command(hass, ws_arm_vacation)
    websocket_api.async_register_command(hass, ws_arm_home_alone)
    websocket_api.async_register_command(hass, ws_disarm)
    websocket_api.async_register_command(hass, ws_skip_delay)  # v1.4.3
    # Speaker profiles (v1.4.0)
    websocket_api.async_register_command(hass, ws_get_speaker_profiles)
    websocket_api.async_register_command(hass, ws_save_speaker_profiles)
    # Home Alone quick messages for alarm card
    websocket_api.async_register_command(hass, ws_get_home_alone_messages)
    websocket_api.async_register_command(hass, ws_get_zones)
    websocket_api.async_register_command(hass, ws_save_zone)
    websocket_api.async_register_command(hass, ws_delete_zone)
    websocket_api.async_register_command(hass, ws_get_users)
    websocket_api.async_register_command(hass, ws_save_user)
    websocket_api.async_register_command(hass, ws_delete_user)
    websocket_api.async_register_command(hass, ws_get_nfc_tags)
    websocket_api.async_register_command(hass, ws_get_persons)
    websocket_api.async_register_command(hass, ws_get_modules)
    websocket_api.async_register_command(hass, ws_save_module)
    websocket_api.async_register_command(hass, ws_get_module_entities)
    websocket_api.async_register_command(hass, ws_get_notifications)
    websocket_api.async_register_command(hass, ws_save_notification)
    websocket_api.async_register_command(hass, ws_delete_notification)
    websocket_api.async_register_command(hass, ws_test_notification)
    websocket_api.async_register_command(hass, ws_get_notify_services)
    websocket_api.async_register_command(hass, ws_test_tts)
    # v1.2.0: sensor groups (anti-masking)
    websocket_api.async_register_command(hass, ws_get_sensor_groups)
    websocket_api.async_register_command(hass, ws_save_sensor_group)
    websocket_api.async_register_command(hass, ws_delete_sensor_group)
    websocket_api.async_register_command(hass, ws_get_automations)
    websocket_api.async_register_command(hass, ws_save_automation)
    websocket_api.async_register_command(hass, ws_delete_automation)
    websocket_api.async_register_command(hass, ws_test_automation)
    websocket_api.async_register_command(hass, ws_get_scheduled_tests)
    websocket_api.async_register_command(hass, ws_save_scheduled_test)
    websocket_api.async_register_command(hass, ws_delete_scheduled_test)
    websocket_api.async_register_command(hass, ws_run_scheduled_test_now)
    websocket_api.async_register_command(hass, ws_get_alarm_state)
    websocket_api.async_register_command(hass, ws_get_health_summary)
    websocket_api.async_register_command(hass, ws_run_test)
    websocket_api.async_register_command(hass, ws_quick_test_siren)
    websocket_api.async_register_command(hass, ws_quick_test_lights)
    websocket_api.async_register_command(hass, ws_get_test_results)
    websocket_api.async_register_command(hass, ws_get_fake_presence)
    websocket_api.async_register_command(hass, ws_set_fake_presence)
    websocket_api.async_register_command(hass, ws_get_home_alone_cameras)
    websocket_api.async_register_command(hass, ws_save_home_alone_cameras)
    # Auto Actions v2 (v1.5.0)
    websocket_api.async_register_command(hass, ws_get_auto_actions)
    websocket_api.async_register_command(hass, ws_save_auto_actions)
    websocket_api.async_register_command(hass, ws_get_fake_presence_v2)
    websocket_api.async_register_command(hass, ws_save_fake_presence_v2)
    # Floorplan (v1.5.0)
    websocket_api.async_register_command(hass, ws_get_floorplan)
    websocket_api.async_register_command(hass, ws_save_floorplan_image)
    websocket_api.async_register_command(hass, ws_save_floorplan_markers)
    websocket_api.async_register_command(hass, ws_delete_floorplan)

    # Start notification dispatcher (listens for alarm + sensor events)
    dispatcher = async_setup_dispatcher(hass)
    hass.data.setdefault(DOMAIN, {})["_notification_dispatcher"] = dispatcher

    _LOGGER.info("Secure Me WebSocket API registered")


#
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
        masked[uid] = {**user, "code": "????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????" if user.get("code") else ""}
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

    # Sync with coordinator: re-initialize module with normalized config.
    # Panel saves objects [{entity_id, ...}] but module classes expect flat strings.
    coordinator = _get_coordinator(hass)
    if coordinator:
        module_id = msg["module_id"]
        normalized = _normalize_module_config(module_id, msg["config"])
        coordinator.update_module_config(module_id, normalized)
        _LOGGER.info("Module %s config synced to coordinator", module_id)

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


#
# NOTIFICATIONS
#

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

    trigger = notif.get("trigger", "")

    # --- Low battery: use dispatcher to build dynamic sensor list ---
    if trigger == "low_battery":
        dispatcher = hass.data.get(DOMAIN, {}).get("_notification_dispatcher")
        if dispatcher:
            try:
                await dispatcher.dispatch_low_battery()
                connection.send_result(msg["id"], {"success": True})
            except Exception as err:
                _LOGGER.error("Failed to test low_battery notification: %s", err)
                connection.send_result(msg["id"], {"success": False, "error": str(err)})
        else:
            connection.send_result(msg["id"], {"success": False, "error": "Dispatcher not ready"})
        return

    # --- Smoke: inject a fake sensor name, send only to admins ---
    if trigger == "smoke":
        from .notification_dispatcher import _build_message, _send_push
        raw = notif.get("message", "")
        message = _build_message(raw, {"sensor": "Test Smoke Detector", "entity_id": "binary_sensor.test_smoke"})
        title = "TEST - FIRE ALERT: Test Smoke Detector"
        try:
            admin_services = [u.get("notify_service") for u in store.get_users().values()
                              if u.get("enabled", True) and u.get("admin") and u.get("notify_service")]
            if not admin_services:
                admin_services = [notif.get("service", "notify.notify")]
            for svc in admin_services:
                await _send_push(hass, svc, title, message)
            connection.send_result(msg["id"], {"success": True})
        except Exception as err:
            connection.send_result(msg["id"], {"success": False, "error": str(err)})
        return

    # --- Water leak: inject a fake sensor name, send only to admins ---
    if trigger == "water_leak":
        from .notification_dispatcher import _build_message, _send_push
        raw = notif.get("message", "")
        message = _build_message(raw, {"sensor": "Test Moisture Sensor", "entity_id": "binary_sensor.test_moisture"})
        title = "TEST - WATER LEAK: Test Moisture Sensor"
        try:
            admin_services = [u.get("notify_service") for u in store.get_users().values()
                              if u.get("enabled", True) and u.get("admin") and u.get("notify_service")]
            if not admin_services:
                admin_services = [notif.get("service", "notify.notify")]
            for svc in admin_services:
                await _send_push(hass, svc, title, message)
            connection.send_result(msg["id"], {"success": True})
        except Exception as err:
            connection.send_result(msg["id"], {"success": False, "error": str(err)})
        return

    # --- All other triggers: route via configured channels ---
    try:
        title = f"TEST: {notif.get('name', 'Secure Me Test')}"
        context_map = {
            "state": "test", "armed_by": "Test", "disarmed_by": "Test",
            "triggered_by": "Test", "sensor_list": "Test sensor", "count": "1",
        }
        from .notification_dispatcher import _build_message, _send_push, _get_tts_module
        message = _build_message(notif.get("message", "Test notification from Secure Me"), context_map)
        channels = notif.get("channels", ["push"])
        if isinstance(channels, str):
            channels = [channels]

        if "push" in channels:
            # Route to admin users only, fallback to notification service
            admin_services = [
                u.get("notify_service")
                for u in store.get_users().values()
                if u.get("enabled", True) and u.get("admin") and u.get("notify_service")
            ]
            if not admin_services:
                admin_services = [notif.get("service", "notify.notify")]
            for svc in admin_services:
                await _send_push(hass, svc, title, message)

        if "tts" in channels and message:
            speaker_ids = notif.get("tts_speakers") or None
            tts = _get_tts_module(hass)
            if tts:
                await tts.announce_system(message, urgent=False, speaker_ids=speaker_ids)
            else:
                _LOGGER.warning("TTS test: TTS module not enabled or not configured")

        connection.send_result(msg["id"], {"success": True})
    except Exception as err:
        _LOGGER.error("Failed to test notification: %s", err)
        connection.send_result(msg["id"], {"success": False, "error": str(err)})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_notify_services",
})
@websocket_api.async_response
async def ws_get_notify_services(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return all available notify services from HA.

    Scans hass.services for the 'notify' domain and returns a flat list
    of service IDs (e.g. 'notify.mobile_app_myphone') so the frontend
    can offer a dropdown instead of a free-text input.
    """
    services: list[str] = []
    notify_services = hass.services.async_services().get("notify", {})
    for service_name in sorted(notify_services.keys()):
        services.append(f"notify.{service_name}")

    connection.send_result(msg["id"], {"services": services})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/test_tts",
    vol.Required("message"): str,
    vol.Optional("speaker_ids"): list,
})
@websocket_api.async_response
async def ws_test_tts(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Test TTS by playing a message immediately via the TTS module.

    speaker_ids: optional list of media_player entity_ids to target.
                 None/omitted = all configured speakers.
    """
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return

    tts_module = coordinator.modules.get("tts")
    if not tts_module or not tts_module.enabled:
        connection.send_error(msg["id"], "tts_not_enabled", "TTS module is not enabled")
        return

    speaker_ids = msg.get("speaker_ids") or None

    try:
        from .notification_dispatcher import _is_tts_quiet_now
        store = _get_store(hass)
        admins = [
            u for u in (store.get_users().values() if store else [])
            if u.get("enabled", True) and u.get("admin")
        ]
        if admins and all(_is_tts_quiet_now(u) for u in admins):
            connection.send_result(msg["id"], {"success": False, "error": "TTS quiet hours active for all admins"})
            return
        await tts_module.announce_system(msg["message"], speaker_ids=speaker_ids)
        connection.send_result(msg["id"], {"success": True})
    except Exception as err:
        _LOGGER.error("TTS test failed: %s", err)
        connection.send_result(msg["id"], {"success": False, "error": str(err)})


#
# AUTOMATIONS
#

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


#
# HEALTH SUMMARY
#






def _normalize_module_config(module_id: str, config: dict) -> dict:
    """Normalize panel config format to module class format.

    Panel saves entity lists as objects: [{entity_id, poe_port, ...}]
    Module classes expect flat string lists: ["entity.id", ...]

    This bridges the two formats so health checks work correctly.
    """
    normalized = dict(config)  # copy

    def extract_ids(items) -> list[str]:
        """Extract entity_id strings from a list of objects or strings."""
        if not isinstance(items, list):
            return []
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict) and item.get("entity_id"):
                result.append(item["entity_id"])
        return [e for e in result if e and "." in e]

    if module_id == "camera":
        # cameras: [{entity_id, poe_port}] -> cameras: [str], poe_switches: [str]
        raw_cameras = config.get("cameras", [])
        normalized["cameras"] = extract_ids(raw_cameras)
        # Extract POE switches from camera objects
        poe = [c["poe_port"] for c in raw_cameras
               if isinstance(c, dict) and c.get("poe_port") and "." in str(c["poe_port"])]
        if poe:
            normalized["poe_switches"] = poe

    elif module_id == "lock":
        # locks: [{entity_id, ...}] -> locks: [str]
        normalized["locks"] = extract_ids(config.get("locks", []))

    elif module_id == "climate":
        # thermostats: [{entity_id, ...}] -> climates: [str]
        normalized["climates"] = extract_ids(config.get("thermostats", []))

    elif module_id == "lights":
        # Frontend saves as 'entities' (flat strings); module class expects 'lights'
        raw = config.get("entities") or config.get("lights", [])
        normalized["lights"] = extract_ids(raw) if raw else []

    elif module_id == "tts":
        # entities: already flat strings in TTS - no change needed
        normalized["media_players"] = extract_ids(config.get("entities", []))
        # Pass tts_service through so TTSModule can use google_say etc.
        if config.get("tts_service"):
            normalized["tts_service"] = config["tts_service"]
        if config.get("language"):
            normalized["language"] = config["language"]
        if config.get("volume") is not None:
            normalized["volume"] = float(config["volume"]) / 100.0
        if config.get("messages"):
            normalized["messages"] = config["messages"]
        # v1.4.0: speaker profiles passed through as-is
        normalized["speaker_profiles"] = config.get("speaker_profiles", [])
        normalized["custom_messages"] = config.get("custom_messages", [])

    elif module_id == "siren":
        # Pass sirens list through as-is (list of dicts with entity_id, pattern, duration, volume)
        normalized["sirens"] = config.get("sirens", [])
        # Legacy gateway fields
        if config.get("gateway_mac"):
            normalized["gateway_mac"] = config["gateway_mac"]
        if config.get("gateway_light"):
            normalized["gateway_light"] = config["gateway_light"]

    return normalized


def _get_module_entity_ids(module) -> list[str]:
    """Extract entity IDs from a module."""
    entities = []
    
    # Check module attributes (cameras, locks, etc.)
    for attr in ("poe_switches", "cameras", "recording_entities",
                 "locks", "lights", "climates", "media_players"):
        val = getattr(module, attr, None)
        if isinstance(val, list):
            entities.extend(val)

    # Siren module: sirens is a list of dicts with entity_id
    sirens_val = getattr(module, "sirens", None)
    if isinstance(sirens_val, list):
        for entry in sirens_val:
            if isinstance(entry, dict) and entry.get("entity_id"):
                entities.append(entry["entity_id"])
            elif isinstance(entry, str) and "." in entry:
                entities.append(entry)
    
    # Check dict attributes
    for attr in ("door_sensors", "battery_sensors"):
        val = getattr(module, attr, None)
        if isinstance(val, dict):
            entities.extend(val.values())
    
    # Check single string attributes
    for attr in ("gateway_light",):
        val = getattr(module, attr, None)
        if isinstance(val, str) and "." in val:
            entities.append(val)
    
    # FALLBACK: If no entities found, try config dict
    if not entities and hasattr(module, 'config'):
        config = module.config
        # Fix F5: Camera module uses 'entities' key
        for key in ("entities", "cameras", "locks", "climates", "lights", "media_players"):
            if key in config and isinstance(config[key], list):
                entities.extend(config[key])
    
    # Remove duplicates and filter out None/empty strings
    entities = [e for e in entities if e and isinstance(e, str) and "." in e]
    return list(set(entities))  # Remove duplicates


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

    # Battery summary — cached via coordinator (5-minute TTL) to avoid
    # scanning all HA entities on every health poll.
    store = _get_store(hass)
    configured_eids: set[str] = set()
    if store:
        configured_eids = {s["entity_id"] for s in store.get_available_sensors() if s.get("entity_id")}
    if coordinator and hasattr(coordinator, "get_batteries_cached"):
        batteries = coordinator.get_batteries_cached(configured_eids)
    else:
        batteries = _discover_batteries(hass, configured_eids)
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
        "armed_by": coordinator.armed_by if coordinator else None,
        "triggered_by": coordinator.triggered_by if coordinator else None,
        "last_triggered": getattr(coordinator, "_last_triggered", None) if coordinator else None,
        "bypassed_sensors": getattr(coordinator, "_bypassed_sensors", []) if coordinator else [],
        "open_sensors": coordinator.open_sensors if coordinator else [],
        "arm_history": coordinator.arm_history[:10] if coordinator else [],
    })


#
# RUN TEST
#

async def _run_test_internal(hass: HomeAssistant, test_type: str) -> dict[str, Any]:
    """Run a system test and return results dict.

    Shared by ws_run_test (manual) and _check_scheduled_tests (scheduled).
    test_type: "quick" | "standard" | "full" | "<module_id>"
    """
    import time
    coordinator = _get_coordinator(hass)
    store = _get_store(hass)

    results: dict[str, Any] = {
        "test_type": test_type,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "modules": {},
        "batteries": {},
        "sensors": {},
        "overall": "pass",
    }

    if not coordinator:
        results["overall"] = "error"
        results["error"] = "Coordinator not initialized"
        return results

    start_time = time.time()

    # --- Entity availability check (all test types) ---
    for mod_id, module in coordinator.modules.items():
        if not module.enabled:
            results["modules"][mod_id] = {"status": "skipped", "reason": "disabled"}
            continue

        entities = _get_module_entity_ids(module)

        if len(entities) == 0:
            results["modules"][mod_id] = {
                "status": "warning", "reason": "no_entities",
                "message": "Module is enabled but has no entities configured",
                "entities_total": 0, "entities_available": 0, "unavailable": [],
            }
            continue

        unavail = [
            eid for eid in entities
            if not hass.states.get(eid) or hass.states.get(eid).state in ("unavailable", "unknown")
        ]
        mod_result = {
            "status": "pass" if not unavail else "fail",
            "entities_total": len(entities),
            "entities_available": len(entities) - len(unavail),
            "unavailable": unavail,
        }

        if test_type in ("standard", "full") or test_type == mod_id:
            try:
                test_out = await module.async_test()
                mod_result["test_result"] = test_out
                if not test_out.get("success", False):
                    mod_result["status"] = "fail"
            except Exception as err:
                mod_result["test_result"] = {"success": False, "message": str(err)}
                mod_result["status"] = "error"

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

    # --- Environmental sensors: smoke + water leak (standard + full) ---
    # These are always-on sensors not tied to a module, so we test them explicitly.
    if test_type in ("standard", "full") and store:
        env_sensors = [
            s for s in store.get_available_sensors()
            if s.get("sensor_type") == "environmental" or s.get("is_environmental", False)
        ]
        env_results = {}
        for sensor in env_sensors:
            eid = sensor.get("entity_id", "")
            state = hass.states.get(eid)
            online = state is not None and state.state not in ("unavailable", "unknown")
            env_results[eid] = {
                "name": sensor.get("name", eid),
                "device_class": sensor.get("device_class", "unknown"),
                "online": online,
                "state": state.state if state else "missing",
                "status": "pass" if online else "fail",
            }
        results["environmental"] = {
            "total": len(env_sensors),
            "online": sum(1 for s in env_results.values() if s["online"]),
            "offline": sum(1 for s in env_results.values() if not s["online"]),
            "details": env_results,
            "status": "fail" if any(not s["online"] for s in env_results.values()) else "pass",
        }

    # --- Siren sound test (standard + full) ---
    # Brief 2s test tone at low volume, mirrors v3.0.3 logic.
    if test_type in ("standard", "full"):
        siren_module = coordinator.modules.get("siren") if coordinator else None
        if siren_module and siren_module.enabled and siren_module.gateway_mac:
            try:
                await siren_module.hass.services.async_call(
                    "xiaomi_aqara", "play_ringtone",
                    service_data={
                        "gw_mac": siren_module.gateway_mac,
                        "ringtone_id": siren_module.ringtone_id,
                        "ringtone_vol": 30,
                    },
                    blocking=True,
                )
                await asyncio.sleep(2)
                await siren_module.hass.services.async_call(
                    "xiaomi_aqara", "stop_ringtone",
                    service_data={"gw_mac": siren_module.gateway_mac},
                    blocking=True,
                )
                results["siren_test"] = {"success": True, "message": "2s test tone at 30% volume"}
            except Exception as err:
                _LOGGER.warning("Siren sound test failed during standard test: %s", err)
                results["siren_test"] = {"success": False, "message": str(err)}
        else:
            results["siren_test"] = {"success": None, "message": "Siren not configured or not enabled"}

    # --- Battery discovery (standard + full) — use coordinator cache ---
    if test_type in ("standard", "full"):
        configured_eids_bat: set[str] = set()
        if store:
            configured_eids_bat = {s["entity_id"] for s in store.get_available_sensors() if s.get("entity_id")}
        if coordinator and hasattr(coordinator, "get_batteries_cached"):
            coordinator.invalidate_battery_cache()  # force fresh data during explicit test
            batteries = coordinator.get_batteries_cached(configured_eids_bat)
        else:
            batteries = _discover_batteries(hass, configured_eids_bat)
        low = [b for b in batteries if b["available"] and b["level"] is not None and b["level"] < 20]
        critical = [b for b in batteries if b["available"] and b["level"] is not None and b["level"] < 10]
        results["batteries"] = {
            "total": len(batteries), "low_count": len(low), "critical_count": len(critical),
            "details": batteries, "note": "Battery status is informational only",
        }

    # --- Overall result ---
    duration = round(time.time() - start_time, 1)
    results["duration_seconds"] = duration

    any_fail = any(m.get("status") in ("fail", "error") for m in results["modules"].values())
    sensor_fail = results.get("sensors", {}).get("status") == "fail"
    env_fail = results.get("environmental", {}).get("status") == "fail"
    siren_fail = results.get("siren_test", {}).get("success") is False
    if any_fail or sensor_fail or env_fail or siren_fail:
        results["overall"] = "fail"
    elif any(m.get("status") == "warning" for m in results["modules"].values()):
        results["overall"] = "warning"

    passed  = sum(1 for m in results["modules"].values() if m.get("status") == "pass")
    failed  = sum(1 for m in results["modules"].values() if m.get("status") in ("fail", "error"))
    warned  = sum(1 for m in results["modules"].values() if m.get("status") == "warning")
    skipped = sum(1 for m in results["modules"].values() if m.get("status") == "skipped")
    results["summary"] = {"passed": passed, "failed": failed, "warned": warned, "skipped": skipped}

    # --- Persist to test history (via store method — no direct _data access) ---
    if store:
        await store.async_append_test_result(results)

    return results


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/run_test",
    vol.Required("test_type"): str,
})
@websocket_api.async_response
async def ws_run_test(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run a system test and return results."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_ready", "Coordinator not initialized")
        return

    results = await _run_test_internal(hass, msg["test_type"])
    connection.send_result(msg["id"], results)


#
# QUICK SIREN TEST
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/quick_test_siren",
})
@websocket_api.async_response
async def ws_quick_test_siren(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run a quick 2s siren test using the configured siren entities."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_ready", "Coordinator not initialized")
        return

    siren_module = coordinator.modules.get("siren")
    if not siren_module or not siren_module.enabled:
        connection.send_result(msg["id"], {
            "success": False,
            "message": "Siren module is not enabled",
        })
        return

    if not siren_module.sirens and not siren_module.gateway_mac:
        connection.send_result(msg["id"], {
            "success": False,
            "message": "No siren entities configured",
        })
        return

    try:
        result = await siren_module.async_test()
        connection.send_result(msg["id"], result)
    except Exception as err:
        _LOGGER.error("Quick siren test failed: %s", err)
        connection.send_result(msg["id"], {
            "success": False,
            "message": str(err),
        })


#
# QUICK LIGHTS TEST
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/quick_test_lights",
})
@websocket_api.async_response
async def ws_quick_test_lights(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run a quick 2s emergency flash test on all configured lights."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_ready", "Coordinator not initialized")
        return

    lights_module = coordinator.modules.get("lights")
    if not lights_module or not lights_module.enabled:
        connection.send_result(msg["id"], {
            "success": False,
            "message": "Lights module is not enabled",
        })
        return

    if not lights_module.lights:
        connection.send_result(msg["id"], {
            "success": False,
            "message": "No lights configured",
        })
        return

    try:
        # Flash all lights red/blue for 2 seconds then restore
        tested = []
        for light in lights_module.lights:
            lights_module.backup_state(light)

        for color in ([255, 0, 0], [0, 0, 255], [255, 0, 0], [0, 0, 255]):
            await hass.services.async_call(
                "light", "turn_on",
                service_data={"brightness": 255, "rgb_color": color},
                target={"entity_id": lights_module.lights},
                blocking=True,
            )
            await asyncio.sleep(0.5)

        await hass.services.async_call(
            "light", "turn_off",
            target={"entity_id": lights_module.lights},
            blocking=True,
        )

        # Restore original states
        for light in lights_module.lights:
            backup = lights_module.get_backup_state(light)
            if backup:
                if backup["state"] == "on":
                    attrs = backup.get("attributes", {})
                    svc_data = {k: attrs[k] for k in ("brightness", "rgb_color", "color_temp") if k in attrs}
                    await hass.services.async_call(
                        "light", "turn_on",
                        service_data=svc_data or None,
                        target={"entity_id": light},
                        blocking=True,
                    )
                else:
                    await hass.services.async_call(
                        "light", "turn_off",
                        target={"entity_id": light},
                        blocking=True,
                    )
            tested.append(light)

        lights_module.clear_backup()

        connection.send_result(msg["id"], {
            "success": True,
            "message": "2s flash test completed",
            "details": {"lights_tested": tested},
        })
    except Exception as err:
        _LOGGER.error("Quick lights test failed: %s", err)
        lights_module.clear_backup()
        connection.send_result(msg["id"], {
            "success": False,
            "message": str(err),
        })


#
# SCHEDULED TESTS
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_scheduled_tests",
})
@websocket_api.async_response
async def ws_get_scheduled_tests(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all scheduled test configurations."""
    store = _get_store(hass)
    if not store:
        connection.send_result(msg["id"], {"scheduled_tests": {}})
        return
    connection.send_result(msg["id"], {"scheduled_tests": store.get_scheduled_tests()})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_scheduled_test",
    vol.Optional("test_id", default=""): str,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_scheduled_test(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save (create or update) a scheduled test."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    test_id = msg["test_id"] or None
    saved_id = await store.async_save_scheduled_test(test_id, msg["config"])
    connection.send_result(msg["id"], {"success": True, "test_id": saved_id})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_scheduled_test",
    vol.Required("test_id"): str,
})
@websocket_api.async_response
async def ws_delete_scheduled_test(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a scheduled test."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    success = await store.async_delete_scheduled_test(msg["test_id"])
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/run_scheduled_test_now",
    vol.Required("test_id"): str,
})
@websocket_api.async_response
async def ws_run_scheduled_test_now(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Run a scheduled test immediately (manual trigger)."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    sched = store.get_scheduled_tests().get(msg["test_id"])
    if not sched:
        connection.send_error(msg["id"], "not_found", "Scheduled test not found")
        return
    test_type = sched.get("test_type", "quick")
    result = await _run_test_internal(hass, test_type)
    overall = result.get("overall", "unknown")
    import time
    await store.async_update_scheduled_test_result(
        msg["test_id"], time.strftime("%Y-%m-%d %H:%M:%S"), overall
    )
    connection.send_result(msg["id"], {"success": True, "result": result})


#
# TEST RESULTS
#

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


#
# FAKE PRESENCE
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_fake_presence",
})
@websocket_api.async_response
async def ws_get_fake_presence(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get current fake presence state."""
    store = _get_store(hass)
    active = store.get_fake_presence() if store else False
    cameras = store.get_home_alone_cameras() if store else []
    connection.send_result(msg["id"], {
        "active": active,
        "home_alone_cameras": cameras,
    })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/set_fake_presence",
    vol.Required("active"): vol.Boolean(),
})
@websocket_api.async_response
async def ws_set_fake_presence(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Set fake presence state."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "not_found", "Coordinator not found")
        return

    await coordinator.async_set_fake_presence(msg["active"])
    connection.send_result(msg["id"], {"active": msg["active"]})


#
# HOME ALONE CAMERAS
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_home_alone_cameras",
})
@websocket_api.async_response
async def ws_get_home_alone_cameras(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get configured Home Alone Monitor cameras."""
    store = _get_store(hass)
    if not store:
        connection.send_result(msg["id"], {"cameras": []})
        return

    # Return entity IDs + friendly names for the panel to display
    cameras = []
    for entity_id in store.get_home_alone_cameras():
        state = hass.states.get(entity_id)
        cameras.append({
            "entity_id": entity_id,
            "name": state.attributes.get("friendly_name", entity_id) if state else entity_id,
        })
    connection.send_result(msg["id"], {"cameras": cameras})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_home_alone_cameras",
    vol.Required("cameras"): list,
})
@websocket_api.async_response
async def ws_save_home_alone_cameras(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save Home Alone Monitor camera selection."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "not_found", "Store not found")
        return

    # Accept list of entity_id strings or dicts with entity_id key
    cameras = []
    for item in msg["cameras"]:
        if isinstance(item, str):
            cameras.append(item)
        elif isinstance(item, dict) and item.get("entity_id"):
            cameras.append(item["entity_id"])

    await store.async_save_home_alone_cameras(cameras)
    _LOGGER.info("Home Alone cameras saved: %s", cameras)
    connection.send_result(msg["id"], {"cameras": cameras})


#
# FLOORPLAN (v1.5.0) -- Home Alone live-view
#
# The floorplan image lives on disk under custom_components/secure_me/floorplan/
# and is served via the panel's static-resource handler (registered in panel.py).
# The store holds image metadata + per-sensor markers; the bytes never go
# through the store. Upload comes in as base64 over websocket and is decoded,
# size-checked, PNG-validated, and written to disk.

# PNG signature for header validation (8 bytes per the PNG spec).
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _floorplan_paths(hass: HomeAssistant) -> tuple[str, str]:
    """Return (directory, file_path) for the floorplan image on disk."""
    root_dir = hass.config.path("custom_components", DOMAIN)
    floorplan_dir = os.path.join(root_dir, FLOORPLAN_DIR_NAME)
    floorplan_file = os.path.join(floorplan_dir, FLOORPLAN_IMAGE_NAME)
    return floorplan_dir, floorplan_file


def _read_png_dimensions(data: bytes) -> tuple[int, int] | None:
    """Return (width, height) from a PNG byte string, or None if invalid.

    Reads the IHDR chunk -- the first chunk after the 8-byte signature --
    which always starts at offset 8 with a 4-byte length, the 4-byte type
    'IHDR', then 4 bytes width and 4 bytes height (big-endian unsigned).
    """
    if len(data) < 24:
        return None
    if data[:8] != _PNG_SIGNATURE:
        return None
    if data[12:16] != b"IHDR":
        return None
    try:
        width, height = struct.unpack(">II", data[16:24])
    except struct.error:
        return None
    if width == 0 or height == 0:
        return None
    return width, height


def _normalise_markers(
    raw_markers: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Validate and clean a markers dict from the frontend.

    Each marker is keyed by entity_id and must have x_pct / y_pct in [0, 100].
    Unknown fields are dropped. Returns a fresh dict; never raises.
    """
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_markers, dict):
        return out

    for entity_id, cfg in raw_markers.items():
        if not isinstance(entity_id, str) or not entity_id:
            continue
        if not isinstance(cfg, dict):
            continue
        try:
            x = float(cfg.get(ATTR_MARKER_X_PCT, -1))
            y = float(cfg.get(ATTR_MARKER_Y_PCT, -1))
        except (TypeError, ValueError):
            continue
        if not (0.0 <= x <= 100.0) or not (0.0 <= y <= 100.0):
            continue

        kind = cfg.get(ATTR_MARKER_KIND) or "motion"
        if kind not in ("motion", "door", "window"):
            kind = "motion"

        label = cfg.get(ATTR_MARKER_LABEL)
        if label is not None and not isinstance(label, str):
            label = None

        out[entity_id] = {
            ATTR_MARKER_X_PCT: round(x, 2),
            ATTR_MARKER_Y_PCT: round(y, 2),
            ATTR_MARKER_LABEL: label,
            ATTR_MARKER_KIND: kind,
        }
    return out


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_floorplan",
})
@websocket_api.async_response
async def ws_get_floorplan(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the current floorplan config (image url + dimensions + markers).

    image_url is None when no floorplan has been uploaded yet.
    """
    store = _get_store(hass)
    if not store:
        connection.send_result(msg["id"], {
            ATTR_FLOORPLAN_IMAGE_URL: None,
            ATTR_FLOORPLAN_WIDTH: 0,
            ATTR_FLOORPLAN_HEIGHT: 0,
            ATTR_FLOORPLAN_MARKERS: {},
        })
        return

    fp = store.get_floorplan()

    # Self-heal: if the store thinks an image exists but the file is gone
    # (e.g. after a HACS update or manual deletion), report image_url=None
    # so the frontend falls back to the upload state.
    # IMPORTANT: only clear the image metadata -- rooms, openings, and sensor
    # assignments must survive a HACS update. Use async_clear_floorplan_image()
    # rather than async_delete_floorplan() to preserve room configuration.
    if fp.get(ATTR_FLOORPLAN_IMAGE_URL):
        _, floorplan_file = _floorplan_paths(hass)
        if not await hass.async_add_executor_job(os.path.isfile, floorplan_file):
            _LOGGER.info(
                "Floorplan image missing on disk (%s) -- attempting restore from backup",
                floorplan_file,
            )
            # Try to restore from base64 backup stored in the store.
            # This recovers the PNG automatically after a HACS update.
            restored = await store.async_restore_floorplan_image_from_backup(
                FLOORPLAN_URL_PATH
            )
            if restored:
                image_bytes, _w, _h = restored
                floorplan_dir, _ = _floorplan_paths(hass)

                def _write_restore() -> None:
                    os.makedirs(floorplan_dir, exist_ok=True)
                    tmp = floorplan_file + ".tmp"
                    with open(tmp, "wb") as fh:
                        fh.write(image_bytes)
                    os.replace(tmp, floorplan_file)

                try:
                    await hass.async_add_executor_job(_write_restore)
                    _LOGGER.info(
                        "Floorplan auto-restored from backup -- %d bytes written to %s",
                        len(image_bytes), floorplan_file,
                    )
                except OSError as err:
                    _LOGGER.warning(
                        "Floorplan restore write failed (%s) -- clearing image metadata only",
                        err,
                    )
                    await store.async_clear_floorplan_image()
            else:
                _LOGGER.info(
                    "No floorplan backup available -- clearing image metadata only"
                    " (rooms and openings preserved)",
                )
                await store.async_clear_floorplan_image()
            fp = store.get_floorplan()

    connection.send_result(msg["id"], fp)


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_floorplan_image",
    vol.Required("image_base64"): str,
})
@websocket_api.async_response
async def ws_save_floorplan_image(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Decode a base64-encoded PNG and write it to disk.

    Validates: max size (FLOORPLAN_MAX_BYTES), PNG signature + IHDR header.
    On success, persists the image URL + decoded width/height to the store.
    Existing markers are preserved (use save_floorplan_markers to clear them).
    """
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialised")
        return

    raw_b64 = msg["image_base64"]
    # Strip data-url prefix if the frontend sent the whole thing.
    if "," in raw_b64 and raw_b64.lstrip().startswith("data:"):
        raw_b64 = raw_b64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(raw_b64, validate=True)
    except (binascii.Error, ValueError) as err:
        connection.send_error(msg["id"], "invalid_base64", f"Could not decode image: {err}")
        return

    if len(image_bytes) > FLOORPLAN_MAX_BYTES:
        connection.send_error(
            msg["id"],
            "image_too_large",
            f"Floorplan image is {len(image_bytes)} bytes (max {FLOORPLAN_MAX_BYTES})",
        )
        return

    dimensions = _read_png_dimensions(image_bytes)
    if dimensions is None:
        connection.send_error(
            msg["id"],
            "invalid_png",
            "Uploaded data is not a valid PNG image",
        )
        return
    width, height = dimensions

    floorplan_dir, floorplan_file = _floorplan_paths(hass)

    def _write() -> None:
        os.makedirs(floorplan_dir, exist_ok=True)
        # Atomic-ish write: tmp file then rename so a half-written file
        # never gets served by the static handler.
        tmp_path = floorplan_file + ".tmp"
        with open(tmp_path, "wb") as fh:
            fh.write(image_bytes)
        os.replace(tmp_path, floorplan_file)

    try:
        await hass.async_add_executor_job(_write)
    except OSError as err:
        _LOGGER.error("Failed to write floorplan image to %s: %s", floorplan_file, err)
        connection.send_error(msg["id"], "write_failed", f"Could not write image: {err}")
        return

    await store.async_save_floorplan_image(FLOORPLAN_URL_PATH, width, height, image_b64=raw_b64)
    _LOGGER.info(
        "Floorplan image saved (%dx%d, %d bytes) -> %s",
        width, height, len(image_bytes), floorplan_file,
    )

    connection.send_result(msg["id"], {
        "success": True,
        ATTR_FLOORPLAN_IMAGE_URL: FLOORPLAN_URL_PATH,
        ATTR_FLOORPLAN_WIDTH: width,
        ATTR_FLOORPLAN_HEIGHT: height,
    })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_floorplan_markers",
    vol.Optional("markers"): dict,
    vol.Optional("rooms"): dict,
    vol.Optional("openings"): list,
})
@websocket_api.async_response
async def ws_save_floorplan_markers(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Replace the full floorplan data (rooms, openings, or legacy markers).

    v1.6.0: frontend sends { rooms: { room_id: { name, color, points, sensors } } }.
    v1.6.1: frontend also sends { openings: [ { type, label, points } ] }.
    v1.5.0 legacy: frontend sent { markers: { entity_id: { x_pct, y_pct, ... } } }.
    """
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialised")
        return

    if "rooms" in msg:
        # v1.6.0+ room-based format
        rooms = msg["rooms"]
        if not isinstance(rooms, dict):
            connection.send_error(msg["id"], "invalid_format", "rooms must be a dict")
            return
        openings = msg.get("openings")
        if openings is not None and not isinstance(openings, list):
            connection.send_error(msg["id"], "invalid_format", "openings must be a list")
            return
        await store.async_save_floorplan_rooms(rooms, openings)
        _LOGGER.debug(
            "Floorplan saved: %d rooms, %d openings",
            len(rooms),
            len(openings) if openings else 0,
        )
        connection.send_result(msg["id"], {"success": True, "rooms": rooms})
    else:
        # v1.5.0 legacy markers format
        cleaned = _normalise_markers(msg.get("markers"))
        await store.async_save_floorplan_markers(cleaned)
        _LOGGER.debug("Floorplan markers saved: %d markers", len(cleaned))
        connection.send_result(msg["id"], {
            "success": True,
            ATTR_FLOORPLAN_MARKERS: cleaned,
        })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_floorplan",
})
@websocket_api.async_response
async def ws_delete_floorplan(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete the floorplan image from disk and clear the store."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialised")
        return

    _, floorplan_file = _floorplan_paths(hass)

    def _unlink() -> bool:
        try:
            os.unlink(floorplan_file)
            return True
        except FileNotFoundError:
            return False
        except OSError as err:
            _LOGGER.warning("Could not delete floorplan file %s: %s", floorplan_file, err)
            return False

    removed = await hass.async_add_executor_job(_unlink)
    await store.async_delete_floorplan()
    _LOGGER.info("Floorplan deleted (file_removed=%s)", removed)
    connection.send_result(msg["id"], {"success": True, "file_removed": removed})


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
    """Remove environmental classification from a mis-classified sensor."""
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
# ARM / DISARM (used by secure-me-alarm-card for custom modes)
#

#
# ARM / DISARM via WebSocket (used by alarm card)
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_away",
    vol.Optional("code"): str,
    vol.Optional("force", default=False): bool,
})
@websocket_api.async_response
async def ws_arm_away(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in away mode via WebSocket.

    force=True skips the open-sensor check (bypass all open sensors).
    """
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    force = bool(msg.get("force", False))
    success = await coordinator.async_arm_away(code=code, force=force)
    bypassed = coordinator.bypassed_sensors if success and not force else []
    connection.send_result(msg["id"], {
        "success": success,
        "bypassed_sensors": bypassed,
    })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_home",
    vol.Optional("code"): str,
    vol.Optional("force", default=False): bool,
})
@websocket_api.async_response
async def ws_arm_home(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in home mode via WebSocket.

    force=True skips the open-sensor check (bypass all open sensors).
    """
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    force = bool(msg.get("force", False))
    success = await coordinator.async_arm_home(code=code, force=force)
    bypassed = coordinator.bypassed_sensors if success and not force else []
    connection.send_result(msg["id"], {
        "success": success,
        "bypassed_sensors": bypassed,
    })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_night",
    vol.Optional("code"): str,
})
@websocket_api.async_response
async def ws_arm_night(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in night mode via WebSocket."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    success = await coordinator.async_arm_night(code=code)
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_vacation",
    vol.Optional("code"): str,
})
@websocket_api.async_response
async def ws_arm_vacation(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in vacation mode via WebSocket."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    success = await coordinator.async_arm_vacation(code=code)
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_home_alone",
    vol.Optional("code"): str,
})
@websocket_api.async_response
async def ws_arm_home_alone(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in home alone mode via WebSocket."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    success = await coordinator.async_arm_home_alone(code=code)
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/disarm",
    vol.Optional("code"): str,
})
@websocket_api.async_response
async def ws_disarm(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Disarm via WebSocket."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    success = await coordinator.async_disarm(code=code)
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/skip_delay",
})
@websocket_api.async_response
async def ws_skip_delay(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Skip active exit/entry countdown via WebSocket (v1.4.3).

    Returns success=True if a countdown was skipped, False if there was
    no active countdown to skip.
    """
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    success = await coordinator.async_skip_delay()
    connection.send_result(msg["id"], {"success": success})


#
# SPEAKER PROFILES (v1.4.0)
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_speaker_profiles",
})
@websocket_api.async_response
async def ws_get_speaker_profiles(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all speaker profiles."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    profiles = store.get_speaker_profiles()
    # Enrich with current media_player state
    enriched = []
    for p in profiles:
        eid = p.get("entity_id", "")
        state = hass.states.get(eid)
        enriched.append({
            **p,
            "available": state is not None and state.state not in ("unavailable", "unknown"),
            "current_volume": state.attributes.get("volume_level") if state else None,
        })
    connection.send_result(msg["id"], {"profiles": enriched})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_speaker_profiles",
    vol.Required("profiles"): list,
})
@websocket_api.async_response
async def ws_save_speaker_profiles(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save speaker profiles and reload TTS module config."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    profiles = msg["profiles"]
    # Validate each profile has required fields
    for p in profiles:
        if not p.get("entity_id"):
            connection.send_error(msg["id"], "invalid_profile", "Each profile needs entity_id")
            return
        p.setdefault("name", p["entity_id"])
        p.setdefault("volume", 0.5)
        p.setdefault("tts_service", "tts.cloud_say")
        p.setdefault("tts_entity", "tts.home_assistant_cloud")

    await store.async_save_speaker_profiles(profiles)

    # Reload TTS module config so it picks up new profiles immediately
    coordinator = _get_coordinator(hass)
    if coordinator:
        tts = coordinator.modules.get("tts")
        if tts:
            tts._speaker_profiles = profiles
            _LOGGER.debug("TTS speaker profiles reloaded: %d profiles", len(profiles))

    connection.send_result(msg["id"], {"success": True, "count": len(profiles)})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_home_alone_messages",
})
@websocket_api.async_response
async def ws_get_home_alone_messages(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get Home Alone quick messages for the alarm card.

    Returns notifications with trigger=home_alone_action, formatted for
    the alarm card's quick-message buttons. Each message includes speaker
    preferences so the card can target the right speakers.
    """
    store = _get_store(hass)
    if not store:
        connection.send_result(msg["id"], {"messages": []})
        return

    messages = []
    for notif in store.get_notifications().values():
        if not notif.get("enabled", True):
            continue
        if notif.get("trigger") != "home_alone_action":
            continue
        messages.append({
            "label": notif.get("name", ""),
            "message": notif.get("message", ""),
            "speakers": notif.get("tts_speakers", []),
        })

    connection.send_result(msg["id"], {"messages": messages})


#
# AUTO ACTIONS v2
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_auto_actions",
})
@websocket_api.async_response
async def ws_get_auto_actions(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get Auto Actions v2 configuration."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    connection.send_result(msg["id"], {"config": store.get_auto_actions()})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_auto_actions",
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_auto_actions(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save Auto Actions v2 configuration."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    await store.async_save_auto_actions(msg["config"])
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_fake_presence_v2",
})
@websocket_api.async_response
async def ws_get_fake_presence_v2(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get Fake Presence v2 configuration dict."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    connection.send_result(msg["id"], {"config": store.get_fake_presence_v2()})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_fake_presence_v2",
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_fake_presence_v2(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save Fake Presence v2 configuration dict."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    await store.async_save_fake_presence_v2(msg["config"])

    # Keep coordinator in sync via the proper async method
    coordinator = _get_coordinator(hass)
    if coordinator:
        await coordinator.async_set_fake_presence(msg["config"].get("active", False))

    connection.send_result(msg["id"], {"success": True, "config": store.get_fake_presence_v2()})