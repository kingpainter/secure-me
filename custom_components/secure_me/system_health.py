"""System health for Secure Me."""
# VERSION = "1.5.5"

import logging
from typing import Any

from homeassistant.components import system_health
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, COORDINATOR

_LOGGER = logging.getLogger(__name__)


@callback
def async_register(
    hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register system health callbacks.

    v1.4.2: Must be decorated with @callback. Without it, HA's platform
    loader inspects the 'async_' prefix and treats the function as a
    coroutine, triggering 'RuntimeWarning: coroutine async_register was
    never awaited' at startup.
    """
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Get comprehensive info for the HA System Health panel.

    Shown in Settings -> System -> System Health -> Secure Me.
    Extended in v1.5.0:
    - sensor + zone counts
    - zone monitoring active flag (verifies sensors are watched)
    - last_triggered timestamp (survives restarts via RestoreEntity)
    - bypassed_sensors count at last arm
    - state_restore_source (which mechanism restored state after last restart)
    - fake_presence with consequence note
    - low battery count
    """
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

        # Basic state
        info["integration_loaded"] = True
        info["alarm_state"] = coordinator.alarm_state

        # Last triggered (ISO timestamp — None if never triggered)
        last_triggered = getattr(coordinator, "_last_triggered", None)
        info["last_triggered"] = last_triggered or "never"

        # Bypassed sensors at last arm
        bypassed = getattr(coordinator, "_bypassed_sensors", [])
        info["bypassed_sensors_last_arm"] = len(bypassed)

        # Module health
        module_health = coordinator.get_module_health()
        enabled_count = sum(1 for m in module_health.values() if m.get("enabled"))
        healthy_count = sum(
            1 for m in module_health.values()
            if m.get("enabled") and m.get("status") == "ok"
        )
        problem_modules = [
            mid for mid, m in module_health.items()
            if m.get("enabled") and m.get("status") != "ok"
        ]
        info["modules_enabled"] = enabled_count
        info["modules_healthy"] = healthy_count
        if problem_modules:
            info["modules_with_problems"] = ", ".join(problem_modules)

        # Health score
        info["health_score"] = f"{coordinator.get_health_score()}%"

        # Zone info
        store = domain_data.get("store")
        if store:
            zones = store.get_zones()
            info["zones_configured"] = len(zones)
            enabled_zones = sum(1 for z in zones.values() if z.get("enabled", True))
            info["zones_enabled"] = enabled_zones
            info["sensors_configured"] = len(store.get_sensors())

        # Zone monitoring active — critical: if False while armed, sensors aren't watched
        zone_mgr = coordinator.zone_manager
        monitoring_active = bool(
            getattr(zone_mgr, "_unsubscribe_callbacks", None)
        )
        info["zone_monitoring_active"] = monitoring_active
        if coordinator.alarm_state not in ("disarmed", "arming") and not monitoring_active:
            info["zone_monitoring_warning"] = "Armed but zone monitoring is NOT active!"

        # Open sensors right now
        open_sensors = coordinator.open_sensors
        info["open_sensors_count"] = len(open_sensors)

        # Battery summary (uses coordinator cache — no expensive full scan)
        configured_eids: set[str] = set()
        if store:
            configured_eids = {
                s["entity_id"]
                for s in store.get_available_sensors()
                if s.get("entity_id")
            }
        if hasattr(coordinator, "get_batteries_cached"):
            batteries = coordinator.get_batteries_cached(configured_eids)
            low_batteries = [
                b for b in batteries
                if b.get("available") and b.get("level") is not None and b["level"] < 20
            ]
            info["low_battery_count"] = len(low_batteries)
            if low_batteries:
                info["low_battery_sensors"] = ", ".join(
                    b.get("name", b.get("entity_id", "?")) for b in low_batteries
                )

        # Fake presence — include consequence note so it's actionable
        fake = coordinator.fake_presence
        info["fake_presence_active"] = fake
        if fake:
            info["fake_presence_note"] = "Auto-arm is blocked while Fake Presence is on"

        # Arm history depth (confirms ring buffer is working)
        info["arm_history_events"] = len(getattr(coordinator, "_arm_history", []))

    except Exception as err:
        _LOGGER.error("Error getting system health info: %s", err)
        info["error"] = str(err)

    return info
