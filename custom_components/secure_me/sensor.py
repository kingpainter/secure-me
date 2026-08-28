"""Sensor platform for Secure Me - Health Metrics, Status & Battery Tracking."""
# VERSION = "1.5.5"

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COORDINATOR,
    DOMAIN,
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_ARMED_HOME_ALONE,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    VERSION,
)
from .coordinator import SecureMeCoordinator
from .module_dispatch import get_module_entity_ids
from .ws_helpers import _discover_batteries

_LOGGER = logging.getLogger(__name__)

# Battery thresholds
BATTERY_THRESHOLD_LOW = 20       # Warning level (%)
BATTERY_THRESHOLD_CRITICAL = 10  # Critical level (%)

# Human-readable state names
STATE_DISPLAY = {
    STATE_ALARM_DISARMED: "Disarmed",
    STATE_ALARM_ARMING: "Arming",
    STATE_ALARM_ARMED_AWAY: "Armed Away",
    STATE_ALARM_ARMED_HOME: "Armed Home",
    STATE_ALARM_ARMED_NIGHT: "Armed Night",
    STATE_ALARM_ARMED_VACATION: "Armed Vacation",
    STATE_ALARM_ARMED_HOME_ALONE: "Armed Home Alone",
    STATE_ALARM_PENDING: "Entry Delay",
    STATE_ALARM_TRIGGERED: "TRIGGERED",
}

# State icons
STATE_ICONS = {
    STATE_ALARM_DISARMED: "mdi:shield-off-outline",
    STATE_ALARM_ARMING: "mdi:shield-sync",
    STATE_ALARM_ARMED_AWAY: "mdi:shield-lock",
    STATE_ALARM_ARMED_HOME: "mdi:shield-home",
    STATE_ALARM_ARMED_NIGHT: "mdi:shield-moon",
    STATE_ALARM_ARMED_VACATION: "mdi:shield-airplane",
    STATE_ALARM_ARMED_HOME_ALONE: "mdi:shield-account",
    STATE_ALARM_PENDING: "mdi:shield-alert",
    STATE_ALARM_TRIGGERED: "mdi:shield-alert",
}


def _get_module_entities(module) -> list[str]:
    """Extract all configured entity IDs from a module.

    Delegates to module_dispatch.get_module_entity_ids() -- see
    binary_sensor.py's copy of this same fix for why a diverged local copy
    (missing siren support) is dangerous here.
    """
    return get_module_entity_ids(module)


def _check_entity_availability(hass: HomeAssistant, entity_id: str) -> bool:
    """Check if an entity is available."""
    state = hass.states.get(entity_id)
    return state is not None and state.state not in ("unavailable", "unknown")


def _get_configured_battery_scope(coordinator) -> set[str]:
    """Return entity_ids of sensors and module entities actually used by
    Secure Me (enabled alarm sensors + entities from enabled modules).

    Used to scope battery discovery to devices Secure Me actually cares
    about, matched by shared HA *device* (not just entity_id) -- a
    Zigbee/Z-Wave door sensor's battery reading lives on a separate entity
    on the same physical device as the contact sensor, so entity_id alone
    wouldn't find it.
    """
    configured: set[str] = set()

    store = getattr(coordinator, "store", None)
    if store:
        for s in store.get_available_sensors():
            if s.get("enabled") and s.get("entity_id"):
                configured.add(s["entity_id"])

    for module in coordinator.modules.values():
        if not module.enabled:
            continue
        configured.update(_get_module_entities(module))

    return configured


