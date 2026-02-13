"""Diagnostics support for Secure Me."""
# VERSION = "0.3.0"

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
    in Settings → Devices & Services → Secure Me → 3-dot menu.
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
        "modules": modules_info,
        "health": health_info,
        "store": store_info,
        "batteries": battery_info,
        "zones": zone_info,
    }
