"""Auto Actions manager for Secure Me.

Monitors person_entity/tracker_entity from enabled Secure Me user profiles
(v1.5.4 -- previously watched every person.* entity in HA; see
async_refresh_trackers() below for why that changed). When the home
becomes empty (all tracked users not_home) it schedules three independent
delayed actions:
  1. Lock all configured locks (unless Fake Presence blocks locks).
  2. Arm the alarm in away mode (unless Fake Presence blocks alarm).
  3. Activate cameras / start recording (unless Fake Presence blocks cameras).

Each action has its own configurable delay. An arrival confirmation window
prevents a brief GPS flicker from cancelling actions mid-flight.

State machine per action:
  IDLE -> PENDING (home empty, timer started)
       -> DONE    (action executed)
  PENDING -> IDLE  (person confirmed home after arrival_confirmation_delay)
  PENDING -> DONE  (delay elapsed, action ran)
  DONE    -> IDLE  (a person comes home -- reset for next cycle)
"""
# VERSION = "1.5.5"

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, callback

from .const import (
    AA_LOCK_ENABLED,
    AA_LOCK_DELAY,
    AA_ALARM_ENABLED,
    AA_ALARM_DELAY,
    AA_CAMERA_ENABLED,
    AA_CAMERA_DELAY,
    AA_ARRIVAL_DELAY,
    AA_NOTIFY_ALL,
    AA_RECHECK_ON_DISARM,
    DEFAULT_AA_RECHECK_ON_DISARM,
    AA_RECHECK_DELAY,
    AA_RECHECK_MIN_AWAY_DURATION,
    AA_RECHECK_INCLUDE_LOCK,
    AA_RECHECK_INCLUDE_ALARM,
    AA_RECHECK_INCLUDE_CAMERA,
    DEFAULT_AA_RECHECK_DELAY,
    DEFAULT_AA_RECHECK_MIN_AWAY_DURATION,
    DEFAULT_AA_RECHECK_INCLUDE_LOCK,
    DEFAULT_AA_RECHECK_INCLUDE_ALARM,
    DEFAULT_AA_RECHECK_INCLUDE_CAMERA,
    FP_ACTIVE,
    FP_BLOCK_ALARM,
    FP_BLOCK_LOCKS,
    FP_BLOCK_CAMERAS,
    DEFAULT_AA_LOCK_DELAY,
    DEFAULT_AA_ALARM_DELAY,
    DEFAULT_AA_CAMERA_DELAY,
    DEFAULT_AA_ARRIVAL_DELAY,
    EVENT_HOME_EMPTY,
    EVENT_PERSON_HOME,
    EVENT_AUTO_ACTION_DONE,
    EVENT_ALARM_DISARMED,
    NOTIFY_ID_AUTO_ACTIONS,
    STATE_ALARM_DISARMED,
)

_LOGGER = logging.getLogger(__name__)