def _get_battery_summary(hass: HomeAssistant, coordinator) -> dict[str, Any]:
    """Get a complete battery summary, scoped to Secure Me's own sensors.

    Fix: previously scanned every device_class='battery' sensor in the
    entire Home Assistant instance, regardless of whether it had anything
    to do with Secure Me (a Sonos remote's battery, an unrelated device's
    battery, etc. would all show up as "lowest battery" candidates). Now
    reuses the same device-matched discovery already used by the Testing
    tab / health summary (ws_helpers._discover_batteries), scoped to
    entities Secure Me actually has enabled (alarm sensors + module
    entities) via _get_configured_battery_scope() above.

    Returns dict with:
        batteries: list of matched battery sensors with details
        lowest_level: int or None
        lowest_name: str
        lowest_entity: str
        low_count: count of sensors below BATTERY_THRESHOLD_LOW
        critical_count: count of sensors below BATTERY_THRESHOLD_CRITICAL
        total: total tracked sensors
        unavailable_count: sensors that can't be read
    """
    configured_entity_ids = _get_configured_battery_scope(coordinator)
    batteries = _discover_batteries(hass, configured_entity_ids)

    lowest_level: int | None = None
    lowest_name = "none"
    lowest_entity = "none"
    low_count = 0
    critical_count = 0
    unavailable_count = 0

    for bat in batteries:
        level = bat["level"]
        if not bat["available"] or level is None:
            unavailable_count += 1
            continue
        if lowest_level is None or level < lowest_level:
            lowest_level = level
            lowest_name = bat["name"]
            lowest_entity = bat["entity_id"]
        if level < BATTERY_THRESHOLD_LOW:
            low_count += 1
        if level < BATTERY_THRESHOLD_CRITICAL:
            critical_count += 1

    return {
        "batteries": batteries,
        "lowest_level": lowest_level,
        "lowest_name": lowest_name,
        "lowest_entity": lowest_entity,
        "low_count": low_count,
        "critical_count": critical_count,
        "total": len(batteries),
        "unavailable_count": unavailable_count,
    }


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secure Me sensors for health metrics, status, and battery tracking."""
    _LOGGER.info("Setting up Secure Me health metric and battery sensors")

    coordinator: SecureMeCoordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    entities: list[SensorEntity] = [
        # Health & status sensors
        SecureMeHealthScore(coordinator, config_entry),
        SecureMeAlarmStatus(coordinator, config_entry),
        SecureMeActiveModules(coordinator, config_entry),
        SecureMeOpenSensors(coordinator, config_entry),
        SecureMeLastArmedBy(coordinator, config_entry),
        SecureMeLastTriggeredBy(coordinator, config_entry),
        # Battery tracking sensors
        SecureMeLowestBattery(coordinator, config_entry),
        SecureMeLowBatteryCount(coordinator, config_entry),
    ]

    async_add_entities(entities)
    _LOGGER.info("Created %d sensors (health + battery)", len(entities))


class SecureMeBaseSensor(CoordinatorEntity[SecureMeCoordinator], SensorEntity):
    """Base class for Secure Me sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SecureMeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize base sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Secure Me Alarm System",
            "manufacturer": "Secure Me",
            "model": "Alarm Manager",
            "sw_version": VERSION,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class SecureMeHealthScore(SecureMeBaseSensor):
    """Sensor showing overall system health as a percentage (0-100).

    Calculation:
    - Each enabled module with configured entities counts equally
    - A module scores 100% if all its entities are available
    - A module scores proportionally less for each unavailable entity
    - If no modules have entities configured, score is 100
    """

    _attr_name = "Health Score"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:heart-pulse"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize health score sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_health_score"

    @property
    def native_value(self) -> int:
        """Return the health score as percentage."""
        total_entities = 0
        available_entities = 0

        for module_id, module in self.coordinator.modules.items():
            if not module.enabled:
                continue
            entities = _get_module_entities(module)
            for entity_id in entities:
                total_entities += 1
                if _check_entity_availability(self.hass, entity_id):
                    available_entities += 1

        if total_entities == 0:
            return 100

        return round((available_entities / total_entities) * 100)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return health breakdown per module."""
        breakdown: dict[str, Any] = {}
        total = 0
        ok = 0

        for module_id, module in self.coordinator.modules.items():
            if not module.enabled:
                breakdown[module_id] = "disabled"
                continue
            entities = _get_module_entities(module)
            if not entities:
                breakdown[module_id] = "no entities"
                continue
            avail = sum(1 for e in entities if _check_entity_availability(self.hass, e))
            total += len(entities)
            ok += avail
            breakdown[module_id] = f"{avail}/{len(entities)} ok"

        return {
            "module_breakdown": breakdown,
            "total_entities": total,
            "available_entities": ok,
        }


class SecureMeAlarmStatus(SecureMeBaseSensor):
    """Sensor showing human-readable alarm status with countdown info."""

    _attr_name = "Alarm Status"

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize alarm status sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_alarm_status"

    @property
    def native_value(self) -> str:
        """Return human-readable alarm state."""
        state = self.coordinator.alarm_state
        return STATE_DISPLAY.get(state, state)

    @property
    def icon(self) -> str:
        """Return state-specific icon."""
        state = self.coordinator.alarm_state
        return STATE_ICONS.get(state, "mdi:shield-outline")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed status info."""
        attrs: dict[str, Any] = {
            "raw_state": self.coordinator.alarm_state,
        }

        # Countdown during arming/pending
        countdown = self.coordinator.delay_countdown
        if countdown > 0:
            attrs["countdown"] = countdown

        # Armed/disarmed by
        if self.coordinator.armed_by:
            attrs["armed_by"] = self.coordinator.armed_by
        if self.coordinator.disarmed_by:
            attrs["disarmed_by"] = self.coordinator.disarmed_by
        if self.coordinator.triggered_by:
            attrs["triggered_by"] = self.coordinator.triggered_by

        # Open sensors
        open_sensors = self.coordinator.open_sensors
        if open_sensors:
            attrs["open_sensors"] = open_sensors
            attrs["open_sensor_count"] = len(open_sensors)

        return attrs


