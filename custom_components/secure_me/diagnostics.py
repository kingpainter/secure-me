"""Diagnostics support for Secure Me."""
# VERSION = "1.4.0"

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CODE,
    COORDINATOR,
    DOMAIN,
    MODULE_CAMERA,
    MODULE_CLIMATE,
    MODULE_LIGHTS,
    MODULE_LOCK,
    MODULE_SIREN,
    MODULE_TTS,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

# Keys to redact from diagnostics output
TO_REDACT = {
    CONF_CODE,
    "code",
    "pin",
    "password",
    "nfc_tag_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    This is shown when the user clicks "Download diagnostics"
    in Settings -> Devices & Services -> Secure Me -> 3-dot menu.
    """
    entry_data = hass.data.get(DOMAIN, {}).get(config_entry.entry_id, {})
    coordinator = entry_data.get(COORDINATOR)
    store = hass.data.get(DOMAIN, {}).get("store")

    # --- Config entry info (redacted) ---
    config_data = async_redact_data(dict(config_entry.data), TO_REDACT)
    options_data = async_redact_data(dict(config_entry.options), TO_REDACT)

    # --- Coordinator state ---
    coordinator_info: dict[str, Any] = {"available": False}
    if coordinator:
        coordinator_info = {
            "available": True,
            "alarm_state": coordinator.alarm_state,
            "countdown": coordinator.delay_countdown,
            "exit_delay": coordinator.exit_delay,
            "entry_delay": coordinator.entry_delay,
            "armed_by": coordinator.armed_by,
            "disarmed_by": coordinator.disarmed_by,
            "triggered_by": coordinator.triggered_by,
            "open_sensors_count": len(coordinator.open_sensors),
            "bypassed_zones": coordinator.bypassed_zones,
        }

    # --- Module status ---
    modules_info: dict[str, Any] = {}
    if coordinator:
        for mod_id, module in coordinator.modules.items():
            modules_info[mod_id] = {
                "enabled": module.enabled,
                "module_name": module.module_name,
                "config_keys": list(module.config.keys()) if module.config else [],
            }

    # --- Module health ---
    health_info: dict[str, Any] = {}
    if coordinator:
        health_info = {
            "health_score": coordinator.get_health_score(),
            "module_health": coordinator.get_module_health(),
            "enabled_module_count": coordinator.get_enabled_module_count(),
        }

    # --- Store summary (redacted) ---
    store_info: dict[str, Any] = {"available": False}
    if store:
        store_data = store._data
        store_info = {
            "available": True,
            "sensor_count": len(store_data.get("sensors", {})),
            "zone_count": len(store_data.get("zones", {})),
            "user_count": len(store_data.get("users", {})),
            "notification_count": len(store_data.get("notifications", {})),
            "automation_count": len(store_data.get("automations", {})),
            "module_configs": {
                mod_id: {"enabled": mod_cfg.get("enabled", False)}
                for mod_id, mod_cfg in store_data.get("modules", {}).items()
            },
            "test_history_count": len(store_data.get("test_history", [])),
        }

    # --- Battery summary ---
    battery_info: dict[str, Any] = {}
    battery_count = 0
    low_count = 0
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != "battery":
            continue
        battery_count += 1
        try:
            level = int(float(state.state))
            if level < 20:
                low_count += 1
        except (ValueError, TypeError):
            pass
    battery_info = {
        "total_battery_sensors": battery_count,
        "low_batteries": low_count,
    }

    # --- Zone info from zone_manager ---
    zone_info: dict[str, Any] = {}
    if coordinator:
        zone_mgr = coordinator.zone_manager
        zone_info = {
            "total_zones": len(zone_mgr.zones) if hasattr(zone_mgr, "zones") else 0,
            "monitoring_active": bool(
                zone_mgr._unsubscribe_callbacks
                if hasattr(zone_mgr, "_unsubscribe_callbacks")
                else False
            ),
            "triggered_zones": len(zone_mgr.get_triggered_zones()),
            "all_open_sensors": zone_mgr.get_all_open_sensors(),
        }

    # --- Performance Metrics (NEW) ---
    performance_info: dict[str, Any] = {}
    if coordinator:
        performance_info = {
            "last_update_success": coordinator.last_update_success,
            "last_update_success_time": (
                coordinator.last_update_success_time.isoformat()
                if coordinator.last_update_success_time
                else None
            ),
            "update_interval": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
        }

    # --- Recent Test Results (NEW) ---
    test_results_info: dict[str, Any] = {}
    if store:
        test_data = store.get("test_results", {})
        if test_data:
            last_result = test_data.get("last_result", {})
            test_results_info = {
                "last_test_status": last_result.get("status", "unknown"),
                "last_test_time": last_result.get("timestamp", "never"),
                "last_test_level": last_result.get("level", "unknown"),
                "last_test_duration": last_result.get("duration", 0),
                "test_history_available": len(store._data.get("test_history", [])),
            }
            
            # Include last test details if available
            if last_result:
                test_results_info["last_test_details"] = {
                    "passed_checks": last_result.get("passed_checks", 0),
                    "total_checks": last_result.get("total_checks", 0),
                    "failed_modules": last_result.get("failed_modules", []),
                }

    # --- Entity Registry Info (NEW) ---
    entity_info: dict[str, Any] = {}
    entity_registry = hass.helpers.entity_registry.async_get(hass)
    entities = [
        e
        for e in entity_registry.entities.values()
        if e.config_entry_id == config_entry.entry_id
    ]
    
    entities_by_platform: dict[str, list[str]] = {}
    disabled_entities: list[str] = []
    
    for entity in entities:
        platform = entity.domain
        if platform not in entities_by_platform:
            entities_by_platform[platform] = []
        entities_by_platform[platform].append(entity.entity_id)
        
        if entity.disabled:
            disabled_entities.append(entity.entity_id)
    
    entity_info = {
        "total_entities": len(entities),
        "enabled_entities": len(entities) - len(disabled_entities),
        "disabled_entities": len(disabled_entities),
        "entities_by_platform": {
            platform: len(entity_list)
            for platform, entity_list in entities_by_platform.items()
        },
        "disabled_entity_list": disabled_entities,
    }

    # --- WebSocket API Status (NEW) ---
    websocket_info: dict[str, Any] = {}
    websocket_commands = hass.data.get(f"{DOMAIN}_websocket_commands", [])
    websocket_info = {
        "commands_registered": len(websocket_commands),
        "command_list": websocket_commands,
    }

    # --- User Configuration (NEW) ---
    users_info: dict[str, Any] = {}
    if store:
        users = store.get_users()
        users_info = {
            "total_users": len(users),
            "user_names": [u.get("name", "Unknown") for u in users],
        }

    # --- Zone Details (NEW) ---
    zones_detail: list[dict[str, Any]] = []
    if store:
        zones = store.get_zones()
        for zone in zones:
            zone_detail = {
                "id": zone.get("id"),
                "name": zone.get("name", "Unknown"),
                "enabled": zone.get("enabled", True),
                "zone_type": zone.get("zone_type", "unknown"),
                "sensor_count": len(zone.get("sensors", [])),
            }
            zones_detail.append(zone_detail)

    return {
        "integration_version": VERSION,
        "config_entry": {
            "entry_id": config_entry.entry_id,
            "title": config_entry.title,
            "data": config_data,
            "options": options_data,
            "source": config_entry.source,
        },
        "coordinator": coordinator_info,
        "performance": performance_info,  # NEW
        "modules": modules_info,
        "health": health_info,
        "store": store_info,
        "batteries": battery_info,
        "zones": zone_info,
        "zones_detail": zones_detail,  # NEW
        "test_results": test_results_info,  # NEW
        "entities": entity_info,  # NEW
        "websocket": websocket_info,  # NEW
        "users": users_info,  # NEW
    }