class AutoActionsManager:
    """Manages presence-based automatic actions for Secure Me.

    Lifecycle:
      async_start()  -- call once after coordinator is ready
      async_stop()   -- call on integration unload
    """

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: Any,
        store: Any,
    ) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.store = store

        # Pending asyncio tasks keyed by action name
        self._action_tasks: dict[str, asyncio.Task] = {}
        # Arrival confirmation task
        self._arrival_task: asyncio.Task | None = None
        # v1.5.x: Delayed disarm-recheck task (see _handle_alarm_disarmed())
        self._recheck_task: asyncio.Task | None = None

        # Track which actions have already run in this "home empty" cycle
        self._done_actions: set[str] = set()
        # Track whether home is currently considered empty
        self._home_empty: bool = False
        # v1.5.x: Timestamp (time.monotonic()) of when the house most recently
        # became continuously empty -- tracked independently of alarm state
        # and independently of _home_empty, so it keeps accruing even while
        # _on_home_empty() short-circuits because the alarm is already armed.
        # Powers AA_RECHECK_MIN_AWAY_DURATION. None while not empty.
        self._all_away_since: float | None = None
        # v1.5.x: Restricts which action types the CURRENT empty-house cycle
        # may schedule/settle on. None means "whatever's globally enabled"
        # (the normal, presence-triggered cycle). Set to a concrete subset by
        # _run_recheck_after_delay() so _all_actions_settled() knows not to
        # wait forever on action types this particular recheck excluded.
        self._current_only_actions: set[str] | None = None

        # HA state listener cancel handle
        self._unsub_listener = None
        self._unsub_disarm_listener = None

        # v1.5.4: Scoped presence tracking -- only person_entity/tracker_entity
        # from enabled Secure Me user profiles, not every person.* entity in
        # HA. Rebuilt by async_refresh_trackers(), called from async_start()
        # and whenever a user profile is saved/deleted (see ws_sensors.py).
        self._tracker_entities: set[str] = set()

    # -------------------------------------------------------------------------
    # Public lifecycle
    # -------------------------------------------------------------------------

    @callback
    def async_start(self) -> None:
        """Register presence state listener and start monitoring.

        v1.5.4: Scoped to Secure Me users only (previously watched every
        person.* entity in HA -- see async_refresh_trackers() docstring).
        Also checks initial presence state on startup: hass.bus.async_listen
        only fires on FUTURE state changes, so if the house is already empty
        when HA (and this manager) starts up, no state_changed event would
        ever occur to trigger _on_home_empty() without this check.
        """
        self.async_refresh_trackers()
        self._unsub_listener = self.hass.bus.async_listen(
            "state_changed", self._handle_state_changed
        )
        # v1.5.x: Optional re-check after a remote disarm -- see
        # _handle_alarm_disarmed() docstring and AA_RECHECK_ON_DISARM in
        # const.py for why this exists and why it defaults off.
        self._unsub_disarm_listener = self.hass.bus.async_listen(
            EVENT_ALARM_DISARMED, self._handle_alarm_disarmed
        )
        _LOGGER.info(
            "AutoActionsManager started -- monitoring %d Secure Me user tracker(s)",
            len(self._tracker_entities),
        )
        self.hass.async_create_task(self._check_initial_presence())

    @callback
    def async_refresh_trackers(self) -> None:
        """Rebuild the tracked person-entity set from enabled Secure Me users.

        v1.5.4: AutoActionsManager previously reacted to every person.*
        entity in HA (via a startswith("person.") filter in
        _handle_state_changed), regardless of whether it was tied to a
        Secure Me user. A person entity unrelated to the alarm (a guest, a
        test account, one used only by another integration) could then
        silently block or delay Auto Actions from ever considering the
        house "empty", since _all_persons_away() required every person.*
        entity in the whole HA instance to be not_home. Scoped now to only
        the person_entity/tracker_entity fields on enabled Secure Me user
        profiles -- the same source PresenceMonitor (removed in v1.5.4)
        used to read.

        Call this whenever user profiles may have changed (on
        async_start(), and from ws_save_user/ws_delete_user) so tracker
        edits take effect without an HA restart.
        """
        trackers: set[str] = set()
        for user in self.store.get_users().values():
            if not user.get("enabled", True):
                continue
            tracker = user.get("person_entity") or user.get("tracker_entity", "")
            if tracker:
                trackers.add(tracker)
        self._tracker_entities = trackers
        _LOGGER.debug(
            "AutoActions: tracking %d Secure Me user(s): %s",
            len(trackers), ", ".join(sorted(trackers)) or "<none>",
        )

    async def _check_initial_presence(self) -> None:
        """Check whether the house is already empty at startup.

        See async_start() docstring -- hass.bus.async_listen only fires on
        future changes, so this closes the gap where HA restarts while
        everyone is already away and disarmed.
        """
        if not self._tracker_entities:
            return
        if not self._all_persons_away():
            _LOGGER.debug("AutoActions: at least one tracked person is home at startup")
            return
        self._mark_all_away_if_needed()
        _LOGGER.info(
            "AutoActions: all tracked Secure Me users show 'not_home' at startup "
            "-- treating house as already empty"
        )
        await self._on_home_empty()

    async def async_stop(self) -> None:
        """Cancel all pending tasks and unregister listener."""
        if self._unsub_listener:
            self._unsub_listener()
            self._unsub_listener = None
        if self._unsub_disarm_listener:
            self._unsub_disarm_listener()
            self._unsub_disarm_listener = None
        await self._cancel_all_action_tasks()
        if self._arrival_task and not self._arrival_task.done():
            self._arrival_task.cancel()
        if self._recheck_task and not self._recheck_task.done():
            self._recheck_task.cancel()
        _LOGGER.info("AutoActionsManager stopped")

    # -------------------------------------------------------------------------
    # State change handler
    # -------------------------------------------------------------------------

    @callback
    def _handle_state_changed(self, event: Any) -> None:
        """Handle HA state_changed events for tracked Secure Me user entities.

        v1.5.4: filters against self._tracker_entities (Secure Me users
        only) instead of any entity_id starting with "person." -- see
        async_refresh_trackers() docstring.
        """
        entity_id: str = event.data.get("entity_id", "")
        if entity_id not in self._tracker_entities:
            return

        new_state = event.data.get("new_state")
        if new_state is None:
            return

        new_val = new_state.state

        if new_val == "not_home":
            # Check if ALL persons are now away
            if self._all_persons_away():
                self._mark_all_away_if_needed()
                self.hass.async_create_task(self._on_home_empty())
        else:
            # Someone arrived (or state unknown) -- start arrival confirmation.
            # v1.5.x: also trigger when a disarm-recheck task is pending --
            # the house may not be in the normal _home_empty/_action_tasks
            # state at all (the alarm was armed when the house became empty,
            # so the ordinary empty-house cycle never started and neither
            # flag was ever set), but a recheck could still be counting down
            # in the background and must be cancellable by an arrival just
            # like an ordinary pending action would be.
            recheck_pending = self._recheck_task is not None and not self._recheck_task.done()
            if self._home_empty or self._action_tasks or recheck_pending:
                self.hass.async_create_task(
                    self._on_person_arrived(entity_id, new_val)
                )

    # -------------------------------------------------------------------------
    # Home empty / person arrived
    # -------------------------------------------------------------------------

    async def _on_home_empty(self, only_actions: set[str] | None = None) -> None:
        """Called when all persons are away. Start pending action timers.

        v1.5.x: If the alarm is already armed (in ANY mode -- away, home,
        night, vacation, or the custom home_alone mode), Auto Actions must
        not attempt anything at all: not just skip re-arming (which
        _do_alarm() already guarded against by checking for
        STATE_ALARM_DISARMED), but also skip lock and camera, since an
        already-armed state is a deliberate, current choice that Auto
        Actions should never second-guess. Previously only the alarm
        sub-action checked this; lock/camera would still fire even while
        e.g. armed_home_alone.

        only_actions: when given, restricts this cycle to just these action
        types (still ANDed with the corresponding AA_*_ENABLED flag -- this
        only narrows, never widens what's globally enabled). Used by
        _run_recheck_after_delay() so a disarm-triggered recheck can be
        configured to e.g. only re-lock without re-arming. None (the normal,
        presence-triggered case) means "whatever's globally enabled".
        """
        if self.coordinator.alarm_state != STATE_ALARM_DISARMED:
            _LOGGER.info(
                "AutoActions: home empty but alarm already armed (state=%s) -- "
                "skipping all actions (lock/alarm/camera)",
                self.coordinator.alarm_state,
            )
            return
        if self._home_empty:
            return  # Already in empty state
        self._home_empty = True
        self._done_actions.clear()
        self._current_only_actions = only_actions

        self.hass.bus.async_fire(EVENT_HOME_EMPTY, {})
        _LOGGER.info("AutoActions: home is now empty -- scheduling actions")

        cfg = self.store.get_auto_actions()
        fp = self.store.get_fake_presence_v2()

        def _wanted(name: str) -> bool:
            return only_actions is None or name in only_actions

        # Schedule each enabled action independently
        if cfg.get(AA_LOCK_ENABLED, True) and _wanted("lock"):
            delay = int(cfg.get(AA_LOCK_DELAY, DEFAULT_AA_LOCK_DELAY))
            blocked = fp.get(FP_ACTIVE, False) and fp.get(FP_BLOCK_LOCKS, False)
            self._schedule_action("lock", delay, blocked)

        if cfg.get(AA_ALARM_ENABLED, True) and _wanted("alarm"):
            delay = int(cfg.get(AA_ALARM_DELAY, DEFAULT_AA_ALARM_DELAY))
            blocked = fp.get(FP_ACTIVE, False) and fp.get(FP_BLOCK_ALARM, True)
            self._schedule_action("alarm", delay, blocked)

        if cfg.get(AA_CAMERA_ENABLED, True) and _wanted("camera"):
            delay = int(cfg.get(AA_CAMERA_DELAY, DEFAULT_AA_CAMERA_DELAY))
            blocked = fp.get(FP_ACTIVE, False) and fp.get(FP_BLOCK_CAMERAS, False)
            self._schedule_action("camera", delay, blocked)

    async def _on_person_arrived(self, entity_id: str, state: str) -> None:
        """Called when a person.* entity transitions to a non-away state.

        Starts arrival_confirmation_delay before acting. If the person is
        still home after the delay, cancel remaining pending actions.
        If they leave again before the delay expires, ignore the arrival.
        """
        # Cancel any previous arrival confirmation still running
        if self._arrival_task and not self._arrival_task.done():
            self._arrival_task.cancel()

        arrival_delay = int(
            self.store.get_auto_actions().get(AA_ARRIVAL_DELAY, DEFAULT_AA_ARRIVAL_DELAY)
        )
        _LOGGER.info(
            "AutoActions: %s arrived (state=%s) -- waiting %ds for arrival confirmation",
            entity_id, state, arrival_delay,
        )
        self.hass.bus.async_fire(EVENT_PERSON_HOME, {"entity_id": entity_id})

        self._arrival_task = self.hass.async_create_task(
            self._confirm_arrival(entity_id, arrival_delay)
        )

    async def _confirm_arrival(self, entity_id: str, delay: int) -> None:
        """Wait delay seconds then check if person is still home."""
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return

        # Re-check: is the person (and at least one other) still home?
        # v1.5.x fix: "unknown"/"unavailable" must NOT count as a confirmed
        # arrival. _handle_state_changed() starts this confirmation on ANY
        # transition away from "not_home" -- including a tracker flickering
        # to "unknown" (common with phone GPS/wifi trackers) while the
        # person is genuinely still away. Previously only "not_home" was
        # treated as "still away"; anything else (including "unknown") fell
        # through to "confirmed home" below and cancelled all pending Auto
        # Actions -- e.g. the auto-arm -- even though nobody had actually
        # come home. This mirrors the fail-safe direction already used by
        # _all_persons_away() (which also treats unknown/unavailable as
        # "not confirmed away"), but applied here to the arrival side so a
        # flaky tracker can no longer silently cancel a legitimate
        # in-progress empty-house cycle.
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("not_home", "unknown", "unavailable"):
            _LOGGER.info(
                "AutoActions: arrival confirmation failed for %s (state=%s) -- timers continue",
                entity_id, state.state if state else "missing",
            )
            return

        # Confirmed home -- cancel all pending action tasks
        _LOGGER.info(
            "AutoActions: %s confirmed home after %ds -- cancelling pending timers",
            entity_id, delay,
        )
        await self._cancel_all_action_tasks()
        self._home_empty = False
        self._all_away_since = None
        if self._recheck_task and not self._recheck_task.done():
            self._recheck_task.cancel()

    @callback
    def _handle_alarm_disarmed(self, event: Any) -> None:
        """Optionally re-check presence after the alarm is disarmed.

        Auto Actions normally only reacts to a person.* tracker transitioning
        to not_home. If the alarm is disarmed remotely (e.g. via the app,
        for a delivery or a one-off errand) while everyone is already away,
        no tracker transition happens -- so without this, Auto Actions would
        never notice and would never re-schedule lock/alarm/camera, even
        though the house is (still) empty and now also unarmed.

        Opt-in via AA_RECHECK_ON_DISARM (default off, see const.py). Does not
        act immediately -- kicks off _run_recheck_after_delay(), which waits
        AA_RECHECK_DELAY and then additionally requires AA_RECHECK_MIN_AWAY_
        DURATION of continuous emptiness before doing anything, and even
        then only schedules the action types selected by AA_RECHECK_INCLUDE_*.
        """
        cfg = self.store.get_auto_actions()
        if not cfg.get(AA_RECHECK_ON_DISARM, DEFAULT_AA_RECHECK_ON_DISARM):
            return
        if not self._all_persons_away():
            return
        self._mark_all_away_if_needed()

        delay = int(cfg.get(AA_RECHECK_DELAY, DEFAULT_AA_RECHECK_DELAY))
        _LOGGER.info(
            "AutoActions: alarm disarmed while all tracked users are away -- "
            "waiting %ds before re-checking (recheck_on_disarm enabled)",
            delay,
        )
        if self._recheck_task and not self._recheck_task.done():
            self._recheck_task.cancel()
        self._recheck_task = self.hass.async_create_task(
            self._run_recheck_after_delay(delay)
        )

    async def _run_recheck_after_delay(self, delay: int) -> None:
        """Wait AA_RECHECK_DELAY, then honour the recheck if still warranted.

        Two additional gates beyond the initial check in
        _handle_alarm_disarmed():
          1. Still all-away after the wait (an ordinary arrival-then-disarm
             may have resolved itself by now).
          2. The house has been CONTINUOUSLY empty (self._all_away_since,
             independent of alarm state) for at least
             AA_RECHECK_MIN_AWAY_DURATION -- guards against a fresh "just
             stepped out" disarm-adjacent moment being treated the same as
             a long-standing empty house.

        Only the action types selected by AA_RECHECK_INCLUDE_LOCK/ALARM/
        CAMERA are passed on to _on_home_empty() as its only_actions filter;
        these still only narrow what the corresponding AA_*_ENABLED flag
        already allows, never widen it.
        """
        try:
            if delay > 0:
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return

        if not self._all_persons_away():
            _LOGGER.info(
                "AutoActions: recheck aborted -- someone came home during the wait"
            )
            return

        cfg = self.store.get_auto_actions()
        min_away = int(
            cfg.get(AA_RECHECK_MIN_AWAY_DURATION, DEFAULT_AA_RECHECK_MIN_AWAY_DURATION)
        )
        away_since = self._all_away_since
        if away_since is None or (time.monotonic() - away_since) < min_away:
            _LOGGER.info(
                "AutoActions: recheck skipped -- house not continuously empty "
                "for the required %ds yet",
                min_away,
            )
            return

        only_actions: set[str] = set()
        if cfg.get(AA_RECHECK_INCLUDE_LOCK, DEFAULT_AA_RECHECK_INCLUDE_LOCK):
            only_actions.add("lock")
        if cfg.get(AA_RECHECK_INCLUDE_ALARM, DEFAULT_AA_RECHECK_INCLUDE_ALARM):
            only_actions.add("alarm")
        if cfg.get(AA_RECHECK_INCLUDE_CAMERA, DEFAULT_AA_RECHECK_INCLUDE_CAMERA):
            only_actions.add("camera")
        if not only_actions:
            _LOGGER.info(
                "AutoActions: recheck has no action types selected -- nothing to do"
            )
            return

        _LOGGER.info(
            "AutoActions: recheck confirmed (away %ds, >= %ds required) -- "
            "scheduling %s",
            int(time.monotonic() - away_since), min_away, ", ".join(sorted(only_actions)),
        )
        await self._on_home_empty(only_actions=only_actions)

    # -------------------------------------------------------------------------
    # Action scheduling
    # -------------------------------------------------------------------------

    def _schedule_action(self, action: str, delay: int, blocked: bool) -> None:
        """Schedule an action task."""
        if action in self._action_tasks and not self._action_tasks[action].done():
            return  # Already scheduled

        if blocked:
            _LOGGER.info(
                "AutoActions: %s skipped -- blocked by Fake Presence", action
            )
            self._done_actions.add(action + "_skipped")
            return

        task = self.hass.async_create_task(
            self._run_action_after_delay(action, delay)
        )
        self._action_tasks[action] = task

    async def _run_action_after_delay(self, action: str, delay: int) -> None:
        """Sleep delay seconds, then execute action."""
        try:
            if delay > 0:
                _LOGGER.info(
                    "AutoActions: %s scheduled -- executing in %ds", action, delay
                )
                await asyncio.sleep(delay)
        except asyncio.CancelledError:
            _LOGGER.info("AutoActions: %s timer cancelled", action)
            return

        # Double-check home is still empty (person may have returned just now)
        if not self._home_empty:
            _LOGGER.info("AutoActions: %s aborted -- home no longer empty", action)
            return

        # v1.5.4: Re-check Fake Presence right before executing. _schedule_action()
        # only checked the block flags once, at the moment the house first went
        # empty -- if Fake Presence was toggled on AFTER that (but before this
        # action's delay elapsed), the action would still fire unblocked. This
        # closes the same race that PresenceMonitor's (removed in v1.5.4)
        # Fake-Presence timer-cancel path used to guard against.
        fp = self.store.get_fake_presence_v2()
        if fp.get(FP_ACTIVE, False):
            block_key = {
                "lock": FP_BLOCK_LOCKS,
                "alarm": FP_BLOCK_ALARM,
                "camera": FP_BLOCK_CAMERAS,
            }.get(action)
            if block_key and fp.get(block_key, False):
                _LOGGER.info(
                    "AutoActions: %s aborted at execution time -- Fake Presence now blocks it",
                    action,
                )
                self._done_actions.add(action + "_skipped")
                if self._all_actions_settled():
                    await self._send_summary_notification()
                return

        _LOGGER.info("AutoActions: executing action '%s'", action)
        result = await self._execute_action(action)
        self._done_actions.add(action)
        self.hass.bus.async_fire(EVENT_AUTO_ACTION_DONE, {"action": action, "result": result})

        # If all scheduled actions are done, send summary notification
        if self._all_actions_settled():
            await self._send_summary_notification()

    async def _execute_action(self, action: str) -> str:
        """Execute the given action. Returns a short result string."""
        if action == "lock":
            return await self._do_lock()
        if action == "alarm":
            return await self._do_alarm()
        if action == "camera":
            return await self._do_camera()
        return "unknown"

    # -------------------------------------------------------------------------
    # Individual actions
    # -------------------------------------------------------------------------

    async def _do_lock(self) -> str:
        """Lock all configured lock entities."""
        lock_module = self.coordinator.modules.get("lock")
        if not lock_module or not lock_module.enabled:
            _LOGGER.info("AutoActions lock: lock module disabled or not configured")
            return "skipped (module disabled)"

        locks = getattr(lock_module, "locks", [])
        if not locks:
            return "skipped (no locks configured)"

        locked = []
        failed = []
        for lock_entity in locks:
            # Skip if door is open
            door_sensor = lock_module.door_sensors.get(lock_entity)
            if door_sensor:
                door_state = self.hass.states.get(door_sensor)
                if door_state and door_state.state == "on":
                    _LOGGER.warning(
                        "AutoActions lock: skipping %s -- door is open", lock_entity
                    )
                    continue

            current = self.hass.states.get(lock_entity)
            if current and current.state == "locked":
                locked.append(lock_entity)
                continue  # Already locked

            ok = await lock_module.async_call_service_with_retry(
                "lock", "lock",
                target={"entity_id": lock_entity},
                action=f"auto_lock:{lock_entity}",
            )
            if ok:
                locked.append(lock_entity)
            else:
                failed.append(lock_entity)

        if failed:
            return f"locked {len(locked)}, failed {len(failed)}: {', '.join(failed)}"
        return f"locked {len(locked)}: {', '.join(locked)}"

    async def _do_alarm(self) -> str:
        """Arm the alarm in away mode (skip exit delay)."""
        current_state = self.coordinator.alarm_state
        if current_state != STATE_ALARM_DISARMED:
            _LOGGER.info(
                "AutoActions alarm: skipping arm -- state is %s", current_state
            )
            return f"skipped (state={current_state})"

        ok = await self.coordinator.async_arm_away(skip_delay=True)
        if ok:
            return "armed away"
        return "arm failed"

    async def _do_camera(self) -> str:
        """Activate camera module (start recording)."""
        camera_module = self.coordinator.modules.get("camera")
        if not camera_module or not camera_module.enabled:
            return "skipped (module disabled)"

        # Trigger camera module as if arming -- this activates recording
        ok = await camera_module.async_arm("away")
        if ok:
            return "cameras activated"
        return "camera activation failed"

    # -------------------------------------------------------------------------
    # Notification
    # -------------------------------------------------------------------------

    async def _send_summary_notification(self) -> None:
        """Send a summary notification of what happened."""
        cfg = self.store.get_auto_actions()
        fp = self.store.get_fake_presence_v2()
        fp_active = fp.get(FP_ACTIVE, False)

        lines = ["Auto Actions completed -- home was empty:"]

        action_labels = {
            "lock": "Locks",
            "alarm": "Alarm",
            "camera": "Cameras",
        }
        for action, label in action_labels.items():
            if action in self._done_actions:
                lines.append(f"  {label}: completed")
            elif action + "_skipped" in self._done_actions:
                lines.append(f"  {label}: skipped (Fake Presence active)")
            # Actions still pending are not included (notification only fires when all settled)

        if fp_active:
            fp_blocks = []
            if fp.get(FP_BLOCK_ALARM):
                fp_blocks.append("alarm")
            if fp.get(FP_BLOCK_LOCKS):
                fp_blocks.append("locks")
            if fp.get(FP_BLOCK_CAMERAS):
                fp_blocks.append("cameras")
            if fp_blocks:
                lines.append(f"  Fake Presence blocked: {', '.join(fp_blocks)}")

        message = "\n".join(lines)
        timestamp = datetime.now().strftime("%H:%M:%S")
        title = f"Secure Me: Auto Actions ({timestamp})"

        # Determine recipients
        notify_all = cfg.get(AA_NOTIFY_ALL, False)
        users = self.store.get_users()
        services = []
        for user in users.values():
            if not user.get("enabled", True):
                continue
            svc = user.get("notify_service", "")
            if not svc:
                continue
            if notify_all or user.get("admin", False):
                services.append(svc)

        if not services:
            # Fallback to persistent notification.
            # v1.5.x fix: hass.components.* is a deprecated/removed access
            # pattern on modern HA HomeAssistant objects (this line crashed
            # with AttributeError on every run that hit this fallback --
            # e.g. Auto Actions enabled with no admin notify_service
            # configured -- surfaced as a silent "Task exception was never
            # retrieved" in the log, though the action itself still
            # completed fine since this only affects the notification).
            # Matches the import pattern coordinator.py already uses for
            # Fake Presence notifications.
            from homeassistant.components.persistent_notification import (
                async_create as pn_create,
            )
            pn_create(
                self.hass,
                message=message,
                title=title,
                notification_id=NOTIFY_ID_AUTO_ACTIONS,
            )
            return

        for svc in set(services):
            domain, service_name = svc.split(".", 1) if "." in svc else (svc, "notify")
            try:
                await self.hass.services.async_call(
                    domain, service_name,
                    {"title": title, "message": message},
                )
            except Exception as err:
                _LOGGER.warning(
                    "AutoActions: failed to notify via %s: %s", svc, err
                )

        _LOGGER.info("AutoActions: summary notification sent to %d service(s)", len(set(services)))

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _mark_all_away_if_needed(self) -> None:
        """Record the start of the current continuous-empty-house stretch.

        Independent of alarm state and of _home_empty -- called whenever
        _all_persons_away() first becomes true, whether or not
        _on_home_empty() actually goes on to schedule anything (e.g. it
        keeps accruing even while the alarm is already armed and
        _on_home_empty() short-circuits). Reset to None only on a confirmed
        arrival (_confirm_arrival()). Powers AA_RECHECK_MIN_AWAY_DURATION.
        """
        if self._all_away_since is None:
            self._all_away_since = time.monotonic()

    def _all_persons_away(self) -> bool:
        """Return True if every tracked Secure Me user is currently away.

        v1.5.4: iterates self._tracker_entities (Secure Me users only)
        instead of every person.* entity in HA -- see
        async_refresh_trackers() docstring. Fail-safe direction preserved:
        "unavailable"/"unknown" states count as NOT away (same as
        PresenceMonitor's equivalent _all_away(), which this replaces), so
        a flaky tracker never triggers an unattended arm/lock.
        """
        if not self._tracker_entities:
            return False
        for entity_id in self._tracker_entities:
            state = self.hass.states.get(entity_id)
            if state is None or state.state in ("home", "unavailable", "unknown"):
                return False
        return True

    def _all_actions_settled(self) -> bool:
        """Return True when all scheduled action tasks have finished or were skipped.

        v1.5.x: When the current cycle was started by a disarm-recheck with
        a restricted only_actions set (self._current_only_actions), the
        expected set is intersected with it -- otherwise this would wait
        forever for an action type the recheck deliberately excluded, since
        that type never gets scheduled and so never lands in _done_actions.
        """
        cfg = self.store.get_auto_actions()
        expected: set[str] = set()
        if cfg.get(AA_LOCK_ENABLED, True):
            expected.add("lock")
        if cfg.get(AA_ALARM_ENABLED, True):
            expected.add("alarm")
        if cfg.get(AA_CAMERA_ENABLED, True):
            expected.add("camera")
        if self._current_only_actions is not None:
            expected &= self._current_only_actions

        for action in expected:
            if action not in self._done_actions and action + "_skipped" not in self._done_actions:
                return False
        return True

    async def _cancel_all_action_tasks(self) -> None:
        """Cancel all running action tasks."""
        for action, task in list(self._action_tasks.items()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        self._action_tasks.clear()
