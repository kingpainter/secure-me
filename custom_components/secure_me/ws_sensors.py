"""WebSocket API — Sensor, Zone and User commands for Secure Me."""

# VERSION = "2.2.0"
from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

from .ws_helpers import _get_coordinator, _get_store

# SENSOR GROUPS (anti-masking) — v1.2.0
#


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_sensor_groups",
    }
)
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_sensor_group",
        vol.Optional("group_id"): str,
        vol.Required("config"): dict,
    }
)
@websocket_api.require_admin
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
    group_id = await store.async_save_sensor_group(msg.get("group_id"), msg["config"])
    # Reload sensor groups into active zone manager
    coordinator = _get_coordinator(hass)
    if coordinator:
        coordinator.zone_manager.load_sensor_groups(store.get_sensor_groups())
    connection.send_result(msg["id"], {"success": True, "group_id": group_id})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_sensor_group",
        vol.Required("group_id"): str,
    }
)
@websocket_api.require_admin
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_alarm_state",
    }
)
@websocket_api.async_response
async def ws_get_alarm_state(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get current alarm state."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_result(
            msg["id"],
            {
                "state": "unknown",
                "countdown": 0,
            },
        )
        return

    connection.send_result(
        msg["id"],
        {
            "state": coordinator.alarm_state,
            "countdown": coordinator.delay_countdown,
            "armed_by": coordinator.armed_by,
            "disarmed_by": coordinator.disarmed_by,
            "open_sensors": coordinator.open_sensors,
        },
    )


#
# SENSORS
#


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_sensors",
    }
)
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_sensors",
        vol.Required("sensors"): dict,
    }
)
@websocket_api.require_admin
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
        # Fix 3 (secure_me_implementering.md): a saved sensor set can add or
        # remove configured entities, which changes the battery-list scope --
        # without this, a newly added sensor's battery wouldn't show up for
        # up to 5 minutes (the cache TTL).
        coordinator.invalidate_battery_cache()

    connection.send_result(msg["id"], {"success": True})


#
# ZONES
#


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_zones",
    }
)
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_zone",
        vol.Required("zone_id"): str,
        vol.Required("config"): dict,
    }
)
@websocket_api.require_admin
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
    # Fix (2026-08-27): the panel has always sent the zone type under the
    # key "type", but every backend reader expects "zone_type". Normalize on
    # save so newly-saved/edited zones store the canonical key going forward
    # -- the read-side fallback in coordinator.py/ws_sensors.py still covers
    # zones that were saved before this fix and never get re-edited.
    if "zone_type" not in config and "type" in config:
        config["zone_type"] = config["type"]
    await store.async_save_zone(msg["zone_id"], config)

    # Sync with zone manager — reload all zones so arm_modes take effect
    coordinator = _get_coordinator(hass)
    if coordinator and hasattr(coordinator, "zone_manager"):
        _reload_zones_into_coordinator(coordinator, store)
        _LOGGER.info("Zone %s saved and reloaded into zone manager", msg["zone_id"])
        # Fix 3: zone sensor membership can change here too.
        coordinator.invalidate_battery_cache()

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
            # See matching comment in coordinator.py's async_load_store_config():
            # the panel has always saved the zone type under "type", not
            # "zone_type" -- fall back to the legacy key so Instant/Perimeter/
            # Interior zones behave correctly instead of silently acting as
            # "entry" (delayed) zones.
            zone_type=zone_cfg.get("zone_type") or zone_cfg.get("type", "entry"),
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_zone",
        vol.Required("zone_id"): str,
    }
)
@websocket_api.require_admin
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
            # Fix 3: deleting a zone can remove sensors from the configured set.
            coordinator.invalidate_battery_cache()

    connection.send_result(msg["id"], {"success": success})


