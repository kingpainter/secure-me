"""Zone management for Secure Me."""
# VERSION = "1.5.5"

import asyncio
import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ZONE_TYPE_ENTRY,
    ZONE_TYPE_INSTANT,
    NOTIFY_ID_MODULE_ERROR,
    EVENT_READY_TO_ARM_MODES_CHANGED,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# States that mean a sensor is "open" / triggered
_OPEN_STATES = frozenset({"on", "open", "detected", "unlocked"})


# All valid arm modes
ALL_ARM_MODES = frozenset({"away", "home", "night", "vacation", "home_alone"})

# Default arm_modes if not specified (away only — safe default)
DEFAULT_ARM_MODES = ["away"]

# v1.4.3 Home Alone bugfix:
# Motion-like device_classes that must be visual-only in home_alone mode.
# The previous filter only matched device_class == "motion", which let
# occupancy/presence/mmWave sensors fall through and trigger the alarm.
# Empty/None device_class also defaults to visual-only in home_alone --
# safer to over-suppress motion-style sensors than to false-trigger.
_HOME_ALONE_MOTION_LIKE_CLASSES = frozenset({
    "motion", "occupancy", "presence", "moving", "vibration", "sound",
})

# Door/window/opening device_classes that should dispatch a notification
# (instead of triggering the alarm) in home_alone mode.
_HOME_ALONE_DOOR_LIKE_CLASSES = frozenset({"door", "window", "opening", "garage_door"})


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
        """Update this sensor's membership in the zone's open-sensor list.

        Returns True if THIS SENSOR's own open/closed status actually changed
        (added to or removed from the zone's open list) -- not whether the
        zone's aggregate `is_triggered` flag flipped.

        This distinction matters: in a zone with sensor A already open,
        sensor B newly opening still returns True here (B's own membership
        changed), even though `is_triggered` stays True -> True. Callers that
        need to react per-sensor (e.g. Home Alone door-notification dispatch,
        the deleted/unavailable-sensor edge cases in ZoneManager) rely on
        this per-sensor granularity. Using the old aggregate-only semantics
        silently dropped events for any sensor that changed state while
        another sensor in the same zone was already open/closed the same way.
        """
        was_open = entity_id in self._open_sensors
        if is_open and entity_id not in self._open_sensors:
            self._open_sensors.append(entity_id)
        elif not is_open and entity_id in self._open_sensors:
            self._open_sensors.remove(entity_id)
        now_open = entity_id in self._open_sensors
        return was_open != now_open

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

        # v1.4.3: Alarmo-style unavailable state memory.
        # When a sensor goes 'unavailable'/'unknown' we remember its prior
        # state. If it returns to that same prior state, we treat the
        # transition as a no-op flap (no trigger, no zone state change).
        # This prevents Zigbee/WiFi sensors that briefly drop offline from
        # firing spurious triggers when they reconnect in their previous
        # state -- e.g. a door that was open before going unavailable and
        # comes back as open should not register as a fresh "door opened"
        # event.
        self._unavailable_state_mem: dict[str, str] = {}

        # v1.4.3: Track which arm modes are currently "ready" (no open
        # non-bypass sensors). Frontends subscribe to
        # EVENT_READY_TO_ARM_MODES_CHANGED to enable/disable arm buttons
        # in real time. Recomputed on every sensor state change.
        self._ready_modes_cache: set[str] = set()

        # v1.4.3 Home Alone bugfix: initialise the active arm mode so the
        # _sensor_state_changed callback can rely on it being present even
        # if start_monitoring() somehow has not run yet (e.g. an early
        # state_changed event during HA restore).
        self._active_arm_mode: str | None = None

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

        # v1.4.3: (Re)start the always-on ready-modes listener whenever
        # sensor configs change. The listener watches all sensors that
        # appear in any zone so we can update arm-button readiness in real
        # time even when the alarm is disarmed and not actively monitoring.
        self._setup_ready_modes_listener()

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

    def get_auto_bypass_sensors(
        self,
        zone_sensors: list[str],
        arm_mode: str | None = None,
    ) -> list[str]:
        """Return sensors that are currently open AND have auto_bypass for arm_mode.

        Called before arming to determine which sensors to silently bypass.

        v1.4.3: per-mode bypass via `auto_bypass_modes` list.
            - If arm_mode is given AND sensor has `auto_bypass_modes` list,
              the sensor is bypassed only when arm_mode is in that list.
            - If `auto_bypass_modes` is missing/empty, fall back to the legacy
              global `auto_bypass` flag (treated as "all modes" only when the
              caller passes arm_mode=None for backwards compatibility).
            - When arm_mode is given and neither field opts in, no bypass.
        """
        bypassed = []
        for entity_id in zone_sensors:
            cfg = self._sensor_configs.get(entity_id, {})

            # v1.4.3 path: per-mode list (preferred)
            modes_list = cfg.get("auto_bypass_modes")
            opted_in = False
            if isinstance(modes_list, list) and modes_list:
                if arm_mode is None:
                    # No arm_mode context -> any opt-in counts. Defensive
                    # path; current callers always pass arm_mode.
                    opted_in = True
                else:
                    opted_in = arm_mode in modes_list
            elif arm_mode is None and cfg.get("auto_bypass", False):
                # Legacy global flag, only honoured when caller has not
                # specified a mode (preserves pre-v1.4.3 behaviour).
                opted_in = True

            # allow_open: permanent bypass — sensor altid ignoreret ved arming
            if cfg.get("allow_open", False):
                state = self.hass.states.get(entity_id)
                if state and state.state in _OPEN_STATES:
                    bypassed.append(entity_id)
                    _LOGGER.debug(
                        "allow_open sensor bypassed at arm time: %s", entity_id
                    )
                continue

            if not opted_in:
                continue

            state = self.hass.states.get(entity_id)
            if state and state.state in _OPEN_STATES:
                bypassed.append(entity_id)
                _LOGGER.info(
                    "Auto-bypassing open sensor at arm time (mode=%s): %s",
                    arm_mode or "<any>", entity_id,
                )
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

    # ── Ready-to-arm prediction (v1.4.3, Alarmo-inspired) ──────────────────

    _ALL_ARM_MODES = ("away", "home", "night", "vacation", "home_alone")

    def _compute_ready_modes(self) -> tuple[set[str], dict[str, list[str]]]:
        """Determine which arm modes can currently be entered.

        For each arm mode, simulate what async_arm_<mode> would see:
        gather sensors from all enabled zones active for that mode,
        subtract auto-bypass sensors, and check if anything is still open.

        Returns (ready_modes, blocked_modes) where:
        - ready_modes is the set of mode names that can arm cleanly
        - blocked_modes maps blocked mode names to their open sensor list
          (so frontends can show "Front door open" tooltips)
        """
        ready: set[str] = set()
        blocked: dict[str, list[str]] = {}

        for mode in self._ALL_ARM_MODES:
            mode_sensors = [
                s for z in self._zones.values()
                if z.enabled and z.is_active_for_mode(mode)
                for s in z.sensors
            ]
            if not mode_sensors:
                # No sensors -> trivially ready
                ready.add(mode)
                continue

            # v1.4.3: pass arm_mode so per-mode bypass list is respected
            bypass_set = set(self.get_auto_bypass_sensors(mode_sensors, arm_mode=mode))
            # allow_open sensorer er altid bypassed -- tilfoej dem til bypass_set
            allow_open_set = {
                s for s in mode_sensors
                if self._sensor_configs.get(s, {}).get("allow_open", False)
            }
            bypass_set |= allow_open_set
            blocking = []
            for sensor_id in mode_sensors:
                if sensor_id in bypass_set:
                    continue
                state = self.hass.states.get(sensor_id)
                if not state:
                    continue
                if state.state in ("unavailable", "unknown"):
                    continue  # treated as closed in arm path
                if state.state in _OPEN_STATES:
                    blocking.append(sensor_id)

            if blocking:
                blocked[mode] = blocking
            else:
                ready.add(mode)

        return ready, blocked

    def _check_ready_modes_changed(self) -> None:
        """Recompute ready modes; fire event if changed.

        Called on every sensor state change. Cached previous result is
        compared against the new result; event only fires on actual
        change to avoid event spam.
        """
        try:
            new_ready, new_blocked = self._compute_ready_modes()
        except Exception as err:
            # Defensive: never let ready-mode computation break the
            # state-change handler. Log and continue.
            _LOGGER.debug("ready_modes computation failed: %s", err)
            return

        if new_ready == self._ready_modes_cache:
            return

        added = sorted(new_ready - self._ready_modes_cache)
        removed = sorted(self._ready_modes_cache - new_ready)
        _LOGGER.debug(
            "Ready modes changed: +%s -%s (now %s)",
            added, removed, sorted(new_ready),
        )
        self._ready_modes_cache = new_ready

        self.hass.bus.async_fire(EVENT_READY_TO_ARM_MODES_CHANGED, {
            "ready_modes": sorted(new_ready),
            "blocked_modes": new_blocked,
        })

    def _setup_ready_modes_listener(self) -> None:
        """Subscribe to state changes for all sensors used in any zone.

        Always-on listener (active even while alarm is disarmed) so the
        ready-to-arm prediction can be kept fresh. Re-creates the
        subscription each time sensor configs are loaded so we cover any
        newly added sensors and drop removed ones.
        """
        # Tear down any previous ready-modes listener
        unsub = getattr(self, "_ready_modes_unsub", None)
        if unsub:
            try:
                unsub()
            except Exception:
                pass
            self._ready_modes_unsub = None

        # Build the watched set from all enabled-zone sensors
        watched: set[str] = set()
        for zone in self._zones.values():
            if zone.enabled:
                watched.update(zone.sensors)
        if not watched:
            return

        from homeassistant.helpers.event import async_track_state_change_event

        @callback
        def _on_state_change(event):
            self._check_ready_modes_changed()

        self._ready_modes_unsub = async_track_state_change_event(
            self.hass, list(watched), _on_state_change
        )

        # Compute baseline so the first real change can be diffed
        try:
            ready, _ = self._compute_ready_modes()
            self._ready_modes_cache = ready
        except Exception:
            self._ready_modes_cache = set()

        _LOGGER.debug(
            "Ready-modes listener subscribed to %d sensors", len(watched)
        )

    # ── State update ────────────────────────────────────────────────────────────────────

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
        # v1.4.2: Zigbee/WiFi sensors routinely flap to 'unavailable' for a few
        # seconds (battery radio, mesh restarts, router reboots). Logging these
        # as WARNING + firing a persistent notification every time drowns real
        # issues in noise. Degrade to DEBUG and drop the notification. Sensors
        # that are permanently dead will show up as 'unavailable' in the HA UI
        # and via the diagnostics sensor -- no need for per-event alerts here.
        #
        # v1.4.3: Remember the prior state so we can detect "flap to
        # unavailable and back to the same state" as a no-op rather than as a
        # state change. The actual flap-detection happens in
        # async_sensor_state_changed where we have access to old_state.
        if state.state in ("unavailable", "unknown"):
            _LOGGER.debug(
                "Sensor %s is %s while monitoring active -- treating as closed",
                entity_id, state.state,
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

            # v1.4.3: Alarmo-style flap detection.
            # Track prior state when going to unavailable. When coming back,
            # if we land on the same state we had before, it was just a
            # connection blip -- skip the rest of the handler so we don't
            # fire spurious triggers (e.g. a door that was already 'on'
            # before the radio dropped should not register as a fresh open).
            new_raw = new_state.state if new_state else None
            old_raw = old_state.state if old_state else None

            if new_raw in ("unavailable", "unknown") and old_raw not in ("unavailable", "unknown", None):
                # Sensor is going offline -- remember where it was.
                self._unavailable_state_mem[entity_id] = old_raw
            elif entity_id in self._unavailable_state_mem and old_raw in ("unavailable", "unknown"):
                # Sensor is coming back online -- check if it landed on its
                # prior state. If so, swallow this transition entirely.
                prior = self._unavailable_state_mem.pop(entity_id)
                if prior == new_raw:
                    _LOGGER.debug(
                        "Sensor %s flapped %s -> %s -> %s, ignoring",
                        entity_id, prior, old_raw, new_raw,
                    )
                    return

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
            # v1.4.3 bugfix: Home Alone mode is supervisory only -- it is
            # designed for when a child or vulnerable person is alone at
            # home with cameras live and motion visible, but the alarm
            # must NOT trigger from interior motion. Previously only the
            # exact device_class == "motion" was suppressed; occupancy,
            # presence, mmWave and untyped sensors fell through to the
            # normal trigger path and rang the alarm. Two changes:
            #   1. Use a broader motion-like class set (occupancy, etc.)
            #   2. Default-deny: anything that is NOT a known door/window
            #      sensor is treated as visual-only. This is the safer
            #      direction in this specific mode -- a missed-but-quiet
            #      sensor is fine, a false alarm with a child home is not.
            if self._active_arm_mode == "home_alone":
                ha_state = self.hass.states.get(entity_id)
                device_class = (
                    (ha_state.attributes.get("device_class") or "").lower()
                    if ha_state else ""
                )
                sensor_name = (
                    ha_state.attributes.get("friendly_name", entity_id) if ha_state else entity_id
                )

                # Door / window / opening: dispatch the action notification
                # (camera snapshot + push action buttons + TTS) but do NOT
                # trigger the alarm.
                if device_class in _HOME_ALONE_DOOR_LIKE_CLASSES:
                    # v1.5.0 bugfix: this branch used to dispatch (camera
                    # snapshot + push + TTS) on every single trigger with no
                    # debounce at all -- unlike the normal trigger path below,
                    # which suppresses rapid re-fires per sensor. A door that
                    # rattles in the wind or has a bouncy contact sensor could
                    # spam pushes/TTS repeatedly. Reuse the same anti-flap
                    # debounce window used everywhere else in this file.
                    now = time.monotonic()
                    last = self._last_trigger_time.get(entity_id, 0.0)
                    if now - last < self._debounce_interval:
                        _LOGGER.debug(
                            "Home Alone: door sensor %s debounced (%.3fs since last dispatch)",
                            entity_id, now - last,
                        )
                        return
                    self._last_trigger_time[entity_id] = now

                    sensor_cfg = self.get_home_alone_sensor_config(entity_id)
                    # Remember this trigger's context so a tap on either of
                    # the two push-notification quick-response buttons
                    # (EVENT_HOME_ALONE_ACTION_1/2) knows which door/speaker
                    # it belongs to. Mobile-app action-button taps only echo
                    # back the action id, not the original notification
                    # payload, so this has to be tracked out-of-band.
                    self.hass.data.setdefault(DOMAIN, {})["_last_home_alone_trigger"] = {
                        "entity_id": entity_id,
                        "sensor_cfg": sensor_cfg,
                        "timestamp": time.monotonic(),
                    }
                    from .notification_dispatcher import dispatch_home_alone_door_trigger
                    self.hass.async_create_task(
                        dispatch_home_alone_door_trigger(
                            self.hass, entity_id, sensor_name, sensor_cfg
                        )
                    )
                    _LOGGER.info(
                        "Home Alone: door sensor %s (device_class=%s) opened -- notification dispatched, no alarm",
                        entity_id, device_class or "<none>",
                    )
                    return

                # Motion-like or untyped sensor: visual-only, no trigger.
                # Logged at INFO so it is visible in the HA log when this
                # filter actually fires -- DEBUG was too quiet to verify.
                if device_class in _HOME_ALONE_MOTION_LIKE_CLASSES or not device_class:
                    _LOGGER.info(
                        "Home Alone: %s (device_class=%s) activated -- visual only, no alarm trigger",
                        entity_id, device_class or "<none>",
                    )
                    return

                # Any other device_class (e.g. smoke, gas, water_leak):
                # do NOT suppress -- safety sensors must still trigger.
                # Fall through to the normal trigger path below.
                _LOGGER.info(
                    "Home Alone: %s (device_class=%s) is not motion/door -- falling through to alarm trigger",
                    entity_id, device_class,
                )
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
            # v1.4.2: trigger_callback is async (SecureMeCoordinator._zone_triggered).
            # Schedule as task so it actually runs -- calling it directly just
            # creates an unawaited coroutine and logs a RuntimeWarning.
            result = trigger_callback(zone)
            if asyncio.iscoroutine(result):
                self.hass.async_create_task(result)

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

    def cleanup(self) -> None:
        """Full teardown including always-on listeners (v1.4.3).

        Called from coordinator.async_shutdown(). stop_monitoring() only
        cancels armed-state subscriptions; this also tears down the
        ready-modes listener that runs even while disarmed.
        """
        self.stop_monitoring()
        unsub = getattr(self, "_ready_modes_unsub", None)
        if unsub:
            try:
                unsub()
            except Exception:
                pass
            self._ready_modes_unsub = None

    def clear_all_triggers(self) -> None:
        for zone in self._zones.values():
            zone.clear_open_sensors()
        self.reset_sensor_groups()
        _LOGGER.info("Cleared all zone triggers")

    def check_for_open_sensors(
        self,
        bypass_list: list[str] | None = None,
        arm_mode: str | None = None,
    ) -> bool:
        """Check if any sensors are currently open.

        Returns True if open (non-bypassed) sensors found.
        bypass_list: sensors to skip (auto_bypass candidates).
        arm_mode: when given, only zones active for this mode are checked.
                  Prevents sensors in away-only zones from blocking a
                  home/night/home_alone arm attempt.
        """
        bypass = set(bypass_list or [])
        for zone in self._zones.values():
            if not zone.enabled:
                continue
            if arm_mode and not zone.is_active_for_mode(arm_mode):
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