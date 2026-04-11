"""Binary sensor platform for Secure Me - Health Monitoring & Battery Alerts."""
# VERSION = "1.3.0"

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COORDINATOR,
    DOMAIN,
    EVENT_PRESENCE_CHANGED,
    MODULE_CAMERA,
    MODULE_LOCK,
    MODULE_LIGHTS,
    MODULE_CLIMATE,
    MODULE_SIREN,
    MODULE_TTS,
)
from .coordinator import SecureMeCoordinator

_LOGGER = logging.getLogger(__name__)

# Battery thresholds (must match sensor.py)
BATTERY_THRESHOLD_LOW = 20       # Warning level (%)
BATTERY_THRESHOLD_CRITICAL = 10  # Critical level (%)

# Module display names and icons
MODULE_INFO = {
    MODULE_CAMERA: {"name": "Camera Module", "icon_ok": "mdi:camera", "icon_problem": "mdi:camera-off"},
    MODULE_LOCK: {"name": "Lock Module", "icon_ok": "mdi:lock", "icon_problem": "mdi:lock-alert"},
    MODULE_LIGHTS: {"name": "Lights Module", "icon_ok": "mdi:lightbulb", "icon_problem": "mdi:lightbulb-alert"},
    MODULE_CLIMATE: {"name": "Climate Module", "icon_ok": "mdi:thermostat", "icon_problem": "mdi:thermostat-alert"},
    MODULE_SIREN: {"name": "Siren Module", "icon_ok": "mdi:alarm-bell", "icon_problem": "mdi:alarm-light-off"},
    MODULE_TTS: {"name": "TTS Module", "icon_ok": "mdi:text-to-speech", "icon_problem": "mdi:text-to-speech-off"},
}


def _get_module_entities(module) -> list[str]:
    """Extract all configured entity IDs from a module.

    Returns a flat list of entity_id strings found in the module's config attributes.
    """
    entities: list[str] = []

    # List-type attributes (most modules)
    for attr_name in (
        "poe_switches", "cameras", "recording_entities",  # camera
        "locks",                                            # lock
        "lights",                                           # lights
        "climates",                                         # climate
        "media_players",                                    # tts
    ):
        value = getattr(module, attr_name, None)
        if isinstance(value, list):
            entities.extend(value)

    # Dict-type attributes (lock module has door_sensors, battery_sensors as dicts)
    for attr_name in ("door_sensors", "battery_sensors"):
        value = getattr(module, attr_name, None)
        if isinstance(value, dict):
            entities.extend(value.values())

    # Single entity attributes (siren)
    for attr_name in ("gateway_light",):
        value = getattr(module, attr_name, None)
        if isinstance(value, str) and "." in value:
            entities.append(value)

    return entities


