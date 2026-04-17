"""Zone management for Secure Me."""
# VERSION = "1.4.0"

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


# All valid arm modes
ALL_ARM_MODES = frozenset({"away", "home", "night", "vacation", "home_alone"})

# Default arm_modes if not specified (away only — safe default)
DEFAULT_ARM_MODES = ["away"]


class Zone:
    """Representation of a security zone."""

    def __init__(
        self,
        zone_id: str,
        zone_type: str,
        sensors: list[str] | None = None,
        enabled: bool = True,
        arm_modes: list[str] | None = None,
    ) -> None:
        self.zone_id = zone_id
        self.zone_type = zone_type
        self.sensors = sensors or []
        self.enabled = enabled
        self.arm_modes: list[str] = arm_modes if arm_modes else list(DEFAULT_ARM_MODES)
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

    def is_active_for_mode(self, arm_mode: str) -> bool:
        """Return True if this zone should be active for the given arm mode."""
        return arm_mode in self.arm_modes

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "zone_type": self.zone_type,
            "sensors": self.sensors,
            "enabled": self.enabled,
            "arm_modes": self.arm_modes,
            "is_triggered": self.is_triggered,
            "open_sensors": self._open_sensors,
        }


class SensorGroup:
    """Anti-masking sensor group.

    Only triggers if at least `event_count` sensors activate within
    `timeout` seconds of each other. A timeout of 0 disables the window
    (all sensors must activate regardless of timing).

    Inspired by Alarmo's SensorGroupEntry.
    """

    def __init__(
        self,
        group_id: str,
        name: str,
        entities: list[str],
        timeout: int = 0,
        event_count: int = 2,
    ) -> None:
        self.group_id = group_id
        self.name = name
        self.entities = list(entities)
        self.timeout = timeout
        self.event_count = event_count
        # (entity_id -> monotonic timestamp) of recent activations
        self._activations: dict[str, float] = {}

    def record_activation(self, entity_id: str) -> bool:
        """Record a sensor activation and return True if group threshold is met.

        Cleans up stale activations outside the timeout window first.
        If timeout == 0: all activations count regardless of timing.
        """
        now = time.monotonic()
        self._activations[entity_id] = now

        if self.timeout > 0:
            # Remove activations outside the time window
            cutoff = now - self.timeout
            self._activations = {
                eid: ts for eid, ts in self._activations.items()
                if ts >= cutoff
            }

        active_count = len(self._activations)
        _LOGGER.debug(
            "Sensor group '%s': %d/%d activations (timeout=%ds)",
            self.group_id, active_count, self.event_count, self.timeout,
        )
        return active_count >= self.event_count

    def reset(self) -> None:
        """Clear all activation records."""
        self._activations.clear()


