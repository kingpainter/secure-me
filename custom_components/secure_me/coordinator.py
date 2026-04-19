"""DataUpdateCoordinator for Secure Me with state machine and zones."""
# VERSION = "1.4.1"

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    STATE_MACHINE_UPDATE_INTERVAL,
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    CONF_CODE,
    CONF_EXIT_DELAY,
    CONF_ENTRY_DELAY,
    CONF_TRIGGER_TIME,
    DEFAULT_TRIGGER_TIME,
    MODULE_CAMERA,
    MODULE_LOCK,
    MODULE_LIGHTS,
    MODULE_CLIMATE,
    MODULE_SIREN,
    MODULE_TTS,
    EVENT_ALARM_ARMED,
    EVENT_ALARM_DISARMED,
    EVENT_ALARM_TRIGGERED,
    EVENT_MODULE_ENABLED,
    EVENT_MODULE_DISABLED,
    EVENT_MODULE_ERROR,
    CONF_FAKE_PRESENCE,
    NOTIFY_ID_FAKE_PRESENCE,
    FAKE_PRESENCE_ON_EN,
    FAKE_PRESENCE_OFF_EN,
    EVENT_FAKE_PRESENCE_CHANGED,
    # v1.2.0: push notification action constants
    PUSH_EVENT,
    PUSH_EVENT_ACTIONS,
    EVENT_ACTION_FORCE_ARM,
    EVENT_ACTION_RETRY_ARM,
    EVENT_ACTION_DISARM,
    EVENT_ACTION_ARM_AWAY,
    EVENT_ACTION_ARM_HOME,
    EVENT_ACTION_ARM_NIGHT,
    EVENT_ACTION_ARM_VACATION,
    EVENT_ACTION_ARM_HOME_ALONE,
    STATE_ALARM_ARMED_HOME_ALONE,
    # v1.4.0: presence-based auto-arm
    AUTO_ARM_AWAY_DELAY,
    AUTO_ARM_PUSH_TITLE,
    AUTO_ARM_PUSH_MESSAGE,
)
from .state_machine import AlarmStateMachine
from .zones import ZoneManager
from .module_manager import ModuleManager
from .modules import (
    CameraModule,
    ClimateModule,
    LightsModule,
    LockModule,
    SirenModule,
    TTSModule,
)

_LOGGER = logging.getLogger(__name__)


def _normalize_coordinator_config(module_id: str, config: dict) -> dict:
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


