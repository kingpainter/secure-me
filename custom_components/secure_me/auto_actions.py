"""Auto Actions manager for Secure Me.

Monitors all person.* entities. When the home becomes empty (all persons
not_home) it schedules three independent delayed actions:
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
# VERSION = "1.5.0"

import asyncio
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    AA_LOCK_ENABLED,
    AA_LOCK_DELAY,
    AA_ALARM_ENABLED,
    AA_ALARM_DELAY,
    AA_CAMERA_ENABLED,
    AA_CAMERA_DELAY,
    AA_ARRIVAL_DELAY,
    AA_NOTIFY_ALL,
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

        # Track which actions have already run in this "home empty" cycle
        self._done_actions: set[str] = set()
        # Track whether home is currently considered empty
        self._home_empty: bool = False

        # HA state listener cancel handle
        self._unsub_listener = None

    # -------------------------------------------------------------------------
    # Public lifecycle
    # -------------------------------------------------------------------------

    @callback
    def async_start(self) -> None:
        """Register presence state listener."""
        self._unsub_listener = self.hass.bus.async_listen(
            "state_changed", self._handle_state_changed
        )
        _LOGGER.info("AutoActionsManager started -- monitoring person.* entities")

    async def async_stop(self) -> None:
        """Cancel all pending tasks and unregister listener."""
        if self._unsub_listener:
            self._unsub_listener()
            self._unsub_listener = None
        await self._cancel_all_action_tasks()
        if self._arrival_task and not self._arrival_task.done():
            self._arrival_task.cancel()
        _LOGGER.info("AutoActionsManager stopped")

    # -------------------------------------------------------------------------
    # State change handler
    # -------------------------------------------------------------------------

    @callback
    def _handle_state_changed(self, event: Any) -> None:
        """Handle HA state_changed events for person.* entities."""
        entity_id: str = event.data.get("entity_id", "")
        if not entity_id.startswith("person."):
            return

        new_state = event.data.get("new_state")
        if new_state is None:
            return

        new_val = new_state.state

        if new_val == "not_home":
            # Check if ALL persons are now away
            if self._all_persons_away():
                self.hass.async_create_task(self._on_home_empty())
        else:
            # Someone arrived (or state unknown) -- start arrival confirmation
            if self._home_empty or self._action_tasks:
                self.hass.async_create_task(
                    self._on_person_arrived(entity_id, new_val)
                )

    # -------------------------------------------------------------------------
    # Home empty / person arrived
    # -------------------------------------------------------------------------

    async def _on_home_empty(self) -> None:
        """Called when all persons are away. Start pending action timers."""
        if self._home_empty:
            return  # Already in empty state
        self._home_empty = True
        self._done_actions.clear()

        self.hass.bus.async_fire(EVENT_HOME_EMPTY, {})
        _LOGGER.info("AutoActions: home is now empty -- scheduling actions")

        cfg = self.store.get_auto_actions()
        fp = self.store.get_fake_presence_v2()

        # Schedule each enabled action independently
        if cfg.get(AA_LOCK_ENABLED, True):
            delay = int(cfg.get(AA_LOCK_DELAY, DEFAULT_AA_LOCK_DELAY))
            blocked = fp.get(FP_ACTIVE, False) and fp.get(FP_BLOCK_LOCKS, False)
            self._schedule_action("lock", delay, blocked)

        if cfg.get(AA_ALARM_ENABLED, True):
            delay = int(cfg.get(AA_ALARM_DELAY, DEFAULT_AA_ALARM_DELAY))
            blocked = fp.get(FP_ACTIVE, False) and fp.get(FP_BLOCK_ALARM, True)
            self._schedule_action("alarm", delay, blocked)

        if cfg.get(AA_CAMERA_ENABLED, True):
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
        state = self.hass.states.get(entity_id)
        if state is None or state.state == "not_home":
            _LOGGER.info(
                "AutoActions: arrival confirmation failed for %s (left again) -- timers continue",
                entity_id,
            )
            return

        # Confirmed home -- cancel all pending action tasks
        _LOGGER.info(
            "AutoActions: %s confirmed home after %ds -- cancelling pending timers",
            entity_id, delay,
        )
        await self._cancel_all_action_tasks()
        self._home_empty = False

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
            # Fallback to persistent notification
            self.hass.components.persistent_notification.async_create(
                message,
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

    def _all_persons_away(self) -> bool:
        """Return True if all person.* entities are not_home."""
        persons = self.hass.states.async_all("person")
        if not persons:
            return False
        return all(s.state == "not_home" for s in persons)

    def _all_actions_settled(self) -> bool:
        """Return True when all scheduled action tasks have finished or were skipped."""
        cfg = self.store.get_auto_actions()
        expected: set[str] = set()
        if cfg.get(AA_LOCK_ENABLED, True):
            expected.add("lock")
        if cfg.get(AA_ALARM_ENABLED, True):
            expected.add("alarm")
        if cfg.get(AA_CAMERA_ENABLED, True):
            expected.add("camera")

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