class ZoneManager:
    """Manage security zones, sensors, and sensor groups.

    v1.2.0 additions:
    - SensorGroup anti-masking: only trigger if N sensors fire within window
    - Per-sensor auto_bypass: open sensors at arm time are bypassed automatically
    - Per-sensor arm_on_close: auto-arm when sensor closes
    - Per-sensor entry_delay override: passed back to caller via trigger callback

    v0.5.0 edge case fixes (retained):
    - Sensor unavailable while armed: logged + notified, treated as closed
    - Sensor deleted while armed: gracefully ignored, warning logged
    - Sensor removed from HA while armed: mapping cleaned up, user notified
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._zones: dict[str, Zone] = {}
        self._sensor_to_zone: dict[str, str] = {}
        self._unsubscribe_callbacks: list = []
        self._trigger_callback = None
        self._arm_on_close_callback = None  # called when arm_on_close sensor closes

        # Sensor configs keyed by entity_id (loaded from store at arm time)
        self._sensor_configs: dict[str, dict[str, Any]] = {}

        # Sensor groups for anti-masking
        self._sensor_groups: dict[str, SensorGroup] = {}

        # PERF v0.6.0: Debounce per-sensor to suppress flapping.
        self._last_trigger_time: dict[str, float] = {}
        self._debounce_interval: float = 0.5

        _LOGGER.info("Zone manager initialized")

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def zones(self) -> dict[str, Zone]:
        return self._zones

    def register_trigger_callback(self, callback_func) -> None:
        self._trigger_callback = callback_func

    def register_arm_on_close_callback(self, callback_func) -> None:
        """Register callback for arm_on_close events."""
        self._arm_on_close_callback = callback_func

    # ── Sensor configs ──────────────────────────────────────────────────────

    def load_sensor_configs(self, configs: dict[str, dict[str, Any]]) -> None:
        """Load per-sensor configs (entry_delay, auto_bypass, arm_on_close, home_alone fields)."""
        self._sensor_configs = configs
        _LOGGER.debug("Loaded %d sensor configs", len(configs))

    def get_sensor_entry_delay(self, entity_id: str, zone_default: int) -> int:
        """Return per-sensor entry_delay if configured, else zone default."""
        cfg = self._sensor_configs.get(entity_id, {})
        override = cfg.get("entry_delay")
        if override is not None:
            try:
                return int(override)
            except (TypeError, ValueError):
                pass
        return zone_default

    def get_home_alone_sensor_config(self, entity_id: str) -> dict[str, Any]:
        """Return Home Alone specific config for a sensor.

        Returns a dict with keys:
          home_alone_camera   — entity_id of camera to snapshot (str | None)
          home_alone_tts_speaker — entity_id of TTS media_player (str | None)
          home_alone_action_1 — text for push action button 1 (str)
          home_alone_action_2 — text for push action button 2 (str)
        """
        from .const import (
            CONF_HOME_ALONE_CAMERA,
            CONF_HOME_ALONE_SPEAKER,
            CONF_HOME_ALONE_ACTION_1,
            CONF_HOME_ALONE_ACTION_2,
            HOME_ALONE_DEFAULT_ACTION_1,
            HOME_ALONE_DEFAULT_ACTION_2,
        )
        cfg = self._sensor_configs.get(entity_id, {})
        return {
            CONF_HOME_ALONE_CAMERA:  cfg.get(CONF_HOME_ALONE_CAMERA),
            CONF_HOME_ALONE_SPEAKER: cfg.get(CONF_HOME_ALONE_SPEAKER),
            CONF_HOME_ALONE_ACTION_1: cfg.get(CONF_HOME_ALONE_ACTION_1, HOME_ALONE_DEFAULT_ACTION_1),
            CONF_HOME_ALONE_ACTION_2: cfg.get(CONF_HOME_ALONE_ACTION_2, HOME_ALONE_DEFAULT_ACTION_2),
        }

    def get_auto_bypass_sensors(self, zone_sensors: list[str]) -> list[str]:
        """Return sensors that are currently open AND have auto_bypass=True.

        Called before arming to determine which sensors to silently bypass.
        """
        bypassed = []
        for entity_id in zone_sensors:
            cfg = self._sensor_configs.get(entity_id, {})
            if not cfg.get("auto_bypass", False):
                continue
            state = self.hass.states.get(entity_id)
            if state and state.state in _OPEN_STATES:
                bypassed.append(entity_id)
                _LOGGER.info("Auto-bypassing open sensor at arm time: %s", entity_id)
        return bypassed

    # ── Sensor groups ───────────────────────────────────────────────────────

    def load_sensor_groups(self, groups: dict[str, dict[str, Any]]) -> None:
        """Load sensor group definitions from store data."""
        self._sensor_groups = {}
        for gid, gdata in groups.items():
            self._sensor_groups[gid] = SensorGroup(
                group_id=gid,
                name=gdata.get("name", ""),
                entities=gdata.get("entities", []),
                timeout=int(gdata.get("timeout", 0)),
                event_count=int(gdata.get("event_count", 2)),
            )
        _LOGGER.info("Loaded %d sensor groups", len(self._sensor_groups))

    def _get_group_for_sensor(self, entity_id: str) -> SensorGroup | None:
        """Return the SensorGroup this sensor belongs to, or None."""
        for group in self._sensor_groups.values():
            if entity_id in group.entities:
                return group
        return None

    def reset_sensor_groups(self) -> None:
        """Clear all sensor group activation records (call on disarm)."""
        for group in self._sensor_groups.values():
            group.reset()

    # ── Zone CRUD ───────────────────────────────────────────────────────────

    def add_zone(
        self,
        zone_id: str,
        zone_type: str,
        sensors: list[str] | None = None,
        enabled: bool = True,
        arm_modes: list[str] | None = None,
    ) -> None:
        zone = Zone(zone_id, zone_type, sensors, enabled, arm_modes)
        self._zones[zone_id] = zone
        if sensors:
            for sensor in sensors:
                self._sensor_to_zone[sensor] = zone_id
        _LOGGER.info(
            "Added zone: %s (type=%s, sensors=%d, enabled=%s, arm_modes=%s)",
            zone_id, zone_type, len(sensors or []), enabled, zone.arm_modes,
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

    # ── State update ────────────────────────────────────────────────────────

    def update_sensor_state(
        self, entity_id: str, state: State
    ) -> tuple[bool, Zone | None]:
        """Update sensor state.

        Returns (changed, zone) where zone is non-None only when the zone
        became triggered (useful for triggering alarm logic).
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
            try:
                from homeassistant.components.persistent_notification import (
                    async_create as pn_create,
                )
                pn_create(
                    self.hass,
                    message=(
                        f"Sensor '{entity_id}' in zone '{zone.zone_id}' has disappeared "
                        f"from Home Assistant. Check if the device is still connected."
                    ),
                    title="Secure Me - Sensor Missing",
                    notification_id=(
                        f"{NOTIFY_ID_MODULE_ERROR}_sensor_{entity_id.replace('.', '_')}"
                    ),
                )
            except Exception:
                pass
            changed = zone.update_sensor_state(entity_id, False)
            return changed, zone if changed else None

        # EDGE CASE: unavailable/unknown
        if state.state in ("unavailable", "unknown"):
            _LOGGER.warning(
                "Sensor %s is %s while monitoring active — treating as closed",
                entity_id, state.state,
            )
            try:
                from homeassistant.components.persistent_notification import (
                    async_create as pn_create,
                )
                pn_create(
                    self.hass,
                    message=(
                        f"Sensor '{entity_id}' in zone '{zone.zone_id}' is {state.state}. "
                        f"Please check the device connection."
                    ),
                    title="Secure Me - Sensor Unavailable",
                    notification_id=(
                        f"{NOTIFY_ID_MODULE_ERROR}_unavail_{entity_id.replace('.', '_')}"
                    ),
                )
            except Exception:
                pass
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

    # ── Monitoring ──────────────────────────────────────────────────────────

    def start_monitoring(self, callback_func=None, arm_mode: str = "away") -> None:
        """Start monitoring sensors for a specific arm mode.

        Only zones that include the given arm_mode in their arm_modes list
        are activated. v1.2.0: Also tracks arm_on_close sensors regardless
        of zone assignment.
        """
        self._active_arm_mode = arm_mode
        trigger_callback = callback_func or self._trigger_callback
        if not trigger_callback:
            _LOGGER.error("No trigger callback registered")
            return

        all_sensors: set[str] = set()
        for zone in self._zones.values():
            if not zone.enabled:
                continue
            if not zone.is_active_for_mode(arm_mode):
                _LOGGER.debug(
                    "Zone %s skipped — not active for mode '%s' (arm_modes=%s)",
                    zone.zone_id, arm_mode, zone.arm_modes,
                )
                continue
            all_sensors.update(zone.sensors)

        _LOGGER.info(
            "Monitoring %d sensors for arm_mode='%s'",
            len(all_sensors), arm_mode,
        )

        # Also monitor arm_on_close sensors even if not yet in a zone
        for eid, cfg in self._sensor_configs.items():
            if cfg.get("arm_on_close", False):
                all_sensors.add(eid)

        if not all_sensors:
            _LOGGER.warning("No sensors to monitor")
            return

        @callback
        def _sensor_state_changed(event):
            """Handle sensor state change event."""
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")
            old_state = event.data.get("old_state")

            # arm_on_close: sensor transitioned from open -> closed
            cfg = self._sensor_configs.get(entity_id, {})
            if cfg.get("arm_on_close", False) and old_state and new_state:
                was_open = old_state.state in _OPEN_STATES
                is_closed = new_state.state not in _OPEN_STATES and new_state.state not in (
                    "unavailable", "unknown"
                )
                if was_open and is_closed and self._arm_on_close_callback:
                    _LOGGER.info(
                        "arm_on_close triggered by %s (was open, now closed)", entity_id
                    )
                    self.hass.async_create_task(self._arm_on_close_callback(entity_id))

            changed, zone = self.update_sensor_state(entity_id, new_state)
            if not changed or not zone or not zone.is_triggered:
                return

            # ── Home Alone mode: special sensor behaviour ─────────────────
            # Motion sensors: visual-only, no alarm trigger.
            # Door/contact sensors: dispatch action notification, no alarm trigger.
            if self._active_arm_mode == "home_alone":
                ha_state = self.hass.states.get(entity_id)
                device_class = (
                    ha_state.attributes.get("device_class", "") if ha_state else ""
                )
                sensor_name = (
                    ha_state.attributes.get("friendly_name", entity_id) if ha_state else entity_id
                )

                if device_class == "motion":
                    # Motion is visual-only in Home Alone mode — no trigger
                    _LOGGER.debug(
                        "Home Alone: motion sensor %s activated (visual only, no trigger)",
                        entity_id,
                    )
                    return

                # Door/contact sensor — dispatch action notification
                if device_class in ("door", "window", "opening"):
                    sensor_cfg = self.get_home_alone_sensor_config(entity_id)
                    from .notification_dispatcher import dispatch_home_alone_door_trigger
                    self.hass.async_create_task(
                        dispatch_home_alone_door_trigger(
                            self.hass, entity_id, sensor_name, sensor_cfg
                        )
                    )
                    _LOGGER.info(
                        "Home Alone: door sensor %s opened — notification dispatched",
                        entity_id,
                    )
                    return  # No alarm trigger in home_alone mode
            # ── End Home Alone special handling ───────────────────────────

            # Sensor group anti-masking check
            group = self._get_group_for_sensor(entity_id)
            if group is not None:
                threshold_met = group.record_activation(entity_id)
                if not threshold_met:
                    _LOGGER.info(
                        "Sensor group '%s': activation from %s recorded but threshold "
                        "not yet met (%d/%d within %ds)",
                        group.group_id, entity_id,
                        len(group._activations), group.event_count, group.timeout,
                    )
                    return  # do not fire trigger yet

            # Debounce rapid state changes per sensor
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
        self.reset_sensor_groups()
        _LOGGER.info("Cleared all zone triggers")

    def check_for_open_sensors(self, bypass_list: list[str] | None = None) -> bool:
        """Check if any sensors are currently open.

        Returns True if open (non-bypassed) sensors found.
        bypass_list: sensors to skip (auto_bypass candidates).
        """
        bypass = set(bypass_list or [])
        for zone in self._zones.values():
            if not zone.enabled:
                continue
            for sensor in zone.sensors:
                if sensor in bypass:
                    continue
                state = self.hass.states.get(sensor)
                if not state:
                    _LOGGER.warning("Sensor %s not found in HA during open sensor check", sensor)
                    continue
                if state.state in ("unavailable", "unknown"):
                    _LOGGER.debug("Sensor %s is %s — skipping in open check", sensor, state.state)
                    continue
                if state.state in _OPEN_STATES:
                    zone.update_sensor_state(sensor, True)

        open_sensors = [s for s in self.get_all_open_sensors() if s not in bypass]
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
            "sensor_groups": len(self._sensor_groups),
            "zones": [zone.to_dict() for zone in self._zones.values()],
        }
