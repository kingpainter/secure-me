"""Module dispatch and health/battery tracking for Secure Me.

Extracted from coordinator.py (v1.5.5) following the same composition
pattern already used for zones.py's ZoneManager, state_machine.py's
AlarmStateMachine, and auto_actions.py's AutoActionsManager --
coordinator.py had accumulated module instantiation, arm/disarm/trigger
dispatch to the six modules, and health/battery tracking directly on
itself, on top of everything else it owns (state machine orchestration,
push notifications, arm history). ModuleDispatcher owns that one
sub-concern; coordinator.py composes it via `self.module_dispatcher` and
delegates the small set of methods external code already calls directly
(`coordinator.modules`, `coordinator.update_module_config()`,
`coordinator.get_health_score()`, etc.) so nothing outside coordinator.py
needs to change.
"""
# VERSION = "1.5.5"

import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import EVENT_MODULE_ERROR
from .modules import (
    CameraModule,
    ClimateModule,
    LightsModule,
    LockModule,
    SirenModule,
    TTSModule,
)

_LOGGER = logging.getLogger(__name__)

_MODULE_CLASSES = {
    "camera": CameraModule,
    "lock": LockModule,
    "lights": LightsModule,
    "climate": ClimateModule,
    "siren": SirenModule,
    "tts": TTSModule,
}


def get_module_entity_ids(module) -> list[str]:
    """Extract every entity_id a module currently owns, for health/availability checks.

    Single source of truth for this logic -- previously ws_modules.py kept its
    own separate copy (used by the Testing tab / manual self-tests), which had
    diverged from this one: it correctly read the siren module's `sirens` list
    (list of dicts with an `entity_id` key), while this copy did not. That gap
    meant a siren going unavailable was invisible to the passive health score /
    System Health panel / secure_me_health_updated event (all driven by
    ModuleDispatcher.get_health_score()/get_module_health() below), and only
    ever surfaced if someone manually ran a test -- for the module the project's
    own MODULE_SEVERITY map rates "critical". ws_modules.py now imports this
    function instead of defining its own.
    """
    entities: list[str] = []
    for attr in ("poe_switches", "cameras", "recording_entities", "locks", "lights", "climates", "media_players"):
        val = getattr(module, attr, None)
        if isinstance(val, list):
            entities.extend(val)
    # Siren module: `sirens` is a list of dicts with an entity_id key, not a
    # flat string list -- needs its own extraction step.
    sirens_val = getattr(module, "sirens", None)
    if isinstance(sirens_val, list):
        for entry in sirens_val:
            if isinstance(entry, dict) and entry.get("entity_id"):
                entities.append(entry["entity_id"])
            elif isinstance(entry, str) and "." in entry:
                entities.append(entry)
    for attr in ("door_sensors", "battery_sensors"):
        val = getattr(module, attr, None)
        if isinstance(val, dict):
            entities.extend(val.values())
    for attr in ("gateway_light",):
        val = getattr(module, attr, None)
        if isinstance(val, str) and "." in val:
            entities.append(val)
    if not entities and hasattr(module, "config"):
        for key in ("entities", "cameras", "locks", "climates", "lights", "media_players", "poe_switches"):
            val = module.config.get(key)
            if isinstance(val, list):
                entities.extend(val)
            elif isinstance(val, dict):
                entities.extend(val.values())
    return list({e for e in entities if e and isinstance(e, str) and "." in e})


def normalize_module_config(module_id: str, config: dict) -> dict:
    """Normalize panel-saved config (objects) to module class format (flat strings)."""
    normalized = dict(config)

    def extract_ids(items) -> list[str]:
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
        raw = config.get("cameras", [])
        normalized["cameras"] = extract_ids(raw)
        poe = [
            c["poe_port"] for c in raw
            if isinstance(c, dict) and c.get("poe_port") and "." in str(c["poe_port"])
        ]
        if poe:
            normalized["poe_switches"] = poe
    elif module_id == "lock":
        normalized["locks"] = extract_ids(config.get("locks", []))
    elif module_id == "climate":
        normalized["climates"] = extract_ids(config.get("thermostats", []))
    elif module_id == "lights":
        # Frontend saves as 'entities' (flat strings); module class expects 'lights'
        raw = config.get("entities") or config.get("lights", [])
        normalized["lights"] = extract_ids(raw) if raw else []
    elif module_id == "tts":
        normalized["media_players"] = extract_ids(config.get("entities", []))
        normalized["tts_service"] = config.get("tts_service", "tts.cloud_say")
        normalized["language"] = config.get("language", "da")
        normalized["volume"] = config.get("volume", 0.5)
        normalized["custom_messages"] = config.get("custom_messages", [])
        # v1.4.0: speaker profiles passed through from store
        normalized["speaker_profiles"] = config.get("speaker_profiles", [])
    elif module_id == "siren":
        # Pass sirens list through as-is (list of dicts with entity_id, pattern, duration, volume)
        normalized["sirens"] = config.get("sirens", [])
        # Legacy gateway fields
        if config.get("gateway_mac"):
            normalized["gateway_mac"] = config["gateway_mac"]
        if config.get("gateway_light"):
            normalized["gateway_light"] = config["gateway_light"]

    return normalized


