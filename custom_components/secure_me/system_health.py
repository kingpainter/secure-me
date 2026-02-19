# VERSION = "0.3.3"
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

    # Check module health
    unhealthy_modules = []
    for module_id, module in modules.items():
        if module.enabled and not module.is_healthy:
            unhealthy_modules.append(module_id)

    if unhealthy_modules:
        health_info["unhealthy_modules"] = ", ".join(unhealthy_modules)
    else:
        health_info["all_modules_healthy"] = "yes"

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

    # Last test result
    test_data = coordinator.store.get("test_results", {})
    if test_data:
        last_result = test_data.get("last_result", {})
        health_info["last_test_status"] = last_result.get("status", "unknown")
        health_info["last_test_time"] = last_result.get("timestamp", "never")

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