def _check_entity_availability(hass: HomeAssistant, entity_id: str) -> bool:
    """Check if an entity is available in Home Assistant."""
    state = hass.states.get(entity_id)
    return state is not None and state.state not in ("unavailable", "unknown")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secure Me binary sensors for health monitoring and battery alerts."""
    _LOGGER.info("Setting up Secure Me health monitoring binary sensors")

    coordinator: SecureMeCoordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    entities: list[BinarySensorEntity] = []

    # System-wide health sensor
    entities.append(SecureMeSystemHealth(coordinator, config_entry))

    # Per-module health sensors
    for module_id in MODULE_INFO:
        entities.append(
            SecureMeModuleHealth(coordinator, config_entry, module_id)
        )

    # Battery alert sensor
    entities.append(SecureMeBatteryAlert(coordinator, config_entry))

    # Presence sensor (anyone home based on user tracker entities)
    entities.append(SecureMePresence(coordinator, config_entry))

    async_add_entities(entities)
    _LOGGER.info("Created %d health monitoring binary sensors", len(entities))


class SecureMeSystemHealth(CoordinatorEntity[SecureMeCoordinator], BinarySensorEntity):
    """Binary sensor for overall system health.

    State is ON when there is a problem (device_class = problem).
    """

    _attr_has_entity_name = True
    _attr_name = "System Health"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:shield-check"

    def __init__(
        self,
        coordinator: SecureMeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize system health sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_system_health"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Secure Me Alarm System",
            "manufacturer": "Secure Me",
            "model": "Alarm Manager",
            "sw_version": "0.2.0",
        }

    @property
    def is_on(self) -> bool:
        """Return True if there is a problem (any module unhealthy)."""
        for module_id, module in self.coordinator.modules.items():
            if not module.enabled:
                continue
            entities = _get_module_entities(module)
            for entity_id in entities:
                if not _check_entity_availability(self.hass, entity_id):
                    return True
        return False

    @property
    def icon(self) -> str:
        """Return icon based on health state."""
        return "mdi:shield-alert" if self.is_on else "mdi:shield-check"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed health information."""
        modules_ok = 0
        modules_problem = 0
        modules_disabled = 0
        problem_details: list[str] = []

        for module_id, module in self.coordinator.modules.items():
            if not module.enabled:
                modules_disabled += 1
                continue

            entities = _get_module_entities(module)
            unavailable = [
                e for e in entities
                if not _check_entity_availability(self.hass, e)
            ]

            if unavailable:
                modules_problem += 1
                for e in unavailable:
                    problem_details.append(f"{module_id}: {e}")
            else:
                modules_ok += 1

        total_checked = modules_ok + modules_problem
        health_score = round((modules_ok / total_checked) * 100) if total_checked > 0 else 100

        return {
            "health_score": health_score,
            "modules_ok": modules_ok,
            "modules_problem": modules_problem,
            "modules_disabled": modules_disabled,
            "problems": problem_details if problem_details else "none",
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SecureMePresence(CoordinatorEntity[SecureMeCoordinator], BinarySensorEntity):
    """Binary sensor representing whether anyone is home.

    State is ON when at least one tracked user (via tracker_entity in their
    user profile) is home, or when Fake Presence is active.
    State is OFF when all tracked users are away AND Fake Presence is off.

    This sensor is the authoritative presence source for Secure Me auto-arm.
    It listens directly on each user's tracker entity so it updates immediately
    when a person entity changes state.

    entity_id: binary_sensor.secure_me_anyone_home
    device_class: presence (on = home, off = away)
    """

    _attr_has_entity_name = True
    _attr_name = "Anyone Home"
    _attr_device_class = BinarySensorDeviceClass.PRESENCE

    def __init__(
        self,
        coordinator: SecureMeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize presence sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_anyone_home"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Secure Me Alarm System",
            "manufacturer": "Secure Me",
            "model": "Alarm Manager",
            "sw_version": "0.2.0",
        }
        # Subscriptions to tracker entity state changes
        self._tracker_unsubs: list = []
        self._last_anyone_home: bool | None = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to tracker entity state changes when added to HA."""
        await super().async_added_to_hass()
        self._subscribe_trackers()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe tracker listeners on removal."""
        self._unsubscribe_trackers()

    def _get_tracker_entities(self) -> list[str]:
        """Collect all tracker_entity values from enabled user profiles."""
        if not hasattr(self.coordinator, "store") or not self.coordinator.store:
            return []
        trackers = []
        for user in self.coordinator.store.get_users().values():
            if not user.get("enabled", True):
                continue
            tracker = user.get("tracker_entity", "")
            if tracker and "." in tracker:
                trackers.append(tracker)
        return trackers

    def _subscribe_trackers(self) -> None:
        """Subscribe to state changes for all configured tracker entities.

        Called on startup and whenever the store may have changed (e.g. after
        a user profile is saved). Previous subscriptions are cancelled first.
        """
        self._unsubscribe_trackers()
        trackers = self._get_tracker_entities()
        if not trackers:
            _LOGGER.debug("SecureMePresence: no tracker entities configured on users")
            return

        from homeassistant.helpers.event import async_track_state_change_event

        @callback
        def _tracker_state_changed(event) -> None:
            """Fire when any tracked person entity changes state."""
            self._update_and_fire()

        unsub = async_track_state_change_event(
            self.hass, trackers, _tracker_state_changed
        )
        self._tracker_unsubs.append(unsub)
        _LOGGER.debug(
            "SecureMePresence: subscribed to %d tracker entities: %s",
            len(trackers), trackers,
        )

    def _unsubscribe_trackers(self) -> None:
        """Cancel all tracker state-change subscriptions."""
        for unsub in self._tracker_unsubs:
            unsub()
        self._tracker_unsubs.clear()

    def _update_and_fire(self) -> None:
        """Recompute presence and fire EVENT_PRESENCE_CHANGED if state changed."""
        presence = self.coordinator.get_presence_status()
        anyone_home = presence["anyone_home"]
        self.async_write_ha_state()

        if anyone_home != self._last_anyone_home:
            self._last_anyone_home = anyone_home
            self.hass.bus.async_fire(
                EVENT_PRESENCE_CHANGED,
                {
                    "anyone_home": anyone_home,
                    "people_home": presence["people_home"],
                    "people_away": presence["people_away"],
                    "fake_presence": presence["fake_presence"],
                },
            )
            _LOGGER.info(
                "Secure Me presence changed: anyone_home=%s home=%s away=%s",
                anyone_home,
                presence["people_home"],
                presence["people_away"],
            )

    @property
    def is_on(self) -> bool:
        """Return True if anyone is home (presence ON)."""
        return self.coordinator.get_presence_status()["anyone_home"]

    @property
    def icon(self) -> str:
        """Return icon based on presence state."""
        return "mdi:home-account" if self.is_on else "mdi:home-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return presence details."""
        presence = self.coordinator.get_presence_status()
        return {
            "people_home": presence["people_home"] or "none",
            "people_away": presence["people_away"] or "none",
            "tracked_users": presence["tracked_users"],
            "fake_presence": presence["fake_presence"],
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update — also re-subscribe if user list changed."""
        current_trackers = self._get_tracker_entities()
        # Detect if the tracked set has changed (user added/removed/edited)
        # by comparing count against number of active subscriptions.
        if len(current_trackers) != len(self._tracker_unsubs) or not self._tracker_unsubs:
            self._subscribe_trackers()
        self.async_write_ha_state()


class SecureMeModuleHealth(CoordinatorEntity[SecureMeCoordinator], BinarySensorEntity):
    """Binary sensor for individual module health.

    State is ON when the module has a problem (device_class = problem).
    Returns OFF (no problem) if module is disabled or has no entities configured.
    """

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: SecureMeCoordinator,
        config_entry: ConfigEntry,
        module_id: str,
    ) -> None:
        """Initialize module health sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._module_id = module_id
        info = MODULE_INFO[module_id]
        self._attr_name = info["name"]
        self._icon_ok = info["icon_ok"]
        self._icon_problem = info["icon_problem"]
        self._attr_unique_id = f"{config_entry.entry_id}_{module_id}_health"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Secure Me Alarm System",
            "manufacturer": "Secure Me",
            "model": "Alarm Manager",
            "sw_version": "0.2.0",
        }

    @property
    def _module(self):
        """Get the module instance."""
        return self.coordinator.modules.get(self._module_id)

    @property
    def is_on(self) -> bool:
        """Return True if module has a problem."""
        module = self._module
        if module is None or not module.enabled:
            return False  # Disabled = no problem to report

        entities = _get_module_entities(module)
        if not entities:
            return False  # No entities configured = nothing to check

        return any(
            not _check_entity_availability(self.hass, e)
            for e in entities
        )

    @property
    def icon(self) -> str:
        """Return icon based on module state."""
        module = self._module
        if module is None or not module.enabled:
            return "mdi:cancel"
        return self._icon_problem if self.is_on else self._icon_ok

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return module health details."""
        module = self._module
        if module is None:
            return {"status": "not_loaded"}

        if not module.enabled:
            return {"status": "disabled"}

        entities = _get_module_entities(module)
        if not entities:
            return {
                "status": "ok",
                "configured_entities": 0,
                "note": "No entities configured",
            }

        available = [e for e in entities if _check_entity_availability(self.hass, e)]
        unavailable = [e for e in entities if not _check_entity_availability(self.hass, e)]

        return {
            "status": "problem" if unavailable else "ok",
            "configured_entities": len(entities),
            "available": len(available),
            "unavailable_entities": unavailable if unavailable else "none",
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


# ????????? Battery Alert Sensor ?????????


def _discover_battery_levels(hass: HomeAssistant) -> list[dict[str, Any]]:
    """Discover all battery sensors and their current levels.

    Returns list of dicts with entity_id, name, level, available.
    """
    batteries: list[dict[str, Any]] = []
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != "battery":
            continue
        level: int | None = None
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


class SecureMeBatteryAlert(CoordinatorEntity[SecureMeCoordinator], BinarySensorEntity):
    """Binary sensor that turns ON when any battery is critically low.

    Uses device_class 'battery' so it integrates with HA's battery monitoring.
    State is ON when any discovered battery sensor is below BATTERY_THRESHOLD_CRITICAL.
    """

    _attr_has_entity_name = True
    _attr_name = "Battery Alert"
    _attr_device_class = BinarySensorDeviceClass.BATTERY

    def __init__(
        self,
        coordinator: SecureMeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize battery alert sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_battery_alert"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Secure Me Alarm System",
            "manufacturer": "Secure Me",
            "model": "Alarm Manager",
            "sw_version": "0.2.0",
        }

    @property
    def is_on(self) -> bool:
        """Return True if any battery is critically low."""
        for bat in self._get_batteries():
            if bat["available"] and bat["level"] is not None:
                if bat["level"] < BATTERY_THRESHOLD_CRITICAL:
                    return True
        return False

    @property
    def icon(self) -> str:
        """Return icon based on battery alert state."""
        return "mdi:battery-alert-variant-outline" if self.is_on else "mdi:battery-check-outline"

    def _get_batteries(self) -> list[dict[str, Any]]:
        """Get batteries from cache — discover once per update cycle.

        Caches results so is_on and extra_state_attributes share one
        scan instead of calling hass.states.async_all() twice per update.
        """
        if not hasattr(self, "_battery_cache"):
            self._battery_cache: list[dict[str, Any]] = []
            self._battery_cache_key: int = -1
        # Use coordinator last_update_success count as cache key
        current_key = id(self.coordinator.data)
        if current_key != self._battery_cache_key:
            self._battery_cache = _discover_battery_levels(self.hass)
            self._battery_cache_key = current_key
        return self._battery_cache

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details about critical and low batteries."""
        batteries = self._get_batteries()

        critical: list[dict[str, Any]] = []
        low: list[dict[str, Any]] = []
        ok_count = 0
        unavailable_count = 0

        for bat in batteries:
            level = bat["level"]
            if not bat["available"] or level is None:
                unavailable_count += 1
                continue
            if level < BATTERY_THRESHOLD_CRITICAL:
                critical.append({
                    "entity_id": bat["entity_id"],
                    "name": bat["name"],
                    "level": level,
                })
            elif level < BATTERY_THRESHOLD_LOW:
                low.append({
                    "entity_id": bat["entity_id"],
                    "name": bat["name"],
                    "level": level,
                })
            else:
                ok_count += 1

        return {
            "critical_batteries": critical if critical else "none",
            "low_batteries": low if low else "none",
            "ok_count": ok_count,
            "total_tracked": len(batteries),
            "unavailable_count": unavailable_count,
            "threshold_critical": BATTERY_THRESHOLD_CRITICAL,
            "threshold_low": BATTERY_THRESHOLD_LOW,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
