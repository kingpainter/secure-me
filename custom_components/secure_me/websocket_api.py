"""WebSocket API for Secure Me panel."""
# VERSION = "1.2.0"

import asyncio
import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .notification_dispatcher import async_setup_dispatcher

_LOGGER = logging.getLogger(__name__)


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register all websocket commands and start the notification dispatcher."""
    websocket_api.async_register_command(hass, ws_get_sensors)
    websocket_api.async_register_command(hass, ws_save_sensors)
    websocket_api.async_register_command(hass, ws_hide_sensor)
    websocket_api.async_register_command(hass, ws_unmark_environmental)
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
    websocket_api.async_register_command(hass, ws_get_test_results)
    websocket_api.async_register_command(hass, ws_get_fake_presence)
    websocket_api.async_register_command(hass, ws_set_fake_presence)
    websocket_api.async_register_command(hass, ws_get_home_alone_cameras)
    websocket_api.async_register_command(hass, ws_save_home_alone_cameras)

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
    # Do NOT pass code_hashed=True from frontend — let store manage it
    config = dict(msg["config"])
    config.pop("code_hashed", None)  # strip any frontend-supplied flag
    await store.async_save_user(user_id, config)
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

    # --- All other triggers: send only to admin users ---
    try:
        title = f"TEST: {notif.get('name', 'Secure Me Test')}"
        context_map = {
            "state": "test", "armed_by": "Test", "disarmed_by": "Test",
            "triggered_by": "Test", "sensor_list": "Test sensor", "count": "1",
        }
        from .notification_dispatcher import _build_message, _send_push
        message = _build_message(notif.get("message", "Test notification from Secure Me"), context_map)

        # Route to admin users only
        admin_services = [
            u.get("notify_service")
            for u in store.get_users().values()
            if u.get("enabled", True) and u.get("admin") and u.get("notify_service")
        ]

        # Fallback: use notification's own service if no admins configured
        if not admin_services:
            admin_services = [notif.get("service", "notify.notify")]

        for svc in admin_services:
            await _send_push(hass, svc, title, message)

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
})
@websocket_api.async_response
async def ws_test_tts(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Test TTS by playing a message immediately via the TTS module."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return

    tts_module = coordinator.modules.get("tts")
    if not tts_module or not tts_module.enabled:
        connection.send_error(msg["id"], "tts_not_enabled", "TTS module is not enabled")
        return

    # Respects admin quiet hours for TTS test
    try:
        from .notification_dispatcher import _is_tts_quiet_now
        store = _get_store(hass)
        admins = [
            u for u in (store.get_users().values() if store else [])
            if u.get("enabled", True) and u.get("admin")
        ]
        # Only suppress if ALL admins are in quiet hours — otherwise play
        if admins and all(_is_tts_quiet_now(u) for u in admins):
            connection.send_result(msg["id"], {"success": False, "error": "TTS quiet hours active for all admins"})
            return
        await tts_module.announce_system(msg["message"])
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
        # lights: [{entity_id, ...}] -> lights: [str]
        normalized["lights"] = extract_ids(config.get("lights", []))

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

    elif module_id == "siren":
        normalized["lights"] = extract_ids(config.get("lights", []))

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

    # --- Battery discovery (standard + full) ---
    if test_type in ("standard", "full"):
        batteries = _discover_batteries(hass)
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

    # --- Persist to test history ---
    if store:
        test_history = store._data.get("test_history", [])
        test_history.insert(0, results)
        store._data["test_history"] = test_history[:10]
        await store.async_save()

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
