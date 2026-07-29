"""State machine for Secure Me alarm system."""
# VERSION = "1.5.3"

import asyncio
import logging
from typing import Callable

from homeassistant.core import HomeAssistant

from .const import (
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_ARMED_HOME_ALONE,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    ZONE_TYPE_ENTRY,
    ZONE_TYPE_INSTANT,
)

_LOGGER = logging.getLogger(__name__)

# Armed states for quick lookup
_ARMED_STATES = frozenset({
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_ARMED_HOME_ALONE,
})


class AlarmStateMachine:
    """State machine for alarm system with delays, countdowns and edge case handling.

    v0.5.0 edge case fixes:
    - Race condition: countdown task is properly awaited on cancel
    - Auto-reset after trigger_time (was TODO in v0.3.x)
    - Disarm during arming (exit delay) handled cleanly
    - Double-arm guard improved
    """

    def __init__(
        self,
        hass: HomeAssistant,
        exit_delay: int = 30,
        entry_delay: int = 30,
        trigger_time: int = 300,
    ) -> None:
        """Initialize state machine."""
        self.hass = hass
        self._exit_delay = exit_delay
        self._entry_delay = entry_delay
        self._trigger_time = trigger_time

        self._current_state = STATE_ALARM_DISARMED
        self._target_state: str | None = None
        self._countdown: int = 0
        self._countdown_task: asyncio.Task | None = None
        self._trigger_reset_task: asyncio.Task | None = None

        self._state_change_callbacks: list[Callable] = []
        self._countdown_callbacks: list[Callable] = []

        # Lock to prevent race conditions on rapid arm/disarm
        self._transition_lock = asyncio.Lock()

        _LOGGER.info(
            "State machine initialized (exit=%ds, entry=%ds, trigger=%ds)",
            exit_delay, entry_delay, trigger_time,
        )

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def current_state(self) -> str:
        return self._current_state

    @property
    def countdown(self) -> int:
        return self._countdown

    @property
    def target_state(self) -> str | None:
        """The arm mode being transitioned to during an exit-delay countdown.

        Only meaningful while current_state == 'arming'. None otherwise.
        Added so the frontend can show e.g. 'Tilkobler Borte... 12s' during
        the countdown instead of just a bare number.
        """
        return self._target_state

    @property
    def exit_delay(self) -> int:
        return self._exit_delay

    @property
    def entry_delay(self) -> int:
        return self._entry_delay

    @property
    def is_armed(self) -> bool:
        return self._current_state in _ARMED_STATES

    @property
    def is_arming(self) -> bool:
        return self._current_state == STATE_ALARM_ARMING

    @property
    def is_pending(self) -> bool:
        return self._current_state == STATE_ALARM_PENDING

    @property
    def is_triggered(self) -> bool:
        return self._current_state == STATE_ALARM_TRIGGERED

    def update_config(self, exit_delay: int, entry_delay: int, trigger_time: int = 300) -> None:
        """Update delays."""
        self._exit_delay = exit_delay
        self._entry_delay = entry_delay
        self._trigger_time = trigger_time
        _LOGGER.info("State machine delays updated (exit=%ds, entry=%ds)", exit_delay, entry_delay)

    def add_state_change_callback(self, callback: Callable) -> None:
        self._state_change_callbacks.append(callback)

    def add_countdown_callback(self, callback: Callable) -> None:
        self._countdown_callbacks.append(callback)

    # ── Internal ─────────────────────────────────────────────────────────────

    async def _notify_state_change(self) -> None:
        for cb in self._state_change_callbacks:
            try:
                await cb(self._current_state, self._countdown)
            except Exception as err:
                _LOGGER.error("Error in state change callback: %s", err)

    async def _notify_countdown(self) -> None:
        for cb in self._countdown_callbacks:
            try:
                await cb(self._countdown)
            except Exception as err:
                _LOGGER.error("Error in countdown callback: %s", err)

    async def _set_state(self, new_state: str) -> None:
        old_state = self._current_state
        self._current_state = new_state
        _LOGGER.info("State changed: %s -> %s", old_state, new_state)
        await self._notify_state_change()

    async def _cancel_countdown(self) -> None:
        """Cancel active countdown and await task completion.

        EDGE CASE FIX: Previously used synchronous cancel without await,
        which could leave the task running for one more loop iteration,
        causing a race condition on rapid arm -> disarm -> arm sequences.
        """
        task = self._countdown_task
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._countdown_task = None

        task = self._trigger_reset_task
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._trigger_reset_task = None

        self._countdown = 0
        self._target_state = None

    async def skip_current_countdown(self) -> bool:
        """Skip the active exit/entry countdown and finish immediately.

        v1.4.3 (Alarmo-inspired): Power-user feature to bypass an in-progress
        delay. Useful when you arm with 30s exit delay and then realise you
        already locked the door so you want it armed NOW.

        Returns True if a countdown was active and was skipped to its
        target state. Returns False if no countdown was running.

        Behaviour:
        - During exit delay (state=arming): finish to target armed_* state.
        - During entry delay (state=pending): trigger alarm immediately.
        - In any other state: no-op.

        The countdown task is cancelled and the target state is applied via
        the same _set_state path as a natural countdown completion, so all
        state-change callbacks fire normally.
        """
        async with self._transition_lock:
            target = self._target_state
            task = self._countdown_task
            if not target or not task or task.done():
                _LOGGER.debug("skip_delay called with no active countdown")
                return False

            _LOGGER.info(
                "Skipping countdown (%ds remaining) -> %s",
                self._countdown, target,
            )
            # Cancel timer task and await it so we don't race with its
            # natural completion.
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self._countdown_task = None
            self._countdown = 0
            self._target_state = None

            # Apply the target state via the same path as natural completion.
            await self._set_state(target)
            return True

    async def _countdown_timer(self, target_state: str, duration: int) -> None:
        """Run countdown timer and transition to target state when done."""
        _LOGGER.info("Starting countdown: %ds -> %s", duration, target_state)
        self._countdown = duration
        self._target_state = target_state
        try:
            while self._countdown > 0:
                await self._notify_countdown()
                await asyncio.sleep(1)
                self._countdown -= 1
            _LOGGER.info("Countdown finished, transitioning to %s", target_state)
            self._countdown = 0
            self._target_state = None
            await self._set_state(target_state)
        except asyncio.CancelledError:
            _LOGGER.info("Countdown cancelled")
            self._countdown = 0
            self._target_state = None
            raise

    async def _trigger_reset_timer(self) -> None:
        """Auto-reset alarm after trigger_time seconds.

        EDGE CASE FIX: Previously this was a TODO — alarm would stay in
        triggered state forever if never disarmed. Now auto-resets to
        disarmed after trigger_time, matching real alarm panel behaviour.
        """
        try:
            _LOGGER.info("Alarm will auto-reset after %ds", self._trigger_time)
            await asyncio.sleep(self._trigger_time)
            if self._current_state == STATE_ALARM_TRIGGERED:
                _LOGGER.warning("Alarm auto-reset after %ds (not manually disarmed)", self._trigger_time)
                self._countdown = 0
                await self._set_state(STATE_ALARM_DISARMED)
        except asyncio.CancelledError:
            pass

    # ── Public API ───────────────────────────────────────────────────────────

    async def _arm(self, target_state: str, skip_delay: bool = False) -> bool:
        """Shared arm logic for all arm modes (away/home/night/vacation/home_alone).

        Kept as a single implementation so a future fix to the arm flow (e.g.
        a countdown or lock edge case) only has to be made once, instead of
        in five near-identical copies that can drift out of sync.
        """
        async with self._transition_lock:
            if self.is_armed:
                _LOGGER.warning("Cannot arm - already armed in state %s", self._current_state)
                return False
            await self._cancel_countdown()
            if skip_delay or self._exit_delay == 0:
                await self._set_state(target_state)
            else:
                await self._set_state(STATE_ALARM_ARMING)
                self._countdown_task = asyncio.create_task(
                    self._countdown_timer(target_state, self._exit_delay)
                )
            return True

    async def arm_away(self, skip_delay: bool = False) -> bool:
        """Arm in away mode."""
        return await self._arm(STATE_ALARM_ARMED_AWAY, skip_delay)

    async def arm_home(self, skip_delay: bool = False) -> bool:
        """Arm in home mode."""
        return await self._arm(STATE_ALARM_ARMED_HOME, skip_delay)

    async def arm_night(self, skip_delay: bool = False) -> bool:
        """Arm in night mode."""
        return await self._arm(STATE_ALARM_ARMED_NIGHT, skip_delay)

    async def arm_vacation(self, skip_delay: bool = False) -> bool:
        """Arm in vacation mode."""
        return await self._arm(STATE_ALARM_ARMED_VACATION, skip_delay)

    async def arm_home_alone(self, skip_delay: bool = False) -> bool:
        """Arm in home alone mode (children supervised, cameras on, motion visual-only)."""
        return await self._arm(STATE_ALARM_ARMED_HOME_ALONE, skip_delay)

    async def disarm(self) -> bool:
        """Disarm alarm."""
        async with self._transition_lock:
            if self._current_state == STATE_ALARM_DISARMED:
                _LOGGER.warning("Already disarmed")
                return False
            await self._cancel_countdown()
            await self._set_state(STATE_ALARM_DISARMED)
            return True

    async def trigger_entry_delay(self, zone_type: str) -> bool:
        """Trigger entry delay (zone breached while armed).

        RACE FIX: now runs under _transition_lock so a simultaneous
        disarm()/arm_*() call can't interleave with a sensor trigger and
        corrupt _countdown_task/_target_state. Internally calls
        _trigger_alarm_locked() rather than the public trigger_alarm(),
        since asyncio.Lock is not re-entrant and we already hold the lock.
        """
        async with self._transition_lock:
            if not self.is_armed:
                _LOGGER.warning("Cannot trigger entry delay - not armed (state=%s)", self._current_state)
                return False

            if zone_type == ZONE_TYPE_INSTANT:
                _LOGGER.warning("Instant zone triggered - no delay!")
                await self._trigger_alarm_locked("instant_zone")
                return True

            if zone_type == ZONE_TYPE_ENTRY and self._entry_delay > 0:
                _LOGGER.warning("Entry zone triggered - starting %ds entry delay", self._entry_delay)
                await self._cancel_countdown()
                await self._set_state(STATE_ALARM_PENDING)
                self._countdown_task = asyncio.create_task(
                    self._countdown_timer(STATE_ALARM_TRIGGERED, self._entry_delay)
                )
                return True

            _LOGGER.warning("Zone type '%s' triggered - immediate alarm", zone_type)
            await self._trigger_alarm_locked(f"zone_{zone_type}")
            return True

    async def _trigger_alarm_locked(self, source: str) -> bool:
        """Trigger alarm immediately. Caller must already hold _transition_lock."""
        if self._current_state == STATE_ALARM_TRIGGERED:
            _LOGGER.warning("Already triggered")
            return False

        _LOGGER.warning("ALARM TRIGGERED! Source: %s", source)
        await self._cancel_countdown()
        await self._set_state(STATE_ALARM_TRIGGERED)

        # EDGE CASE FIX: Auto-reset after trigger_time (was TODO in v0.3.x)
        if self._trigger_time > 0:
            self._trigger_reset_task = asyncio.create_task(
                self._trigger_reset_timer()
            )

        return True

    async def trigger_alarm(self, source: str) -> bool:
        """Trigger alarm immediately (public entry point -- acquires the lock).

        RACE FIX: previously ran without _transition_lock, so a concurrent
        disarm() could interleave with this call. Now serialized like every
        other state transition.
        """
        async with self._transition_lock:
            return await self._trigger_alarm_locked(source)

    async def cancel_pending(self) -> bool:
        """Cancel pending state (disarm during entry delay).

        RACE FIX: now runs under _transition_lock, matching every other
        state transition.
        """
        async with self._transition_lock:
            if not self.is_pending:
                return False
            _LOGGER.info("Pending state cancelled (disarmed during entry delay)")
            await self._cancel_countdown()
            await self._set_state(STATE_ALARM_DISARMED)
            return True

    def restore_state(self, state: str) -> None:
        """Restore state directly after HA restart — no callbacks, no delays.

        Called once during setup before any listeners are attached.
        Only restores stable armed/disarmed states. Transient states
        (arming, pending, triggered) are intentionally reset to disarmed
        because the countdown context is lost across restarts.
        """
        restorable = {
            STATE_ALARM_DISARMED,
            STATE_ALARM_ARMED_AWAY,
            STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT,
            STATE_ALARM_ARMED_VACATION,
            STATE_ALARM_ARMED_HOME_ALONE,
        }
        if state not in restorable:
            _LOGGER.warning(
                "State '%s' is not restorable (transient) — defaulting to disarmed", state
            )
            self._current_state = STATE_ALARM_DISARMED
        else:
            self._current_state = state
            _LOGGER.info("State machine restored to '%s'", state)

    def cleanup(self) -> None:
        """Cleanup state machine — cancel tasks synchronously on shutdown."""
        if self._countdown_task and not self._countdown_task.done():
            self._countdown_task.cancel()
        if self._trigger_reset_task and not self._trigger_reset_task.done():
            self._trigger_reset_task.cancel()
        self._countdown_task = None
        self._trigger_reset_task = None
        self._state_change_callbacks.clear()
        self._countdown_callbacks.clear()
        _LOGGER.info("State machine cleaned up")