#
# USERS
#


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_users",
    }
)
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


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save_user",
        vol.Required("user_id"): str,
        vol.Required("config"): dict,
    }
)
@websocket_api.require_admin
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

    # Refresh Auto Actions v2's tracked-user set so person_entity edits take
    # effect without requiring a Home Assistant restart. (v1.5.4: replaces
    # the old presence-monitor refresh call, now that PresenceMonitor has
    # been removed and Auto Actions v2 is the sole presence-based system.)
    coordinator = _get_coordinator(hass)
    if (
        coordinator is not None
        and getattr(coordinator, "_auto_actions_manager", None) is not None
    ):
        coordinator._auto_actions_manager.async_refresh_trackers()

    connection.send_result(msg["id"], {"success": True, "user_id": user_id})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_user",
        vol.Required("user_id"): str,
    }
)
@websocket_api.require_admin
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

    # Refresh Auto Actions v2's tracked-user set so removed users' trackers
    # are unsubscribed without requiring a Home Assistant restart. (v1.5.4:
    # replaces the old presence-monitor refresh call.)
    if success:
        coordinator = _get_coordinator(hass)
        if (
            coordinator is not None
            and getattr(coordinator, "_auto_actions_manager", None) is not None
        ):
            coordinator._auto_actions_manager.async_refresh_trackers()

    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_nfc_tags",
    }
)
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_nfc_tags",
    }
)
@websocket_api.async_response
async def ws_get_nfc_tags(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get registered NFC tags for current user."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    tags = store.get_nfc_tags()
    connection.send_result(msg["id"], {"nfc_tags": tags})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/register_nfc_tag",
        vol.Required("tag_id"): str,
        vol.Required("user_id"): str,
        vol.Required("action"): vol.In(["disarm", "arm_away"]),
        vol.Required("name"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_register_nfc_tag(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Register a new NFC tag."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    tag_id = msg["tag_id"]
    user_id = msg["user_id"]
    action = msg["action"]
    name = msg["name"]
    requires_pin = msg.get("requires_pin", False)

    await store.async_save_nfc_tag(tag_id, user_id, action, name, requires_pin)
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_nfc_tag",
        vol.Required("tag_id"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_delete_nfc_tag(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a registered NFC tag."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    tag_id = msg["tag_id"]
    await store.async_delete_nfc_tag(tag_id)
    connection.send_result(msg["id"], {"success": True})




@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_ha_nfc_tags",
    }
)
@websocket_api.async_response
async def ws_get_ha_nfc_tags(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get available NFC tags from Home Assistant."""
    import json
    from pathlib import Path
    
    tag_ids = []
    tag_registry = None

    # Method 1: Try to get from hass.data (if tag component is loaded)
    for key in ["tag_registry", "tag", "tags"]:
        potential_registry = hass.data.get(key)
        if potential_registry:
            tag_registry = potential_registry
            break

    # Method 2: Check if tag component is loaded and has registry
    if not tag_registry:
        try:
            tag_component = hass.components.tag
            if hasattr(tag_component, "registry"):
                tag_registry = tag_component.registry
        except (AttributeError, ImportError):
            pass

    # Extract from in-memory registry if found
    if tag_registry:
        if hasattr(tag_registry, "tags"):
            try:
                if isinstance(tag_registry.tags, dict):
                    tag_ids = [tag.id for tag in tag_registry.tags.values()]
                elif hasattr(tag_registry.tags, "__iter__"):
                    tag_ids = [tag.id if hasattr(tag, "id") else tag for tag in tag_registry.tags]
            except (AttributeError, TypeError):
                pass
        elif isinstance(tag_registry, dict):
            tag_ids = list(tag_registry.keys())

    # Method 3: Fallback - read directly from .storage/tag file
    if not tag_ids:
        try:
            storage_path = Path(hass.config.path(".storage/tag"))
            if storage_path.exists():
                with open(storage_path, "r", encoding="utf-8") as f:
                    storage_data = json.load(f)
                    # Navigate the storage structure to find tags
                    # Structure: { "data": { "items": [ { "id": "...", "name": "...", ... }, ... ] } }
                    if "data" in storage_data and "items" in storage_data["data"]:
                        items = storage_data["data"]["items"]
                        if isinstance(items, list):
                            # Extract IDs from list of tag objects
                            tag_ids = [item.get("id") for item in items if isinstance(item, dict) and "id" in item]
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, Exception):
            pass

    connection.send_result(msg["id"], tag_ids)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/import_nfc_tag",
        vol.Required("tag_id"): str,
        vol.Required("action"): str,
        vol.Optional("name"): str,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_import_nfc_tag(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Import an NFC tag from Home Assistant into Secure Me."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    tag_id = msg.get("tag_id")
    action = msg.get("action")
    name = msg.get("name", tag_id)
    requires_pin = msg.get("requires_pin", False)

    if not tag_id or not action:
        connection.send_error(msg["id"], "invalid_params", "Missing tag_id or action")
        return

    # Save the imported tag without assigning to a specific user yet
    try:
        await store.async_save_nfc_tag(tag_id, None, action, name, requires_pin)
        coordinator = _get_coordinator(hass)
        if coordinator:
            coordinator.invalidate_battery_cache()
        connection.send_result(msg["id"], {"success": True})
    except Exception as e:
        _LOGGER.error(f"Error importing NFC tag: {e}")
        connection.send_error(msg["id"], "import_failed", str(e))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_persons",
    }
)
@websocket_api.async_response
async def ws_get_persons(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all person entities from HA for user-tracker binding."""
    persons = []
    for state in hass.states.async_all("person"):
        persons.append(
            {
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "state": state.state,
            }
        )
    connection.send_result(msg["id"], {"persons": persons})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/hide_sensor",
        vol.Required("entity_id"): str,
        vol.Optional("hidden", default=True): bool,
    }
)
@websocket_api.require_admin
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
        sensors[entity_id] = {
            **sensors.get(entity_id, {}),
            "excluded": True,
            "enabled": False,
        }
    else:
        cfg = dict(sensors.get(entity_id, {}))
        cfg.pop("excluded", None)
        sensors[entity_id] = cfg
    await store.async_save_sensors_bulk(sensors)
    # Fix 3: hiding/unhiding a sensor changes the configured-entity set.
    coordinator = _get_coordinator(hass)
    if coordinator:
        coordinator.invalidate_battery_cache()
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/unmark_environmental",
        vol.Required("entity_id"): str,
    }
)
@websocket_api.require_admin
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
    # Fix 3: this also excludes the sensor, changing the configured-entity set.
    coordinator = _get_coordinator(hass)
    if coordinator:
        coordinator.invalidate_battery_cache()
    connection.send_result(msg["id"], {"success": True})


#
# MODULES
#