class PresenceMonitor:
    """Monitor person trackers and auto-arm when all residents leave home.

    Flow:
      1. Loaded at coordinator startup via async_setup() after store is ready.
      2. Listens for state_changed events on all user person_entity entries.
      3. When ALL tracked users are away: starts a countdown (AUTO_ARM_AWAY_DELAY).
      4. If someone returns before the countdown expires: timer is cancelled.
      5. On countdown expiry, if alarm is still disarmed:
           - Lock module: lock all configured locks.
           - Alarm: arm_away (respects Fake Presence block).
           - Camera module activates automatically as part of arm_away.
           - Push notification sent to all users.

    Note on field name: the store persists the person entity under two possible
    keys depending on when the user profile was created. `person_entity` is the
    canonical name used by the frontend (secure-me-panel.js); `tracker_entity`
    existed as a design name in early drafts. We read both for compatibility -
    `person_entity` takes precedence.
    """

    def __init__(self, hass: HomeAssistant, coordinator: "SecureMeCoordinator") -> None:
        self.hass = hass
        self._coordinator = coordinator
        self._unsubs: list = []
        self._away_timer: asyncio.Task | None = None
        self._tracker_entities: set[str] = set()

    def async_setup(self) -> None:
        """Discover tracker entities from user profiles and start listening.

        Safe to call multiple times: existing listeners and tracker set are
        cleared first so this doubles as a refresh path for async_refresh().
        """
        # Clear previous subscriptions so re-invocation does not register
        # duplicate listeners for the same entities.
        for unsub in self._unsubs:
            try:
                unsub()
            except Exception:
                pass
        self._unsubs.clear()
        self._tracker_entities.clear()

        store = getattr(self._coordinator, "store", None)
        if not store:
            _LOGGER.warning("PresenceMonitor: store not ready at setup")
            return

        for user in store.get_users().values():
            if not user.get("enabled", True):
                continue
            # Read `person_entity` first (canonical name used by frontend) and fall
            # back to `tracker_entity` for any legacy profiles that might exist.
            tracker = user.get("person_entity") or user.get("tracker_entity", "")
            if tracker:
                self._tracker_entities.add(tracker)

        if not self._tracker_entities:
            _LOGGER.info("PresenceMonitor: No tracker entities configured - auto-arm disabled")
            return

        _LOGGER.info(
            "PresenceMonitor: Watching %d tracker(s): %s",
            len(self._tracker_entities),
            ", ".join(sorted(self._tracker_entities)),
        )

        from homeassistant.helpers.event import async_track_state_change_event
        unsub = async_track_state_change_event(
            self.hass,
            list(self._tracker_entities),
            self._on_tracker_state_changed,
        )
        self._unsubs.append(unsub)

    def async_refresh(self) -> None:
        """Rebuild tracker subscriptions after user profile changes.

        Call this from user save/delete handlers so person_entity edits
        take effect without requiring a Home Assistant restart. Any pending
        auto-arm countdown is cancelled since the tracked set may have
        changed semantically.
        """
        self._cancel_timer()
        self.async_setup()

    def async_teardown(self) -> None:
        """Unsubscribe listeners and cancel pending timer."""
        for unsub in self._unsubs:
            try:
                unsub()
            except Exception:
                pass
        self._unsubs.clear()
        self._cancel_timer()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _all_away(self) -> bool:
        """Return True if every tracked person is currently not_home."""
        if not self._tracker_entities:
            return False
        for entity_id in self._tracker_entities:
            state = self.hass.states.get(entity_id)
            if state is None:
                continue
            if state.state in ("home", "unavailable", "unknown"):
                return False
        return True

    def _cancel_timer(self) -> None:
        if self._away_timer and not self._away_timer.done():
            self._away_timer.cancel()
        self._away_timer = None

    @callback
    def _on_tracker_state_changed(self, event) -> None:
        """React to person tracker state changes."""
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        new_val = new_state.state
        _LOGGER.debug("PresenceMonitor: %s -> %s", entity_id, new_val)

        if new_val == "home":
            # Someone returned — cancel countdown
            if self._away_timer:
                _LOGGER.info(
                    "PresenceMonitor: %s returned home — auto-arm timer cancelled", entity_id
                )
                self._cancel_timer()
            return

        # Person left - check if everyone is now away
        if self._all_away() and self._away_timer is None:
            # Fake Presence blocks the entire auto-arm flow (locks + arm).
            # User preference (option C): when Fake Presence is on, nothing
            # auto-runs regardless of tracker state - e.g. user doing laundry
            # while running errands.
            if self._coordinator.fake_presence:
                _LOGGER.info(
                    "PresenceMonitor: All residents away but Fake Presence active - auto-arm suppressed"
                )
                return

            _LOGGER.info(
                "PresenceMonitor: All residents away - starting %ds auto-arm countdown",
                AUTO_ARM_AWAY_DELAY,
            )
            self._away_timer = asyncio.ensure_future(
                self._auto_arm_countdown()
            )

    async def _auto_arm_countdown(self) -> None:
        """Wait AUTO_ARM_AWAY_DELAY seconds then execute auto-arm sequence."""
        try:
            await asyncio.sleep(AUTO_ARM_AWAY_DELAY)
        except asyncio.CancelledError:
            _LOGGER.info("PresenceMonitor: Auto-arm countdown cancelled")
            return
        finally:
            self._away_timer = None

        # Double-check: re-verify everyone is still away
        if not self._all_away():
            _LOGGER.info("PresenceMonitor: Someone returned during countdown — aborting")
            return

        # Only act if alarm is currently disarmed
        if self._coordinator.state_machine.is_armed or self._coordinator.state_machine.is_arming:
            _LOGGER.info("PresenceMonitor: Alarm already armed — no action needed")
            return

        _LOGGER.info("PresenceMonitor: Auto-arm sequence starting")
        await self._execute_auto_arm()

    async def _execute_auto_arm(self) -> None:
        """Lock locks, arm alarm, then notify all users.

        Fake Presence is re-checked at the top: if it was enabled during the
        countdown window (or raced with this expiry), the entire sequence is
        skipped - no locking, no arming, no notification.
        """
        from .notification_dispatcher import send_auto_arm_notification

        # Fake Presence short-circuit: skip locks AND arm. Matches user pref
        # (option C): nothing auto-runs while Fake Presence is active.
        if self._coordinator.fake_presence:
            _LOGGER.info(
                "PresenceMonitor: _execute_auto_arm aborted - Fake Presence active"
            )
            return

        actions_taken: list[str] = []

        # 1. Lock all configured locks
        lock_module = self._coordinator.modules.get("lock")
        if lock_module and lock_module.enabled:
            lock_entities = getattr(lock_module, "locks", [])
            for lock_entity in lock_entities:
                state = self.hass.states.get(lock_entity)
                if state and state.state == "unlocked":
                    try:
                        await self.hass.services.async_call(
                            "lock", "lock",
                            {"entity_id": lock_entity},
                            blocking=False,
                        )
                        actions_taken.append(f"Lock locked: {lock_entity}")
                        _LOGGER.info("PresenceMonitor: Locked %s", lock_entity)
                    except Exception as err:
                        _LOGGER.error("PresenceMonitor: Failed to lock %s: %s", lock_entity, err)

        # 2. Arm alarm in away mode (auto=True respects Fake Presence block)
        arm_success = await self._coordinator.async_arm_away(auto=True)
        if arm_success:
            actions_taken.append("Alarm armed (away) — cameras activated")
            _LOGGER.info("PresenceMonitor: Alarm armed successfully")
        else:
            _LOGGER.warning(
                "PresenceMonitor: arm_away returned False "
                "(Fake Presence active or sensors open)"
            )
            actions_taken.append("Alarm arm skipped (Fake Presence active or open sensors)")

        # 3. Notify all users
        await send_auto_arm_notification(
            self.hass,
            AUTO_ARM_PUSH_TITLE,
            AUTO_ARM_PUSH_MESSAGE,
            actions_taken,
        )


