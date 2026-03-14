# VERSION = "1.0.0"
"""System health integration for Secure Me."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, MODULE_TTS

_LOGGER = logging.getLogger(__name__)


@callback
def async_register(
    hass: HomeAssistant,
    register: system_health.SystemHealthRegistration,
) -> None:
    """Register system health callbacks."""
    register.async_register_info(async_system_health_info)


async def async_system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get system health info for Secure Me."""
    health_info: dict[str, Any] = {}

    # Get coordinator from first config entry
    config_entries = hass.config_entries.async_entries(DOMAIN)
    if not config_entries:
        return {
            "integration_status": "not_configured",
            "error": "No config entries found",
        }

    entry = config_entries[0]
    # F6 Fix: coordinator is stored nested under entry_id with "coordinator" key
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    if isinstance(entry_data, dict):
        coordinator = entry_data.get("coordinator")
    else:
        # Fallback: entry_data might be the coordinator directly
        coordinator = entry_data if hasattr(entry_data, "modules") else None

    if not coordinator:
        return {
            "integration_status": "error",
            "error": "Coordinator not initialized",
        }

    # Basic status
    health_info["integration_status"] = "ok" if coordinator.last_update_success else "degraded"
    health_info["version"] = entry.data.get("version", "unknown")

    # Entity counts
    entity_registry = hass.helpers.entity_registry.async_get(hass)
    entities = [
        e for e in entity_registry.entities.values()
        if e.config_entry_id == entry.entry_id
    ]
    health_info["total_entities"] = len(entities)
    health_info["enabled_entities"] = len([e for e in entities if not e.disabled])

    # Module health (coordinator.modules is the direct dict, no module_manager needed)
    modules = coordinator.modules
    enabled_modules = [m for m in modules.values() if m.enabled]
    health_info["modules_enabled"] = len(enabled_modules)
    health_info["modules_total"] = len(modules)

    # Check module health — split by severity
    MODULE_SEVERITY = {
        "siren": "critical", "lock": "critical",
        "camera": "high",
        "lights": "medium", "climate": "low", "tts": "low",
    }
    critical_unhealthy = []
    high_unhealthy = []
    low_unhealthy = []

    for module_id, module in modules.items():
        if module.enabled and not module.is_healthy:
            sev = MODULE_SEVERITY.get(module_id, "medium")
            if sev == "critical":
                critical_unhealthy.append(module_id)
            elif sev == "high":
                high_unhealthy.append(module_id)
            else:
                low_unhealthy.append(module_id)

    if critical_unhealthy:
        health_info["critical_modules_offline"] = ", ".join(critical_unhealthy)
    if high_unhealthy:
        health_info["high_modules_offline"] = ", ".join(high_unhealthy)
    if low_unhealthy:
        health_info["low_modules_offline"] = ", ".join(low_unhealthy)
    if not critical_unhealthy and not high_unhealthy and not low_unhealthy:
        health_info["all_modules_healthy"] = "yes"

    # Overall module status for quick at-a-glance
    if critical_unhealthy:
        health_info["module_status"] = f"CRITICAL: {', '.join(critical_unhealthy)} offline"
    elif high_unhealthy:
        health_info["module_status"] = f"WARNING: {', '.join(high_unhealthy)} offline"
    elif low_unhealthy:
        health_info["module_status"] = f"minor: {', '.join(low_unhealthy)} offline"
    else:
        health_info["module_status"] = "ok"

    # F6 Fix: TTS module specific health check
    tts_module = modules.get(MODULE_TTS)
    if tts_module and tts_module.enabled:
        health_info["tts_module_status"] = "enabled"
        media_players = getattr(tts_module, "media_players", [])
        health_info["tts_media_players"] = len(media_players) if isinstance(media_players, list) else 0
    elif tts_module:
        health_info["tts_module_status"] = "disabled"

    # Zone info
    zones = coordinator.store.get_zones()
    health_info["zones_configured"] = len(zones)
    health_info["zones_enabled"] = len([z for z in zones if z.get("enabled", True)])

    # User info
    users = coordinator.store.get_users()
    health_info["users_configured"] = len(users)

    # Battery tracking
    battery_sensors = [
        e for e in entities
        if e.domain == "sensor" and "battery" in e.original_name.lower()
    ]
    health_info["battery_sensors"] = len(battery_sensors)

    # Last test result — stored under test_history in _data
    import datetime
    test_history = coordinator.store._data.get("test_history", [])
    if test_history:
        last = test_history[0]
        health_info["last_test_overall"] = last.get("overall", "unknown")
        health_info["last_test_type"] = last.get("test_type", "unknown")
        health_info["last_test_time"] = last.get("timestamp", "never")
        health_info["last_test_duration"] = f"{last.get('duration_seconds', 0)}s"
        # Days since last test
        ts_str = last.get("timestamp", "")
        if ts_str:
            try:
                ts = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                days = (datetime.datetime.now() - ts).days
                health_info["days_since_last_test"] = days
                if days > 30:
                    health_info["test_status_warning"] = f"No test in {days} days — strongly recommended"
                elif days > 7:
                    health_info["test_status_warning"] = f"No test in {days} days — recommended weekly"
            except Exception:
                pass
        # Critical fails from last test
        summary = last.get("summary", {})
        critical = summary.get("critical_fails", [])
        if critical:
            health_info["last_test_critical_fails"] = ", ".join(critical)
    else:
        health_info["last_test_overall"] = "never_run"
        health_info["test_status_warning"] = "System has never been tested — run a test from the panel"

    # Store functionality
    try:
        test_write = await coordinator.store.async_save()
        health_info["store_writable"] = "yes" if test_write else "no"
    except Exception as err:
        health_info["store_writable"] = f"error: {err}"

    # WebSocket API
    websocket_commands = hass.data.get(f"{DOMAIN}_websocket_commands", [])
    health_info["websocket_commands_registered"] = len(websocket_commands)

    return health_info