class ModuleDispatcher:
    """Owns the six alarm modules: instantiation, arm/disarm/trigger dispatch,
    health scoring, and cached battery discovery.

    Lifecycle: constructed once in SecureMeCoordinator.__init__() with
    config_entry.options as a first-boot default; async_load_store_config()
    re-initializes each module via update_module_config() once the store's
    saved config is available, which is the config that actually ends up in
    effect.
    """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self.hass = hass
        self.config_entry = config_entry
        self.modules: dict[str, Any] = {}

        self._battery_cache: list[dict] | None = None
        self._battery_cache_time: float = 0.0
        self._battery_cache_ttl: float = 300.0  # 5-minute TTL

        self._init_modules()

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def _init_modules(self) -> None:
        """Initialize all available modules with config_entry.options as a
        first-boot default. Only ever called once from __init__, before the
        store is loaded -- async_load_store_config() re-initializes every
        module immediately afterwards via update_module_config() once the
        store's saved config is available, which is the config that actually
        ends up in effect."""
        options_modules = self.config_entry.options.get("modules", {})

        for mid, cls in _MODULE_CLASSES.items():
            module_config = options_modules.get(mid, {})
            self.modules[mid] = cls(self.hass, module_config)

        _LOGGER.info("Modules initialized: %s", list(self.modules.keys()))

    def update_module_config(self, module_id: str, config: dict) -> bool:
        """Re-initialize a module with updated configuration."""
        cls = _MODULE_CLASSES.get(module_id)
        if not cls:
            return False
        try:
            self.modules[module_id] = cls(self.hass, config)
            return True
        except Exception as err:
            _LOGGER.error("Failed to re-initialize module %s: %s", module_id, err)
            return False

    # -------------------------------------------------------------------------
    # Arm / disarm / trigger dispatch
    # -------------------------------------------------------------------------

    async def _dispatch(self, action: str, call) -> None:
        """Call `call(module)` on every enabled module, firing EVENT_MODULE_ERROR
        for any that raise instead of letting one bad module abort the rest.

        `action` is the label used in both the log message and the fired
        EVENT_MODULE_ERROR event ("arm_away", "disarm", "trigger", etc.) --
        kept identical to the labels used before this dispatch logic was
        extracted from coordinator.py, since ws_modules.py and any external
        automations listening for secure_me_module_error may match on it.
        """
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await call(module)
                except Exception as err:
                    _LOGGER.error("Module %s failed on %s: %s", mid, action, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": action, "error": str(err)}
                    )

    async def execute_arm_away(self) -> None:
        await self._dispatch("arm_away", lambda m: m.async_arm("away"))

    async def execute_arm_home(self) -> None:
        await self._dispatch("arm_home", lambda m: m.async_arm("home"))

    async def execute_arm_night(self) -> None:
        await self._dispatch("arm_night", lambda m: m.async_arm("night"))

    async def execute_disarm(self) -> None:
        await self._dispatch("disarm", lambda m: m.async_disarm())

    async def execute_trigger(self) -> None:
        await self._dispatch("trigger", lambda m: m.async_trigger())

    # -------------------------------------------------------------------------
    # Health / battery
    # -------------------------------------------------------------------------

    def get_batteries_cached(self, configured_eids: set[str]) -> list[dict]:
        """Return cached battery list; rebuilds every 5 minutes."""
        now = time.monotonic()
        if (
            self._battery_cache is not None
            and now - self._battery_cache_time < self._battery_cache_ttl
        ):
            return self._battery_cache
        from .ws_helpers import _discover_batteries
        self._battery_cache = _discover_batteries(self.hass, configured_eids)
        self._battery_cache_time = now
        return self._battery_cache

    def invalidate_battery_cache(self) -> None:
        """Force a battery cache rebuild on next access."""
        self._battery_cache = None

    def get_health_score(self) -> int:
        total, available = 0, 0
        for module in self.modules.values():
            if not module.enabled:
                continue
            for eid in get_module_entity_ids(module):
                total += 1
                state = self.hass.states.get(eid)
                if state and state.state not in ("unavailable", "unknown"):
                    available += 1
        return round((available / total) * 100) if total > 0 else 100

    def get_module_health(self) -> dict[str, dict]:
        result = {}
        for mid, module in self.modules.items():
            if not module.enabled:
                result[mid] = {"enabled": False, "status": "disabled", "total": 0, "available": 0, "unavailable": []}
                continue
            entities = get_module_entity_ids(module)
            unavail = [
                eid for eid in entities
                if not self.hass.states.get(eid)
                or self.hass.states.get(eid).state in ("unavailable", "unknown")
            ]
            result[mid] = {
                "enabled": True,
                "status": "degraded" if getattr(module, "degraded", False) else ("error" if unavail else "ok"),
                "total": len(entities),
                "available": len(entities) - len(unavail),
                "unavailable": unavail,
            }
        return result

    def get_enabled_module_count(self) -> int:
        return sum(1 for m in self.modules.values() if m.enabled)

    # -------------------------------------------------------------------------
    # Shutdown
    # -------------------------------------------------------------------------

    async def async_cleanup(self) -> None:
        for mid, module in self.modules.items():
            try:
                await module.async_cleanup()
            except Exception as err:
                _LOGGER.error("Module %s cleanup failed: %s", mid, err)
