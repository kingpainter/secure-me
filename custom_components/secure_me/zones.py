"""Zone management for Secure Me."""
# VERSION = "0.3.0"

import logging
from typing import Any

from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ZONE_TYPE_ENTRY,
    ZONE_TYPE_INSTANT,
    ZONE_TYPE_INTERIOR,
    ZONE_TYPE_PERIMETER,
)

_LOGGER = logging.getLogger(__name__)


class Zone:
    """Representation of a security zone."""

    def __init__(
        self,
        zone_id: str,
        zone_type: str,
        sensors: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize zone."""
        self.zone_id = zone_id
        self.zone_type = zone_type
        self.sensors = sensors or []
        self.enabled = enabled
        self._open_sensors: list[str] = []

    @property
    def is_triggered(self) -> bool:
        """Return if zone is triggered (has open sensors)."""
        return len(self._open_sensors) > 0

    @property
    def open_sensors(self) -> list[str]:
        """Return list of open sensors."""
        return self._open_sensors.copy()

    def update_sensor_state(self, entity_id: str, is_open: bool) -> bool:
        """Update sensor state. Returns True if zone state changed."""
        was_triggered = self.is_triggered

        if is_open and entity_id not in self._open_sensors:
            self._open_sensors.append(entity_id)
        elif not is_open and entity_id in self._open_sensors:
            self._open_sensors.remove(entity_id)

        return was_triggered != self.is_triggered

    def clear_open_sensors(self) -> None:
        """Clear all open sensors."""
        self._open_sensors.clear()

    def to_dict(self) -> dict[str, Any]:
        """Return zone as dict."""
        return {
            "zone_id": self.zone_id,
            "zone_type": self.zone_type,
            "sensors": self.sensors,
            "enabled": self.enabled,
            "is_triggered": self.is_triggered,
            "open_sensors": self._open_sensors,
        }


class ZoneManager:
    """Manage security zones and sensors."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize zone manager."""
        self.hass = hass
        self._zones: dict[str, Zone] = {}
        self._sensor_to_zone: dict[str, str] = {}
        self._unsubscribe_callbacks: list = []
        self._trigger_callback = None

        _LOGGER.info("Zone manager initialized")

    def register_trigger_callback(self, callback_func) -> None:
        """Register callback for zone triggers.
        
        Args:
            callback_func: Function to call when zone is triggered.
                          Signature: callback(zone: Zone)
        """
        self._trigger_callback = callback_func
        _LOGGER.debug("Trigger callback registered")

    def add_zone(
        self,
        zone_id: str,
        zone_type: str,
        sensors: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        """Add a zone."""
        zone = Zone(zone_id, zone_type, sensors, enabled)
        self._zones[zone_id] = zone

        # Map sensors to zone
        if sensors:
            for sensor in sensors:
                self._sensor_to_zone[sensor] = zone_id

        _LOGGER.info(
            "Added zone: %s (type=%s, sensors=%d, enabled=%s)",
            zone_id,
            zone_type,
            len(sensors or []),
            enabled,
        )

    def remove_zone(self, zone_id: str) -> None:
        """Remove a zone."""
        if zone_id not in self._zones:
            return

        zone = self._zones[zone_id]

        # Remove sensor mappings
        for sensor in zone.sensors:
            self._sensor_to_zone.pop(sensor, None)

        # Remove zone
        self._zones.pop(zone_id)
        _LOGGER.info("Removed zone: %s", zone_id)

    def get_zone(self, zone_id: str) -> Zone | None:
        """Get a zone by ID."""
        return self._zones.get(zone_id)

    def get_zones(self) -> list[Zone]:
        """Get all zones."""
        return list(self._zones.values())

    def get_zone_by_sensor(self, entity_id: str) -> Zone | None:
        """Get zone for a sensor."""
        zone_id = self._sensor_to_zone.get(entity_id)
        if zone_id:
            return self._zones.get(zone_id)
        return None

    def get_triggered_zones(self) -> list[Zone]:
        """Get all triggered zones."""
        return [zone for zone in self._zones.values() if zone.is_triggered]

    def get_entry_zones(self) -> list[Zone]:
        """Get all entry zones."""
        return [
            zone
            for zone in self._zones.values()
            if zone.zone_type == ZONE_TYPE_ENTRY
        ]

    def get_instant_zones(self) -> list[Zone]:
        """Get all instant zones."""
        return [
            zone
            for zone in self._zones.values()
            if zone.zone_type == ZONE_TYPE_INSTANT
        ]

    def get_all_open_sensors(self) -> list[str]:
        """Get all open sensors from all zones."""
        open_sensors = []
        for zone in self._zones.values():
            if zone.enabled:
                open_sensors.extend(zone.open_sensors)
        return open_sensors

    def update_sensor_state(self, entity_id: str, state: State) -> tuple[bool, Zone | None]:
        """Update sensor state. Returns (zone_changed, zone)."""
        zone = self.get_zone_by_sensor(entity_id)
        if not zone or not zone.enabled:
            return False, None

        # Determine if sensor is "open" (triggered)
        is_open = state.state in ["on", "open", "detected", "unlocked"]

        # Update zone
        changed = zone.update_sensor_state(entity_id, is_open)

        if changed:
            _LOGGER.info(
                "Zone %s state changed: triggered=%s (sensor=%s, state=%s)",
                zone.zone_id,
                zone.is_triggered,
                entity_id,
                state.state,
            )

        return changed, zone

    def start_monitoring(self, callback_func=None) -> None:
        """Start monitoring sensors.
        
        Args:
            callback_func: Optional callback. If provided, overrides registered callback.
        """
        # Use provided callback or fall back to registered callback
        trigger_callback = callback_func or self._trigger_callback
        
        if not trigger_callback:
            _LOGGER.error("No trigger callback registered")
            return
        
        # Get all sensors from all zones
        all_sensors = set()
        for zone in self._zones.values():
            all_sensors.update(zone.sensors)

        if not all_sensors:
            _LOGGER.warning("No sensors to monitor")
            return

        # Subscribe to state changes
        @callback
        def _sensor_state_changed(event):
            """Handle sensor state change."""
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")

            if not new_state:
                return

            changed, zone = self.update_sensor_state(entity_id, new_state)
            if changed and zone:
                # Notify callback
                trigger_callback(zone)

        unsub = async_track_state_change_event(
            self.hass,
            list(all_sensors),
            _sensor_state_changed,
        )
        self._unsubscribe_callbacks.append(unsub)

        _LOGGER.info("Started monitoring %d sensors", len(all_sensors))

    def stop_monitoring(self) -> None:
        """Stop monitoring sensors."""
        for unsub in self._unsubscribe_callbacks:
            unsub()
        self._unsubscribe_callbacks.clear()
        _LOGGER.info("Stopped monitoring sensors")

    def clear_all_triggers(self) -> None:
        """Clear all zone triggers."""
        for zone in self._zones.values():
            zone.clear_open_sensors()
        _LOGGER.info("Cleared all zone triggers")

    def check_for_open_sensors(self) -> bool:
        """Check if any sensors are currently open. Returns True if found."""
        for zone in self._zones.values():
            if not zone.enabled:
                continue

            for sensor in zone.sensors:
                state = self.hass.states.get(sensor)
                if state and state.state in ["on", "open", "detected", "unlocked"]:
                    zone.update_sensor_state(sensor, True)

        open_sensors = self.get_all_open_sensors()
        if open_sensors:
            _LOGGER.warning("Open sensors detected: %s", open_sensors)
            return True

        return False

    def get_status(self) -> dict[str, Any]:
        """Get zone manager status."""
        return {
            "total_zones": len(self._zones),
            "enabled_zones": len([z for z in self._zones.values() if z.enabled]),
            "triggered_zones": len(self.get_triggered_zones()),
            "total_sensors": len(self._sensor_to_zone),
            "open_sensors": len(self.get_all_open_sensors()),
            "zones": [zone.to_dict() for zone in self._zones.values()],
        }
