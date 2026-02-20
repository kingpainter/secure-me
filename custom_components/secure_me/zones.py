"""Zone management for Secure Me."""
# VERSION = "0.6.0"

import asyncio
import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ZONE_TYPE_ENTRY,
    ZONE_TYPE_INSTANT,
    ZONE_TYPE_INTERIOR,
    ZONE_TYPE_PERIMETER,
    NOTIFY_ID_MODULE_ERROR,
)

_LOGGER = logging.getLogger(__name__)

# States that mean a sensor is "open" / triggered
_OPEN_STATES = frozenset({"on", "open", "detected", "unlocked"})


class Zone:
    """Representation of a security zone."""

    def __init__(
        self,
        zone_id: str,
        zone_type: str,
        sensors: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        self.zone_id = zone_id
        self.zone_type = zone_type
        self.sensors = sensors or []
        self.enabled = enabled
        self._open_sensors: list[str] = []

    @property
    def is_triggered(self) -> bool:
        return len(self._open_sensors) > 0

    @property
    def open_sensors(self) -> list[str]:
        return self._open_sensors.copy()

    def update_sensor_state(self, entity_id: str, is_open: bool) -> bool:
        """Update sensor state. Returns True if zone trigger state changed."""
        was_triggered = self.is_triggered
        if is_open and entity_id not in self._open_sensors:
            self._open_sensors.append(entity_id)
        elif not is_open and entity_id in self._open_sensors:
            self._open_sensors.remove(entity_id)
        return was_triggered != self.is_triggered

    def clear_open_sensors(self) -> None:
        self._open_sensors.clear()

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "zone_type": self.zone_type,
            "sensors": self.sensors,
            "enabled": self.enabled,
            "is_triggered": self.is_triggered,
            "open_sensors": self._open_sensors,
        }