class SecureMeCoordinator(DataUpdateCoordinator):
    """Secure Me coordinator with state machine and zone management."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=STATE_MACHINE_UPDATE_INTERVAL),
        )

        self.config_entry = config_entry
        self.modules: dict[str, Any] = {}
        self._armed_by: str | None = None
        self._disarmed_by: str | None = None
        self._armed_by_id: str | None = None
        self._disarmed_by_id: str | None = None
        self._triggered_by: str | None = None
        self._last_arm_mode: str | None = None  # v1.2.0: remembered for push force-arm

        self._code = config_entry.data.get(CONF_CODE, "")
        exit_delay = config_entry.data.get(CONF_EXIT_DELAY, 30)
        entry_delay = config_entry.data.get(CONF_ENTRY_DELAY, 30)
        trigger_time = config_entry.data.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME)

        self.state_machine = AlarmStateMachine(
            hass,
            exit_delay=exit_delay,
            entry_delay=entry_delay,
            trigger_time=trigger_time,
        )

        self.zone_manager = ZoneManager(hass)
        self.zone_manager.register_trigger_callback(self._zone_triggered)
        self.zone_manager.register_arm_on_close_callback(self._arm_on_close_triggered)

        self._init_modules()

        self.state_machine.add_state_change_callback(self._state_changed)
        self.state_machine.add_countdown_callback(self._countdown_updated)

        # v1.2.0: Register push notification listener
        self._push_unsub = hass.bus.async_listen(
            PUSH_EVENT, self._handle_push_event
        )

        # Scheduled test runner — checks every minute
        from homeassistant.helpers.event import async_track_time_interval
        self._scheduled_test_unsub = async_track_time_interval(
            hass, self._check_scheduled_tests, timedelta(minutes=1)
        )

        _LOGGER.info(
            "Secure Me coordinator initialized (exit=%ds, entry=%ds)",
            exit_delay, entry_delay,
        )

        self._last_health_event_time: float = 0.0
        self._health_event_interval: float = 5.0
        self._last_countdown: int = -1

        # v1.4.0: Presence-based auto-arm monitor (started after store is loaded)
        self._presence_monitor: PresenceMonitor | None = None

    # ── Scheduled test runner ────────────────────────────────────────────────

    async def _check_scheduled_tests(self, now=None) -> None:
        """Called every minute — runs any scheduled tests that are due."""
        if not hasattr(self, "store") or not self.store:
            return

        from datetime import datetime
        import time as _time

        scheduled = self.store.get_scheduled_tests()
        if not scheduled:
            return

        now_dt = datetime.now()
        weekday  = now_dt.weekday()   # 0=Mon, 6=Sun
        hour     = now_dt.hour
        minute   = now_dt.minute

        for test_id, cfg in scheduled.items():
            if not cfg.get("enabled", True):
                continue

            schedule = cfg.get("schedule", {})
            sched_hour   = schedule.get("hour", 8)
            sched_minute = schedule.get("minute", 0)
            mode         = schedule.get("mode", "weekly")

            # Only fire at the configured minute
            if hour != sched_hour or minute != sched_minute:
                continue

            # Avoid running twice in the same minute
            last_run = cfg.get("last_run", "")
            if last_run:
                try:
                    last_dt = datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S")
                    if (now_dt - last_dt).total_seconds() < 60:
                        continue
                except ValueError:
                    pass

            should_run = False
            if mode == "weekly":
                sched_weekday = schedule.get("weekday", 6)  # default Sunday
                should_run = (weekday == sched_weekday)
            elif mode == "interval":
                interval_weeks = schedule.get("interval_weeks", 1)
                # Calculate weeks since epoch, compare modulo interval
                epoch = datetime(2024, 1, 7)  # a Sunday
                weeks_since = (now_dt - epoch).days // 7
                should_run = (weeks_since % interval_weeks == 0) and (weekday == 6)
            elif mode == "daily":
                should_run = True

            if not should_run:
                continue

            test_type = cfg.get("test_type", "quick")
            _LOGGER.info(
                "Scheduled test '%s' (%s/%s) firing at %s",
                cfg.get("name", test_id), mode, test_type, now_dt.strftime("%Y-%m-%d %H:%M")
            )

            # Run test via websocket handler logic — import inline to avoid circular
            try:
                from .websocket_api import _run_test_internal
                result = await _run_test_internal(self.hass, test_type)
                overall = result.get("overall", "unknown")
                timestamp = result.get("timestamp", now_dt.strftime("%Y-%m-%d %H:%M:%S"))
                await self.store.async_update_scheduled_test_result(test_id, timestamp, overall)

                _LOGGER.info("Scheduled test '%s' completed: %s", cfg.get("name", test_id), overall)

                # Notify admins on fail if configured
                if cfg.get("notify_on_fail", True) and overall in ("fail", "critical"):
                    await self._notify_scheduled_test_fail(cfg, result)

            except Exception as err:
                _LOGGER.error("Scheduled test '%s' failed: %s", test_id, err)
                await self.store.async_update_scheduled_test_result(
                    test_id, now_dt.strftime("%Y-%m-%d %H:%M:%S"), "error"
                )

    async def _notify_scheduled_test_fail(self, cfg: dict, result: dict) -> None:
        """Send push notification to admin users when a scheduled test fails."""
        from .notification_dispatcher import _send_push
        if not hasattr(self, "store") or not self.store:
            return

        failed_modules = [
            mid for mid, m in result.get("modules", {}).items()
            if m.get("status") in ("fail", "error")
        ]
        msg = (
            f"Scheduled test '{cfg.get('name', 'Test')}' failed. "
            f"Failed modules: {', '.join(failed_modules) if failed_modules else 'sensor or system issue'}."
        )
        title = "Secure Me: Scheduled Test FAILED"

        admins = [
            u for u in self.store.get_users().values()
            if u.get("enabled", True) and u.get("admin") and u.get("notify_service")
        ]
        if admins:
            for user in admins:
                await _send_push(self.hass, user["notify_service"], title, msg)
        else:
            await _send_push(self.hass, "notify.notify", title, msg)

    # ── Push notification handler (v1.2.0) ──────────────────────────────────

    @callback
    def _handle_push_event(self, event) -> None:
        """Handle mobile push notification action buttons.

        Allows arm/disarm from HA Companion push notifications without opening the app.
        Action strings match the PUSH_EVENT_ACTIONS constants.
        """
        if not event.data:
            return

        action = (
            event.data.get("actionName")
            if "actionName" in event.data
            else event.data.get("action")
        )

        if action not in PUSH_EVENT_ACTIONS:
            return

        _LOGGER.info("Received push action: %s", action)
        if action == EVENT_ACTION_DISARM:
            self.hass.async_create_task(self.async_disarm())

        elif action == EVENT_ACTION_FORCE_ARM:
            # Force-arm in last used mode (or away if unknown)
            mode = self._last_arm_mode or STATE_ALARM_ARMED_AWAY
            self.hass.async_create_task(self._arm_by_state(mode, skip_delay=True, force=True))

        elif action == EVENT_ACTION_RETRY_ARM:
            mode = self._last_arm_mode or STATE_ALARM_ARMED_AWAY
            self.hass.async_create_task(self._arm_by_state(mode))

        elif action == EVENT_ACTION_ARM_AWAY:
            self.hass.async_create_task(self.async_arm_away())

        elif action == EVENT_ACTION_ARM_HOME:
            self.hass.async_create_task(self.async_arm_home())

        elif action == EVENT_ACTION_ARM_NIGHT:
            self.hass.async_create_task(self.async_arm_night())

        elif action == EVENT_ACTION_ARM_VACATION:
            self.hass.async_create_task(self.async_arm_vacation())

        elif action == EVENT_ACTION_ARM_HOME_ALONE:
            self.hass.async_create_task(self.async_arm_home_alone())

    async def _arm_by_state(
        self, state: str, skip_delay: bool = False, force: bool = False
    ) -> bool:
        """Arm in the mode corresponding to an alarm state string."""
        if state == STATE_ALARM_ARMED_AWAY:
            return await self.async_arm_away(skip_delay=skip_delay, force=force)
        if state == STATE_ALARM_ARMED_HOME:
            return await self.async_arm_home(skip_delay=skip_delay)
        if state == STATE_ALARM_ARMED_NIGHT:
            return await self.async_arm_night(skip_delay=skip_delay)
        if state == STATE_ALARM_ARMED_VACATION:
            return await self.async_arm_vacation(skip_delay=skip_delay)
        if state == STATE_ALARM_ARMED_HOME_ALONE:
            return await self.async_arm_home_alone(skip_delay=skip_delay)
        return False

    # ── arm_on_close callback (v1.2.0) ──────────────────────────────────────

    async def _arm_on_close_triggered(self, entity_id: str) -> None:
        """Auto-arm when an arm_on_close sensor closes (e.g. front door shut)."""
        if self.state_machine.is_armed or self.state_machine.is_arming:
            return
        _LOGGER.info(
            "arm_on_close: sensor %s closed — automatically arming (away)", entity_id
        )
        await self.async_arm_away(auto=True)

    # ── State / countdown callbacks ──────────────────────────────────────────

    async def _state_changed(self, new_state: str, countdown: int) -> None:
        """Handle state machine state change."""
        _LOGGER.info(
            "Coordinator received state change: %s (countdown=%d)", new_state, countdown
        )
        await self.async_request_refresh()

        if new_state == STATE_ALARM_DISARMED:
            self.zone_manager.clear_all_triggers()
            self.hass.bus.async_fire(
                EVENT_ALARM_DISARMED, {
                    "disarmed_by": self._disarmed_by,
                    "disarmed_by_id": self._disarmed_by_id,
                }
            )

        elif new_state in (
            STATE_ALARM_ARMED_AWAY,
            STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT,
            STATE_ALARM_ARMED_VACATION,
            STATE_ALARM_ARMED_HOME_ALONE,
        ):
            self._last_arm_mode = new_state
            if len(self.zone_manager._unsubscribe_callbacks) == 0:
                # Derive short mode string from state constant
                _mode_map = {
                    STATE_ALARM_ARMED_AWAY:       "away",
                    STATE_ALARM_ARMED_HOME:       "home",
                    STATE_ALARM_ARMED_NIGHT:      "night",
                    STATE_ALARM_ARMED_VACATION:   "vacation",
                    STATE_ALARM_ARMED_HOME_ALONE: "home_alone",
                }
                self.zone_manager.start_monitoring(
                    arm_mode=_mode_map.get(new_state, "away")
                )
            self.hass.bus.async_fire(
                EVENT_ALARM_ARMED, {
                    "mode": new_state,
                    "armed_by": self._armed_by,
                    "armed_by_id": self._armed_by_id,
                }
            )

        elif new_state == STATE_ALARM_TRIGGERED:
            self.hass.bus.async_fire(
                EVENT_ALARM_TRIGGERED, {"triggered_by": self._triggered_by}
            )

    async def _countdown_updated(self, countdown: int) -> None:
        """Handle countdown tick — lightweight update."""
        self._last_countdown = countdown
        if self.data:
            self.data["countdown"] = countdown
        self.async_update_listeners()
        if countdown == 0 or countdown % 5 == 0:
            await self.async_request_refresh()

    async def _zone_triggered(self, zone) -> None:
        """Handle zone trigger."""
        current = self.state_machine.current_state

        if current == STATE_ALARM_ARMING:
            _LOGGER.warning(
                "Zone %s triggered during exit delay — ignoring", zone.zone_id
            )
            return

        if not self.state_machine.is_armed:
            return

        _LOGGER.warning(
            "Zone %s triggered (type=%s, sensors=%s)",
            zone.zone_id, zone.zone_type, zone.open_sensors,
        )
        await self.state_machine.trigger_entry_delay(zone.zone_type)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            data = {
                "state": self.state_machine.current_state,
                "countdown": self.state_machine.countdown,
                "armed_by": self._armed_by,
                "disarmed_by": self._disarmed_by,
                "triggered_by": self._triggered_by,
                "open_sensors": self.zone_manager.get_all_open_sensors(),
                "triggered_zones": len(self.zone_manager.get_triggered_zones()),
                "code_valid": bool(self._code),
                "is_armed": self.state_machine.is_armed,
                "is_arming": self.state_machine.is_arming,
                "is_pending": self.state_machine.is_pending,
                "fake_presence": self.fake_presence,
            }
            now = time.monotonic()
            if now - self._last_health_event_time >= self._health_event_interval:
                self._last_health_event_time = now
                self.hass.bus.async_fire(
                    f"{DOMAIN}_health_updated",
                    {
                        "modules": self.get_module_health(),
                        "health_score": self.get_health_score(),
                    },
                )
            return data
        except Exception as err:
            raise UpdateFailed(f"Error updating coordinator: {err}") from err

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def alarm_state(self) -> str:
        return self.state_machine.current_state

    @property
    def delay_countdown(self) -> int:
        return self.state_machine.countdown

    @property
    def exit_delay(self) -> int:
        return self.state_machine.exit_delay

    @property
    def entry_delay(self) -> int:
        return self.state_machine.entry_delay

    @property
    def code(self) -> str:
        return self._code

    @property
    def armed_by(self) -> str | None:
        return self._armed_by

    @property
    def disarmed_by(self) -> str | None:
        return self._disarmed_by

    @property
    def triggered_by(self) -> str | None:
        return self._triggered_by

    @property
    def open_sensors(self) -> list[str]:
        return self.zone_manager.get_all_open_sensors()

    @property
    def bypassed_zones(self) -> list[str]:
        return []

    @property
    def fake_presence(self) -> bool:
        if hasattr(self, "store") and self.store:
            return self.store.get_fake_presence()
        return False

    # ── Code validation ──────────────────────────────────────────────────────

    def validate_code(self, code: str | None) -> bool:
        """Validate code. Uses bcrypt if store has hashed codes."""
        if not self._code:
            return True
        if not code:
            return False
        if hasattr(self, "store") and self.store:
            result = self.store.authenticate_user(code)
            return result is not None
        return code == self._code

    def identify_user(self, code: str | None) -> str:
        """Return the user's name from code, or 'user' as fallback."""
        if code and hasattr(self, "store") and self.store:
            result = self.store.authenticate_user(code)
            if result:
                return result.get("name") or "user"
        return "user"

    def identify_user_id(self, code: str | None) -> str | None:
        """Return the user_id from code, or None."""
        if code and hasattr(self, "store") and self.store:
            users = self.store.get_users()
            for uid, user in users.items():
                if not user.get("enabled", True):
                    continue
                stored = user.get("code", "")
                if not stored:
                    continue
                from .store import SecureMeStore
                if user.get("code_hashed", False):
                    if SecureMeStore._check_code(code, stored):
                        return uid
                elif stored == code:
                    return uid
        return None

    async def async_restore_state(self, state: str, armed_by: str | None = None) -> None:
        """Restore alarm state after HA restart.

        Called from alarm_control_panel.async_added_to_hass() with the
        last known state from HA's entity registry.

        - Sets state_machine state directly (no callbacks, no delays).
        - Restarts zone monitoring if the restored state is armed.
        - Does NOT fire EVENT_ALARM_ARMED — this is a silent restore.
        """
        _LOGGER.info(
            "Coordinator restoring alarm state: '%s' (armed_by=%s)", state, armed_by
        )
        self.state_machine.restore_state(state)

        if armed_by:
            self._armed_by = armed_by

        # Remember last arm mode for push FORCE_ARM
        if state in (
            STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT, STATE_ALARM_ARMED_VACATION,
            STATE_ALARM_ARMED_HOME_ALONE,
        ):
            self._last_arm_mode = state

        # Restart zone monitoring if armed (so sensors are watched immediately)
        if self.state_machine.is_armed:
            _mode_map = {
                STATE_ALARM_ARMED_AWAY:       "away",
                STATE_ALARM_ARMED_HOME:       "home",
                STATE_ALARM_ARMED_NIGHT:      "night",
                STATE_ALARM_ARMED_VACATION:   "vacation",
                STATE_ALARM_ARMED_HOME_ALONE: "home_alone",
            }
            arm_mode = _mode_map.get(state, "away")
            self.zone_manager.start_monitoring(arm_mode=arm_mode)
            _LOGGER.info(
                "Zone monitoring restarted after restore (mode=%s)", arm_mode
            )

        await self.async_request_refresh()

    # ── Arm / Disarm / Trigger ───────────────────────────────────────────────

    async def async_arm_away(
        self,
        code: str | None = None,
        skip_delay: bool = False,
        auto: bool = False,
        force: bool = False,
    ) -> bool:
        """Arm in away mode.

        force=True skips the open-sensor check (used by push FORCE_ARM).
        auto=True respects fake_presence block.
        """
        _LOGGER.info(
            "Arming alarm (away, skip_delay=%s, auto=%s, force=%s)",
            skip_delay, auto, force,
        )
        if auto and self.fake_presence:
            _LOGGER.info("Auto arm blocked — Fake Presence active")
            return False

        if not force:
            # Only check sensors in zones that are active for 'away' mode
            all_sensors = [
                s for z in self.zone_manager.zones.values()
                if z.enabled and z.is_active_for_mode("away")
                for s in z.sensors
            ]
            bypassed = self.zone_manager.get_auto_bypass_sensors(all_sensors)
            if self.zone_manager.check_for_open_sensors(bypass_list=bypassed):
                _LOGGER.warning(
                    "Cannot arm — open sensors: %s", self.zone_manager.get_all_open_sensors()
                )
                return False

        success = await self.state_machine.arm_away(skip_delay)
        if success:
            self._armed_by = self.identify_user(code)
            self._armed_by_id = self.identify_user_id(code)
            await self._execute_modules_arm_away()
        await self.async_request_refresh()
        return success

    async def async_arm_home(
        self, code: str | None = None, skip_delay: bool = False, force: bool = False
    ) -> bool:
        """Arm in home mode."""
        _LOGGER.info("Arming alarm (home, skip_delay=%s, force=%s)", skip_delay, force)
        if not force:
            all_sensors = [
                s for z in self.zone_manager.zones.values()
                if z.enabled and z.is_active_for_mode("home")
                for s in z.sensors
            ]
            bypassed = self.zone_manager.get_auto_bypass_sensors(all_sensors)
            if self.zone_manager.check_for_open_sensors(bypass_list=bypassed):
                _LOGGER.warning(
                    "Cannot arm home — open sensors: %s", self.zone_manager.get_all_open_sensors()
                )
                return False
        success = await self.state_machine.arm_home(skip_delay)
        if success:
            self._armed_by = self.identify_user(code)
            self._armed_by_id = self.identify_user_id(code)
            await self._execute_modules_arm_home()
        await self.async_request_refresh()
        return success

    async def async_arm_night(
        self, code: str | None = None, skip_delay: bool = False, force: bool = False
    ) -> bool:
        """Arm in night mode."""
        _LOGGER.info("Arming alarm (night, skip_delay=%s, force=%s)", skip_delay, force)
        if not force:
            all_sensors = [
                s for z in self.zone_manager.zones.values()
                if z.enabled and z.is_active_for_mode("night")
                for s in z.sensors
            ]
            bypassed = self.zone_manager.get_auto_bypass_sensors(all_sensors)
            if self.zone_manager.check_for_open_sensors(bypass_list=bypassed):
                _LOGGER.warning(
                    "Cannot arm night — open sensors: %s", self.zone_manager.get_all_open_sensors()
                )
                return False
        success = await self.state_machine.arm_night(skip_delay)
        if success:
            self._armed_by = self.identify_user(code)
            self._armed_by_id = self.identify_user_id(code)
            await self._execute_modules_arm_night()
        await self.async_request_refresh()
        return success

    async def async_arm_vacation(
        self, code: str | None = None, skip_delay: bool = False, force: bool = False
    ) -> bool:
        """Arm in vacation mode."""
        _LOGGER.info("Arming alarm (vacation, skip_delay=%s, force=%s)", skip_delay, force)
        if not force:
            all_sensors = [
                s for z in self.zone_manager.zones.values()
                if z.enabled and z.is_active_for_mode("vacation")
                for s in z.sensors
            ]
            bypassed = self.zone_manager.get_auto_bypass_sensors(all_sensors)
            if self.zone_manager.check_for_open_sensors(bypass_list=bypassed):
                _LOGGER.warning(
                    "Cannot arm vacation — open sensors: %s", self.zone_manager.get_all_open_sensors()
                )
                return False
        success = await self.state_machine.arm_vacation(skip_delay)
        if success:
            self._armed_by = self.identify_user(code)
            self._armed_by_id = self.identify_user_id(code)
            await self._execute_modules_arm_away()
        await self.async_request_refresh()
        return success

    async def async_arm_home_alone(
        self, code: str | None = None, skip_delay: bool = False, force: bool = False
    ) -> bool:
        """Arm in home alone mode (cameras on, motion visual-only, door sensors notify)."""
        _LOGGER.info("Arming alarm (home_alone, skip_delay=%s, force=%s)", skip_delay, force)
        if not force:
            all_sensors = [
                s for z in self.zone_manager.zones.values()
                if z.enabled and z.is_active_for_mode("home_alone")
                for s in z.sensors
            ]
            bypassed = self.zone_manager.get_auto_bypass_sensors(all_sensors)
            if self.zone_manager.check_for_open_sensors(bypass_list=bypassed):
                _LOGGER.warning(
                    "Cannot arm home_alone — open sensors: %s", self.zone_manager.get_all_open_sensors()
                )
                return False
        success = await self.state_machine.arm_home_alone(skip_delay)
        if success:
            self._armed_by = self.identify_user(code)
            self._armed_by_id = self.identify_user_id(code)
            # Activate cameras on arm — same as away mode
            await self._execute_modules_arm_away()
        await self.async_request_refresh()
        return success

    async def async_disarm(self, code: str | None = None) -> bool:
        """Disarm the alarm."""
        _LOGGER.info("Disarming alarm")
        if not self.validate_code(code):
            _LOGGER.warning("Invalid code provided for disarm")
            return False

        if self.state_machine.is_pending:
            success = await self.state_machine.cancel_pending()
        else:
            success = await self.state_machine.disarm()

        if success:
            self._disarmed_by = self.identify_user(code)
            self._disarmed_by_id = self.identify_user_id(code)
            self.zone_manager.stop_monitoring()
            await self._execute_modules_disarm()
        await self.async_request_refresh()
        return success

    async def async_trigger(self, source: str | None = None) -> bool:
        """Trigger the alarm."""
        _LOGGER.warning("Alarm triggered! Source: %s", source or "manual")
        self._triggered_by = source or "manual"
        success = await self.state_machine.trigger_alarm(self._triggered_by)
        if success:
            await self._execute_modules_trigger()
        await self.async_request_refresh()
        return success

    async def async_set_fake_presence(self, active: bool) -> None:
        """Set fake presence and fire notification + event.

        When Fake Presence is enabled, any pending auto-arm countdown is
        cancelled so the user's laundry-while-out scenario does not cause
        locks to engage or the alarm to arm after the countdown expires.
        """
        if not hasattr(self, "store") or not self.store:
            _LOGGER.warning("Cannot set fake presence - store not loaded yet")
            return
        await self.store.async_set_fake_presence(active)

        # Cancel any pending auto-arm countdown when Fake Presence activates.
        # This guards against the race where all trackers went away first,
        # the countdown started, and Fake Presence is toggled on before the
        # countdown expires.
        if active and self._presence_monitor is not None:
            self._presence_monitor._cancel_timer()

        msg = FAKE_PRESENCE_ON_EN if active else FAKE_PRESENCE_OFF_EN
        try:
            from homeassistant.components.persistent_notification import (
                async_create as pn_create,
            )
            pn_create(
                self.hass,
                message=msg,
                title="Secure Me - Fake Presence",
                notification_id=NOTIFY_ID_FAKE_PRESENCE,
            )
        except Exception as err:
            _LOGGER.warning("Could not create persistent notification: %s", err)
        self.hass.bus.async_fire(EVENT_FAKE_PRESENCE_CHANGED, {"active": active})
        _LOGGER.info("Fake presence set to %s", active)
        await self.async_request_refresh()

    # ── Config ───────────────────────────────────────────────────────────────

    def update_config(self, config_data: dict[str, Any]) -> None:
        """Update configuration."""
        self._code = config_data.get(CONF_CODE, self._code)
        exit_delay = config_data.get(CONF_EXIT_DELAY, self.state_machine.exit_delay)
        entry_delay = config_data.get(CONF_ENTRY_DELAY, self.state_machine.entry_delay)
        trigger_time = config_data.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME)
        self.state_machine.update_config(exit_delay, entry_delay, trigger_time)

    # ── Module management ────────────────────────────────────────────────────

    def _init_modules(self, store=None) -> None:
        """Initialize all available modules."""
        if store is not None:
            stored_modules = store.get_modules()
        else:
            stored_modules = {}
        options_modules = self.config_entry.options.get("modules", {})

        def _get_config(mid: str) -> dict:
            return stored_modules.get(mid) or options_modules.get(mid, {})

        for mid in ("camera", "lock", "lights", "climate", "siren", "tts"):
            module_config = _get_config(mid)
            module_classes = {
                "camera": CameraModule,
                "lock": LockModule,
                "lights": LightsModule,
                "climate": ClimateModule,
                "siren": SirenModule,
                "tts": TTSModule,
            }
            self.modules[mid] = module_classes[mid](self.hass, module_config)

        _LOGGER.info("Modules initialized: %s", list(self.modules.keys()))

    async def _execute_modules_arm_away(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm("away")
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_away: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "arm_away", "error": str(err)}
                    )

    async def _execute_modules_arm_home(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm("home")
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_home: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "arm_home", "error": str(err)}
                    )

    async def _execute_modules_arm_night(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm("night")
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_night: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "arm_night", "error": str(err)}
                    )

    async def _execute_modules_disarm(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_disarm()
                except Exception as err:
                    _LOGGER.error("Module %s failed on disarm: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "disarm", "error": str(err)}
                    )

    async def _execute_modules_trigger(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_trigger()
                except Exception as err:
                    _LOGGER.error("Module %s failed on trigger: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "trigger", "error": str(err)}
                    )

    def enable_module(self, module_id: str) -> bool:
        if module_id not in self.modules:
            return False
        self.modules[module_id].enable()
        self.hass.bus.async_fire(EVENT_MODULE_ENABLED, {"module": module_id})
        return True

    def disable_module(self, module_id: str) -> bool:
        if module_id not in self.modules:
            return False
        self.modules[module_id].disable()
        self.hass.bus.async_fire(EVENT_MODULE_DISABLED, {"module": module_id})
        return True

    def update_module_config(self, module_id: str, config: dict) -> bool:
        """Re-initialize a module with updated configuration."""
        module_classes = {
            "camera": CameraModule, "lock": LockModule, "lights": LightsModule,
            "climate": ClimateModule, "siren": SirenModule, "tts": TTSModule,
        }
        cls = module_classes.get(module_id)
        if not cls:
            return False
        try:
            self.modules[module_id] = cls(self.hass, config)
            return True
        except Exception as err:
            _LOGGER.error("Failed to re-initialize module %s: %s", module_id, err)
            return False

    async def async_load_store_config(self, store) -> None:
        """Load module and sensor configs from store, re-initialize modules."""
        self.store = store
        stored = store.get_modules()

        # v1.4.0: inject speaker_profiles into TTS module config
        speaker_profiles = store.get_speaker_profiles()

        if stored:
            for module_id, config in stored.items():
                if config:
                    if module_id == "tts" and speaker_profiles:
                        config = dict(config)
                        config["speaker_profiles"] = speaker_profiles
                    normalized = _normalize_coordinator_config(module_id, config)
                    self.update_module_config(module_id, normalized)

        # Load zones into zone manager (with arm_modes)
        for zone_id, zone_cfg in store.get_zones().items():
            self.zone_manager.add_zone(
                zone_id=zone_id,
                zone_type=zone_cfg.get("zone_type", "entry"),
                sensors=zone_cfg.get("sensors", []),
                enabled=zone_cfg.get("enabled", True),
                arm_modes=zone_cfg.get("arm_modes", ["away"]),
            )
        _LOGGER.info("Loaded %d zones from store", len(store.get_zones()))

        # v1.2.0: Push sensor configs and groups into zone manager
        sensor_configs = store.get_sensors()
        self.zone_manager.load_sensor_configs(sensor_configs)

        # v1.4.0: Merge Home Alone per-sensor config (stored on zone level)
        # into sensor_configs so get_home_alone_sensor_config() can look it up.
        for zone_cfg in store.get_zones().values():
            ha_cfg = zone_cfg.get("home_alone_sensor_config", {})
            for eid, ha_fields in ha_cfg.items():
                if eid not in sensor_configs:
                    sensor_configs[eid] = {}
                sensor_configs[eid].update(ha_fields)
        # Re-load merged configs into zone manager
        self.zone_manager.load_sensor_configs(sensor_configs)

        sensor_groups = store.get_sensor_groups()
        if sensor_groups:
            self.zone_manager.load_sensor_groups(sensor_groups)
            _LOGGER.info("Loaded %d sensor groups from store", len(sensor_groups))

        # v1.4.0: Start presence monitor now that user person_entity fields are available
        if self._presence_monitor is None:
            self._presence_monitor = PresenceMonitor(self.hass, self)
            self._presence_monitor.async_setup()

    # ── Health ───────────────────────────────────────────────────────────────

    def get_health_score(self) -> int:
        total, available = 0, 0
        for module in self.modules.values():
            if not module.enabled:
                continue
            for eid in self._get_module_entity_ids(module):
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
            entities = self._get_module_entity_ids(module)
            unavail = [
                eid for eid in entities
                if not self.hass.states.get(eid)
                or self.hass.states.get(eid).state in ("unavailable", "unknown")
            ]
            result[mid] = {
                "enabled": True,
                "status": "problem" if unavail else "ok",
                "total": len(entities),
                "available": len(entities) - len(unavail),
                "unavailable": unavail,
            }
        return result

    def get_enabled_module_count(self) -> int:
        return sum(1 for m in self.modules.values() if m.enabled)

    @staticmethod
    def _get_module_entity_ids(module) -> list[str]:
        entities: list[str] = []
        for attr in ("poe_switches", "cameras", "recording_entities", "locks", "lights", "climates", "media_players"):
            val = getattr(module, attr, None)
            if isinstance(val, list):
                entities.extend(val)
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

    # ── Presence ──────────────────────────────────────────────────────────────

    def get_presence_status(self) -> dict[str, Any]:
        """Return presence status derived from user tracker entities.

        Reads `person_entity` (canonical) or `tracker_entity` (legacy fallback)
        from each enabled user profile in the store.
        Returns a dict with:
          - anyone_home: bool
          - people_home: list of user names currently home
          - people_away: list of user names currently away
          - tracked_users: total number of users with a tracker configured
          - fake_presence: bool (Fake Presence override active)
        """
        if not hasattr(self, "store") or not self.store:
            return {
                "anyone_home": False,
                "people_home": [],
                "people_away": [],
                "tracked_users": 0,
                "fake_presence": False,
            }

        people_home: list[str] = []
        people_away: list[str] = []

        for user in self.store.get_users().values():
            if not user.get("enabled", True):
                continue
            # Read `person_entity` first (canonical name used by frontend) and fall
            # back to `tracker_entity` for any legacy profiles that might exist.
            tracker = user.get("person_entity") or user.get("tracker_entity", "")
            if not tracker:
                continue
            name = user.get("name", tracker)
            state = self.hass.states.get(tracker)
            if state and state.state == "home":
                people_home.append(name)
            else:
                people_away.append(name)

        fake = self.fake_presence
        # Fake Presence counts as someone being home for auto-arm purposes
        anyone_home = bool(people_home) or fake

        return {
            "anyone_home": anyone_home,
            "people_home": people_home,
            "people_away": people_away,
            "tracked_users": len(people_home) + len(people_away),
            "fake_presence": fake,
        }

    # ── Shutdown ─────────────────────────────────────────────────────────────

    async def async_shutdown(self) -> None:
        """Shutdown coordinator."""
        _LOGGER.info("Shutting down coordinator")

        # Unregister push event listener
        if hasattr(self, "_push_unsub") and self._push_unsub:
            self._push_unsub()

        # Unregister scheduled test timer
        if hasattr(self, "_scheduled_test_unsub") and self._scheduled_test_unsub:
            self._scheduled_test_unsub()

        # v1.4.0: Teardown presence monitor
        if self._presence_monitor is not None:
            self._presence_monitor.async_teardown()
            self._presence_monitor = None

        if hasattr(self, "modules"):
            for mid, module in self.modules.items():
                try:
                    await module.async_cleanup()
                except Exception as err:
                    _LOGGER.error("Module %s cleanup failed: %s", mid, err)
        if hasattr(self, "zone_manager"):
            try:
                self.zone_manager.stop_monitoring()
            except Exception as err:
                _LOGGER.error("Zone manager cleanup failed: %s", err)
        if hasattr(self, "state_machine"):
            try:
                self.state_machine.cleanup()
            except Exception as err:
                _LOGGER.error("State machine cleanup failed: %s", err)