class SecureMeActiveModules(SecureMeBaseSensor):
    """Sensor showing count of active (enabled) modules."""

    _attr_name = "Active Modules"
    _attr_icon = "mdi:puzzle"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize active modules sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_active_modules"

    @property
    def native_value(self) -> int:
        """Return count of enabled modules."""
        return sum(
            1 for module in self.coordinator.modules.values()
            if module.enabled
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return list of enabled/disabled modules."""
        enabled: list[str] = []
        disabled: list[str] = []

        for module_id, module in self.coordinator.modules.items():
            if module.enabled:
                enabled.append(module_id)
            else:
                disabled.append(module_id)

        return {
            "enabled": enabled,
            "disabled": disabled,
            "total": len(self.coordinator.modules),
        }


class SecureMeOpenSensors(SecureMeBaseSensor):
    """Sensor showing count of currently open sensors across all zones."""

    _attr_name = "Open Sensors"
    _attr_icon = "mdi:door-open"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize open sensors counter."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_open_sensors"

    @property
    def native_value(self) -> int:
        """Return count of open sensors."""
        return len(self.coordinator.open_sensors)

    @property
    def icon(self) -> str:
        """Return icon based on open sensor count."""
        return "mdi:door-open" if self.native_value > 0 else "mdi:door-closed"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return list of open sensor entity IDs."""
        open_sensors = self.coordinator.open_sensors
        return {
            "sensors": open_sensors if open_sensors else "none",
        }


class SecureMeLastArmedBy(SecureMeBaseSensor):
    """Sensor showing who last armed the system."""

    _attr_name = "Last Armed By"
    _attr_icon = "mdi:account-lock"

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize last armed by sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_last_armed_by"

    @property
    def native_value(self) -> str:
        """Return who last armed the system."""
        return self.coordinator.armed_by or "none"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return arming details."""
        attrs: dict[str, Any] = {}
        state = self.coordinator.alarm_state
        if state not in (STATE_ALARM_DISARMED,):
            attrs["current_mode"] = STATE_DISPLAY.get(state, state)
        return attrs


class SecureMeLastTriggeredBy(SecureMeBaseSensor):
    """Sensor showing what last triggered the alarm."""

    _attr_name = "Last Triggered By"
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize last triggered by sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_last_triggered_by"

    @property
    def native_value(self) -> str:
        """Return what last triggered the alarm."""
        return self.coordinator.triggered_by or "none"

    @property
    def icon(self) -> str:
        """Return icon based on trigger state."""
        if self.coordinator.alarm_state == STATE_ALARM_TRIGGERED:
            return "mdi:alert-circle"
        return "mdi:alert-circle-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return trigger details."""
        attrs: dict[str, Any] = {}
        triggered_zones = self.coordinator.data.get("triggered_zones", 0) if self.coordinator.data else 0
        if triggered_zones > 0:
            attrs["triggered_zones"] = triggered_zones
        return attrs


# ─── Battery Tracking Sensors ───


class SecureMeLowestBattery(SecureMeBaseSensor):
    """Sensor showing the lowest battery level across all tracked sensors.

    Auto-discovers all sensor entities with device_class 'battery'.
    Shows the lowest percentage and which sensor it belongs to.

    Uses per-update caching to avoid scanning all battery sensors multiple
    times (native_value, icon and extra_state_attributes all use same data).
    """

    _attr_name = "Lowest Battery"
    _attr_native_unit_of_measurement = "%"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery-alert-variant-outline"

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize lowest battery sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_lowest_battery"
        self._battery_summary_cache: dict[str, Any] | None = None

    def _get_summary(self) -> dict[str, Any]:
        """Return battery summary, cached for current update cycle."""
        if self._battery_summary_cache is None:
            self._battery_summary_cache = _get_battery_summary(self.hass, self.coordinator)
        return self._battery_summary_cache

    @callback
    def _handle_coordinator_update(self) -> None:
        """Invalidate cache on coordinator update, then write state."""
        self._battery_summary_cache = None
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> int | None:
        """Return the lowest battery level."""
        return self._get_summary()["lowest_level"]

    @property
    def icon(self) -> str:
        """Return icon based on battery level."""
        level = self._get_summary()["lowest_level"]
        if level is None:
            return "mdi:battery-unknown"
        if level < BATTERY_THRESHOLD_CRITICAL:
            return "mdi:battery-alert-variant-outline"
        if level < BATTERY_THRESHOLD_LOW:
            return "mdi:battery-low"
        if level < 50:
            return "mdi:battery-medium"
        return "mdi:battery"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return full battery overview."""
        summary = self._get_summary()

        # Build per-sensor detail list
        sensor_details: dict[str, Any] = {}
        for bat in summary["batteries"]:
            level = bat["level"]
            if level is None:
                status = "unavailable"
            elif level < BATTERY_THRESHOLD_CRITICAL:
                status = "critical"
            elif level < BATTERY_THRESHOLD_LOW:
                status = "low"
            else:
                status = "ok"
            sensor_details[bat["entity_id"]] = {
                "name": bat["name"],
                "level": level,
                "status": status,
            }

        return {
            "lowest_sensor": summary["lowest_name"],
            "lowest_entity": summary["lowest_entity"],
            "total_tracked": summary["total"],
            "low_count": summary["low_count"],
            "critical_count": summary["critical_count"],
            "unavailable_count": summary["unavailable_count"],
            "threshold_low": BATTERY_THRESHOLD_LOW,
            "threshold_critical": BATTERY_THRESHOLD_CRITICAL,
            "sensors": sensor_details,
        }


class SecureMeLowBatteryCount(SecureMeBaseSensor):
    """Sensor showing count of batteries below the low threshold.

    Useful for automations: 'if low_battery_count > 0 then notify'.

    Uses per-update caching to avoid scanning all battery sensors multiple
    times (native_value, icon and extra_state_attributes all use same data).
    """

    _attr_name = "Low Battery Count"
    _attr_icon = "mdi:battery-alert"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry) -> None:
        """Initialize low battery count sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_low_battery_count"
        self._battery_summary_cache: dict[str, Any] | None = None

    def _get_summary(self) -> dict[str, Any]:
        """Return battery summary, cached for current update cycle."""
        if self._battery_summary_cache is None:
            self._battery_summary_cache = _get_battery_summary(self.hass, self.coordinator)
        return self._battery_summary_cache

    @callback
    def _handle_coordinator_update(self) -> None:
        """Invalidate cache on coordinator update, then write state."""
        self._battery_summary_cache = None
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> int:
        """Return count of batteries below low threshold."""
        return self._get_summary()["low_count"]

    @property
    def icon(self) -> str:
        """Return icon based on count."""
        return "mdi:battery-alert" if self.native_value > 0 else "mdi:battery-check"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return list of low/critical battery sensors."""
        summary = self._get_summary()

        low_sensors: list[dict[str, Any]] = []
        critical_sensors: list[dict[str, Any]] = []

        for bat in summary["batteries"]:
            level = bat["level"]
            if level is None or not bat["available"]:
                continue
            if level < BATTERY_THRESHOLD_CRITICAL:
                critical_sensors.append({
                    "entity_id": bat["entity_id"],
                    "name": bat["name"],
                    "level": level,
                })
            elif level < BATTERY_THRESHOLD_LOW:
                low_sensors.append({
                    "entity_id": bat["entity_id"],
                    "name": bat["name"],
                    "level": level,
                })

        return {
            "low_sensors": low_sensors if low_sensors else "none",
            "critical_sensors": critical_sensors if critical_sensors else "none",
            "critical_count": summary["critical_count"],
            "total_tracked": summary["total"],
        }