class ZoneManager:
    """Manage security zones and sensors.

    v0.5.0 edge case fixes:
    - Sensor goes unavailable while armed: logged + notified, NOT treated as open
    - Sensor deleted while armed: gracefully ignored, warning logged
    - Sensor removed from HA while armed: mapping cleaned up, user notified
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._zones: dict[str, Zone] = {}
        self._sensor_to_zone: dict[str, str] = {}
        self._unsubscribe_callbacks: list = []
        self._trigger_callback = None

        # PERF v0.6.0: Debounce per-sensor to suppress flapping.
        # Key: entity_id, Value: monotonic timestamp of last trigger callback
        self._last_trigger_time: dict[str, float] = {}
        self._debounce_interval: float = 0.5  # seconds — ignore repeated triggers within 500ms

        _LOGGER.info("Zone manager initialized")

    @property
    def zones(self) -> dict[str, Zone]:
        """Return zones dict."""
        return self._zones

    def register_trigger_callback(self, callback_func) -> None:
        self._trigger_callback = callback_func

    def add_zone(
        self,
        zone_id: str,
        zone_type: str,
        sensors: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        zone = Zone(zone_id, zone_type, sensors, enabled)
        self._zones[zone_id] = zone
        if sensors:
            for sensor in sensors:
                self._sensor_to_zone[sensor] = zone_id
        _LOGGER.info(
            "Added zone: %s (type=%s, sensors=%d, enabled=%s)",
            zone_id, zone_type, len(sensors or []), enabled,
        )

    def remove_zone(self, zone_id: str) -> None:
        if zone_id not in self._zones:
            return
        zone = self._zones.pop(zone_id)
        for sensor in zone.sensors:
            self._sensor_to_zone.pop(sensor, None)
        _LOGGER.info("Removed zone: %s", zone_id)

    def get_zone(self, zone_id: str) -> Zone | None:
        return self._zones.get(zone_id)

    def get_zones(self) -> list[Zone]:
        return list(self._zones.values())

    def get_zone_by_sensor(self, entity_id: str) -> Zone | None:
        zone_id = self._sensor_to_zone.get(entity_id)
        return self._zones.get(zone_id) if zone_id else None

    def get_triggered_zones(self) -> list[Zone]:
        return [z for z in self._zones.values() if z.is_triggered]

    def get_entry_zones(self) -> list[Zone]:
        return [z for z in self._zones.values() if z.zone_type == ZONE_TYPE_ENTRY]

    def get_instant_zones(self) -> list[Zone]:
        return [z for z in self._zones.values() if z.zone_type == ZONE_TYPE_INSTANT]

    def get_all_open_sensors(self) -> list[str]:
        open_sensors: list[str] = []
        for zone in self._zones.values():
            if zone.enabled:
                open_sensors.extend(zone.open_sensors)
        return open_sensors

    def update_sensor_state(self, entity_id: str, state: State) -> tuple[bool, Zone | None]:
        """Update sensor state.

        EDGE CASE: If new_state is None (entity removed from HA), the sensor
        is treated as CLOSED (not open) to avoid false triggers. A warning
        is logged and a persistent notification is sent to the user.

        EDGE CASE: If state is 'unavailable' or 'unknown', the sensor is
        also treated as closed (not open). This prevents an offline sensor
        from being ignored but also prevents spurious alarms.
        """
        zone = self.get_zone_by_sensor(entity_id)
        if not zone or not zone.enabled:
            return False, None

        # EDGE CASE: entity deleted / removed from HA
        if state is None:
            _LOGGER.warning(
                "Sensor %s has no state (removed from HA?) — treating as closed",
                entity_id,
            )
            self.hass.components.persistent_notification.async_create(
                message=f"Sensor '{entity_id}' in zone '{zone.zone_id}' has disappeared from Home Assistant. "
                        f"Check if the device is still connected.",
                title="Secure Me - Sensor Missing",
                notification_id=f"{NOTIFY_ID_MODULE_ERROR}_sensor_{entity_id.replace('.', '_')}",
            )
            changed = zone.update_sensor_state(entity_id, False)
            return changed, zone if changed else None

        # EDGE CASE: sensor unavailable/unknown while armed
        if state.state in ("unavailable", "unknown"):
            _LOGGER.warning(
                "Sensor %s is %s while monitoring active — treating as closed, check device",
                entity_id, state.state,
            )
            self.hass.components.persistent_notification.async_create(
                message=f"Sensor '{entity_id}' in zone '{zone.zone_id}' is {state.state}. "
                        f"Please check the device connection.",
                title="Secure Me - Sensor Unavailable",
                notification_id=f"{NOTIFY_ID_MODULE_ERROR}_unavail_{entity_id.replace('.', '_')}",
            )
            changed = zone.update_sensor_state(entity_id, False)
            return changed, zone if changed else None

        is_open = state.state in _OPEN_STATES
        changed = zone.update_sensor_state(entity_id, is_open)

        if changed:
            _LOGGER.info(
                "Zone %s state changed: triggered=%s (sensor=%s, state=%s)",
                zone.zone_id, zone.is_triggered, entity_id, state.state,
            )

        return changed, zone

    def start_monitoring(self, callback_func=None) -> None:
        """Start monitoring sensors."""
        trigger_callback = callback_func or self._trigger_callback
        if not trigger_callback:
            _LOGGER.error("No trigger callback registered")
            return

        all_sensors: set[str] = set()
        for zone in self._zones.values():
            all_sensors.update(zone.sensors)

        if not all_sensors:
            _LOGGER.warning("No sensors to monitor")
            return

        @callback
        def _sensor_state_changed(event):
            """Handle sensor state change event.

            PERF v0.6.0: Debounce rapid state changes per sensor.
            A flapping sensor (on/off/on within 500ms) only fires the trigger
            callback once, preventing cascading alarm triggers and log spam.

            EDGE CASE (v0.5.0): new_state can be None if entity is removed from HA.
            """
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")

            changed, zone = self.update_sensor_state(entity_id, new_state)
            if changed and zone and zone.is_triggered:
                now = time.monotonic()
                last = self._last_trigger_time.get(entity_id, 0.0)
                if now - last < self._debounce_interval:
                    _LOGGER.debug(
                        "Sensor %s debounced (%.3fs since last trigger)",
                        entity_id, now - last,
                    )
                    return
                self._last_trigger_time[entity_id] = now
                trigger_callback(zone)

        unsub = async_track_state_change_event(
            self.hass,
            list(all_sensors),
            _sensor_state_changed,
        )
        self._unsubscribe_callbacks.append(unsub)
        _LOGGER.info("Started monitoring %d sensors", len(all_sensors))

    def stop_monitoring(self) -> None:
        for unsub in self._unsubscribe_callbacks:
            unsub()
        self._unsubscribe_callbacks.clear()
        _LOGGER.info("Stopped monitoring sensors")

    def clear_all_triggers(self) -> None:
        for zone in self._zones.values():
            zone.clear_open_sensors()
        _LOGGER.info("Cleared all zone triggers")

    def check_for_open_sensors(self) -> bool:
        """Check if any sensors are currently open. Returns True if found.

        EDGE CASE: Sensors that are unavailable/unknown are skipped (not
        counted as open). This prevents arming from being blocked by an
        offline sensor.
        """
        for zone in self._zones.values():
            if not zone.enabled:
                continue
            for sensor in zone.sensors:
                state = self.hass.states.get(sensor)
                if not state:
                    # Entity missing — skip, log warning
                    _LOGGER.warning("Sensor %s not found in HA during open sensor check", sensor)
                    continue
                if state.state in ("unavailable", "unknown"):
                    # Unavailable sensor — skip, don't block arming
                    _LOGGER.debug("Sensor %s is %s — skipping in open check", sensor, state.state)
                    continue
                if state.state in _OPEN_STATES:
                    zone.update_sensor_state(sensor, True)

        open_sensors = self.get_all_open_sensors()
        if open_sensors:
            _LOGGER.warning("Open sensors detected: %s", open_sensors)
            return True
        return False

    def get_status(self) -> dict[str, Any]:
        return {
            "total_zones": len(self._zones),
            "enabled_zones": len([z for z in self._zones.values() if z.enabled]),
            "triggered_zones": len(self.get_triggered_zones()),
            "total_sensors": len(self._sensor_to_zone),
            "open_sensors": len(self.get_all_open_sensors()),
            "zones": [zone.to_dict() for zone in self._zones.values()],
        }
