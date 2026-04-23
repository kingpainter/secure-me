"""System health for Secure Me."""
# VERSION = "1.4.2"

import logging
from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant

from .const import DOMAIN, COORDINATOR

_LOGGER = logging.getLogger(__name__)


def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks.

    Must be a plain (non-async) function — HA's system_health platform
    calls this synchronously via platform.async_register().
    """
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get info for the system health."""
    info: dict[str, Any] = {}

    try:
        domain_data = hass.data.get(DOMAIN, {})

        # Find coordinator
        coordinator = None
        for key, value in domain_data.items():
            if isinstance(value, dict) and COORDINATOR in value:
                coordinator = value[COORDINATOR]
                break

        if coordinator is None:
            return {
                "integration_loaded": False,
                "error": "Coordinator not found",
            }

        # Basic info
        info["integration_loaded"] = True
        info["alarm_state"] = coordinator.alarm_state

        # Module health
        module_health = coordinator.get_module_health()
        enabled_count = sum(1 for m in module_health.values() if m.get("enabled"))
        healthy_count = sum(
            1 for m in module_health.values()
            if m.get("enabled") and m.get("status") == "ok"
        )
        info["modules_enabled"] = enabled_count
        info["modules_healthy"] = healthy_count

        # Health score
        info["health_score"] = coordinator.get_health_score()

        # Zone count
        store = domain_data.get("store")
        if store:
            zones = store.get_zones()
            info["zones_configured"] = len(zones)
            enabled_zones = sum(1 for z in zones.values() if z.get("enabled", True))
            info["zones_enabled"] = enabled_zones

        # Fake presence
        info["fake_presence_active"] = coordinator.fake_presence

    except Exception as err:
        _LOGGER.error("Error getting system health info: %s", err)
        info["error"] = str(err)

    return info
