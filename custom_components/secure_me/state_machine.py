"""State machine for Secure Me alarm system."""
# VERSION = "0.3.6"

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_time
import homeassistant.util.dt as dt_util

from .const import (
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    ZONE_TYPE_ENTRY,
    ZONE_TYPE_INSTANT,
)

_LOGGER = logging.getLogger(__name__)


class AlarmStateMachine:
    """State machine for alarm system with delays and countdowns."""

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
        self._cancel_timer: Callable | None = None

        self._state_change_callbacks: list[Callable] = []
        self._countdown_callbacks: list[Callable] = []

        _LOGGER.info(
            "State machine initialized (exit=%ds, entry=%ds, trigger=%ds)",
            exit_delay,
            entry_delay,
            trigger_time,
        )

    @property
    def current_state(self) -> str:
        """Return current state."""
        return self._current_state

    @property
    def countdown(self) -> int:
        """Return current countdown value."""
        return self._countdown

    @property
    def exit_delay(self) -> int:
        """Return exit delay."""
        return self._exit_delay

    @property
    def entry_delay(self) -> int:
        """Return entry delay."""
        return self._entry_delay

    @property
    def is_armed(self) -> bool:
        """Return if alarm is armed."""
        return self._current_state in [
            STATE_ALARM_ARMED_AWAY,
            STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT,
            STATE_ALARM_ARMED_VACATION,
        ]

    @property
    def is_arming(self) -> bool:
        """Return if alarm is arming."""
        return self._current_state == STATE_ALARM_ARMING

    @property
    def is_pending(self) -> bool:
        """Return if alarm is pending."""
        return self._current_state == STATE_ALARM_PENDING

    @property
    def is_triggered(self) -> bool:
        """Return if alarm is triggered."""
        return self._current_state == STATE_ALARM_TRIGGERED

    def update_config(self, exit_delay: int, entry_delay: int, trigger_time: int = 300) -> None:
        """Update delays."""
        self._exit_delay = exit_delay
        self._entry_delay = entry_delay
        self._trigger_time = trigger_time
        _LOGGER.info(
            "State machine delays updated (exit=%ds, entry=%ds)",
            exit_delay,
            entry_delay,
        )

    def add_state_change_callback(self, callback: Callable) -> None:
        """Add state change callback."""
        self._state_change_callbacks.append(callback)

    def add_countdown_callback(self, callback: Callable) -> None:
        """Add countdown callback."""
        self._countdown_callbacks.append(callback)

    async def _notify_state_change(self) -> None:
        """Notify all state change callbacks."""
        for callback in self._state_change_callbacks:
            try:
                await callback(self._current_state, self._countdown)
            except Exception as err:
                _LOGGER.error("Error in state change callback: %s", err)

    async def _notify_countdown(self) -> None:
        """Notify all countdown callbacks."""
        for callback in self._countdown_callbacks:
            try:
                await callback(self._countdown)
            except Exception as err:
                _LOGGER.error("Error in countdown callback: %s", err)

    async def _set_state(self, new_state: str) -> None:
        """Set state and notify callbacks."""
        old_state = self._current_state
        self._current_state = new_state

        _LOGGER.info("State changed: %s → %s", old_state, new_state)
        await self._notify_state_change()

    def _cancel_countdown(self) -> None:
        """Cancel active countdown."""
        if self._countdown_task and not self._countdown_task.done():
            self._countdown_task.cancel()
            self._countdown_task = None

        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None

        self._countdown = 0
        self._target_state = None

    async def _countdown_timer(self, target_state: str, duration: int) -> None:
        """Run countdown timer."""
        _LOGGER.info("Starting countdown: %ds → %s", duration, target_state)
        self._countdown = duration
        self._target_state = target_state

        try:
            while self._countdown > 0:
                await self._notify_countdown()
                await asyncio.sleep(1)
                self._countdown -= 1

            # Countdown finished
            _LOGGER.info("Countdown finished, transitioning to %s", target_state)
            self._countdown = 0
            self._target_state = None
            await self._set_state(target_state)

        except asyncio.CancelledError:
            _LOGGER.info("Countdown cancelled")
            self._countdown = 0
            self._target_state = None
            raise

    async def arm_away(self, skip_delay: bool = False) -> bool:
        """Arm in away mode."""
        if self.is_armed:
            _LOGGER.warning("Cannot arm - already armed")
            return False

        self._cancel_countdown()

        if skip_delay or self._exit_delay == 0:
            await self._set_state(STATE_ALARM_ARMED_AWAY)
        else:
            await self._set_state(STATE_ALARM_ARMING)
            self._countdown_task = asyncio.create_task(
                self._countdown_timer(STATE_ALARM_ARMED_AWAY, self._exit_delay)
            )

        return True

    async def arm_home(self, skip_delay: bool = False) -> bool:
        """Arm in home mode."""
        if self.is_armed:
            _LOGGER.warning("Cannot arm - already armed")
            return False

        self._cancel_countdown()

        if skip_delay or self._exit_delay == 0:
            await self._set_state(STATE_ALARM_ARMED_HOME)
        else:
            await self._set_state(STATE_ALARM_ARMING)
            self._countdown_task = asyncio.create_task(
                self._countdown_timer(STATE_ALARM_ARMED_HOME, self._exit_delay)
            )

        return True

    async def arm_night(self, skip_delay: bool = False) -> bool:
        """Arm in night mode."""
        if self.is_armed:
            _LOGGER.warning("Cannot arm - already armed")
            return False

        self._cancel_countdown()

        if skip_delay or self._exit_delay == 0:
            await self._set_state(STATE_ALARM_ARMED_NIGHT)
        else:
            await self._set_state(STATE_ALARM_ARMING)
            self._countdown_task = asyncio.create_task(
                self._countdown_timer(STATE_ALARM_ARMED_NIGHT, self._exit_delay)
            )

        return True

    async def arm_vacation(self, skip_delay: bool = False) -> bool:
        """Arm in vacation mode."""
        if self.is_armed:
            _LOGGER.warning("Cannot arm - already armed")
            return False

        self._cancel_countdown()

        if skip_delay or self._exit_delay == 0:
            await self._set_state(STATE_ALARM_ARMED_VACATION)
        else:
            await self._set_state(STATE_ALARM_ARMING)
            self._countdown_task = asyncio.create_task(
                self._countdown_timer(STATE_ALARM_ARMED_VACATION, self._exit_delay)
            )

        return True

    async def disarm(self) -> bool:
        """Disarm alarm."""
        if self._current_state == STATE_ALARM_DISARMED:
            _LOGGER.warning("Already disarmed")
            return False

        self._cancel_countdown()
        await self._set_state(STATE_ALARM_DISARMED)
        return True

    async def trigger_entry_delay(self, zone_type: str) -> bool:
        """Trigger entry delay (zone breached while armed)."""
        if not self.is_armed:
            _LOGGER.warning("Cannot trigger entry delay - not armed")
            return False

        if zone_type == ZONE_TYPE_INSTANT:
            # Instant zones trigger immediately
            _LOGGER.warning("Instant zone triggered - no delay!")
            await self.trigger_alarm("instant_zone")
            return True

        if zone_type == ZONE_TYPE_ENTRY and self._entry_delay > 0:
            # Entry zones trigger pending state
            _LOGGER.warning("Entry zone triggered - starting entry delay")
            self._cancel_countdown()
            await self._set_state(STATE_ALARM_PENDING)
            self._countdown_task = asyncio.create_task(
                self._countdown_timer(STATE_ALARM_TRIGGERED, self._entry_delay)
            )
            return True

        # Interior/perimeter zones trigger immediately when armed away
        _LOGGER.warning("Zone triggered - immediate alarm")
        await self.trigger_alarm(f"zone_{zone_type}")
        return True

    async def trigger_alarm(self, source: str) -> bool:
        """Trigger alarm immediately."""
        if self._current_state == STATE_ALARM_TRIGGERED:
            _LOGGER.warning("Already triggered")
            return False

        _LOGGER.warning("ALARM TRIGGERED! Source: %s", source)
        self._cancel_countdown()
        await self._set_state(STATE_ALARM_TRIGGERED)

        # Start trigger timer (alarm will stay triggered for trigger_time)
        if self._trigger_time > 0:
            _LOGGER.info("Alarm will auto-reset after %ds", self._trigger_time)
            # Note: Auto-reset not implemented yet, will be in Phase 2

        return True

    async def cancel_pending(self) -> bool:
        """Cancel pending state (disarm during entry delay)."""
        if not self.is_pending:
            return False

        _LOGGER.info("Pending state cancelled")
        self._cancel_countdown()
        await self._set_state(STATE_ALARM_DISARMED)
        return True

    def cleanup(self) -> None:
        """Cleanup state machine."""
        self._cancel_countdown()
        self._state_change_callbacks.clear()
        self._countdown_callbacks.clear()
        _LOGGER.info("State machine cleaned up")
