"""Shared helpers for Secure Me WebSocket sub-modules."""
# VERSION = "1.5.2"
from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import DOMAIN


def _get_store(hass: HomeAssistant):
    """Return the SecureMeStore instance, or None if not yet initialised."""
    return hass.data[DOMAIN].get("store")


def _get_coordinator(hass: HomeAssistant):
    """Return the active SecureMeCoordinator, or None if not found.

    The coordinator is stored per config entry under entry.entry_id.
    We iterate domain data to find the first valid coordinator dict.
    """
    domain_data = hass.data.get(DOMAIN, {})
    for value in domain_data.values():
        if isinstance(value, dict) and "coordinator" in value:
            return value["coordinator"]
    return None


def _discover_batteries(
    hass,
    configured_entity_ids: set | None = None,
) -> list[dict]:
    """Discover battery sensors for configured Secure Me sensors only.

    Moved here from websocket_api.py to avoid circular imports when
    coordinator.py calls this via get_batteries_cached().
    """
    if not configured_entity_ids:
        return []

    device_ids: set[str] = set()
    try:
        from homeassistant.helpers import entity_registry as er
        ent_reg = er.async_get(hass)
        for eid in configured_entity_ids:
            entry = ent_reg.async_get(eid)
            if entry and entry.device_id:
                device_ids.add(entry.device_id)
    except Exception:
        device_ids = set()

    batteries: list[dict] = []
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != "battery":
            continue
        if device_ids:
            try:
                from homeassistant.helpers import entity_registry as er
                ent_reg = er.async_get(hass)
                entry = ent_reg.async_get(state.entity_id)
                if not entry or entry.device_id not in device_ids:
                    continue
            except Exception:
                pass
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
    return sorted(batteries, key=lambda b: (b["level"] is None, b["level"] or 0))
