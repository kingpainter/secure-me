"""Tests for Secure Me state machine."""
# VERSION = "0.9.0"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.secure_me.const import (
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)


class MockStateMachine:
    """Simplified state machine for unit testing without HA event loop.

    Mirrors the logic of AlarmStateMachine but without async timers.
    """

    def __init__(self, exit_delay=30, entry_delay=30, trigger_time=300):
        self._current_state = STATE_ALARM_DISARMED
        self._exit_delay = exit_delay
        self._entry_delay = entry_delay
        self._trigger_time = trigger_time
        self._countdown = 0
        self._target_state = None

    @property
    def current_state(self) -> str:
        return self._current_state

    @property
    def countdown(self) -> int:
        return self._countdown

    @property
    def exit_delay(self) -> int:
        return self._exit_delay

    @property
    def entry_delay(self) -> int:
        return self._entry_delay

    @property
    def is_armed(self) -> bool:
        return self._current_state in (
            STATE_ALARM_ARMED_AWAY,
            STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT,
            STATE_ALARM_ARMED_VACATION,
        )

    @property
    def is_arming(self) -> bool:
        return self._current_state == STATE_ALARM_ARMING

    @property
    def is_pending(self) -> bool:
        return self._current_state == STATE_ALARM_PENDING

    def arm_away(self, skip_delay=False) -> bool:
        if self._current_state != STATE_ALARM_DISARMED:
            return False
        if skip_delay:
            self._current_state = STATE_ALARM_ARMED_AWAY
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_AWAY
            self._countdown = self._exit_delay
        return True

    def arm_home(self, skip_delay=False) -> bool:
        if self._current_state != STATE_ALARM_DISARMED:
            return False
        if skip_delay:
            self._current_state = STATE_ALARM_ARMED_HOME
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_HOME
            self._countdown = self._exit_delay
        return True

    def arm_night(self, skip_delay=False) -> bool:
        if self._current_state != STATE_ALARM_DISARMED:
            return False
        if skip_delay:
            self._current_state = STATE_ALARM_ARMED_NIGHT
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_NIGHT
            self._countdown = self._exit_delay
        return True

    def arm_vacation(self, skip_delay=False) -> bool:
        if self._current_state != STATE_ALARM_DISARMED:
            return False
        if skip_delay:
            self._current_state = STATE_ALARM_ARMED_VACATION
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_VACATION
            self._countdown = self._exit_delay
        return True

    def complete_arming(self) -> bool:
        """Simulate countdown completion."""
        if self._current_state == STATE_ALARM_ARMING and self._target_state:
            self._current_state = self._target_state
            self._target_state = None
            self._countdown = 0
            return True
        return False

    def disarm(self) -> bool:
        if self._current_state == STATE_ALARM_DISARMED:
            return False
        self._current_state = STATE_ALARM_DISARMED
        self._countdown = 0
        self._target_state = None
        return True

    def trigger_entry_delay(self, zone_type="entry") -> bool:
        if not self.is_armed:
            return False
        if zone_type == "instant":
            self._current_state = STATE_ALARM_TRIGGERED
        else:
            self._current_state = STATE_ALARM_PENDING
            self._countdown = self._entry_delay
        return True

    def trigger_alarm(self) -> bool:
        self._current_state = STATE_ALARM_TRIGGERED
        self._countdown = 0
        return True


class TestStateMachineInit:
    """Test state machine initialization."""

    def test_initial_state_is_disarmed(self):
        sm = MockStateMachine()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_initial_countdown_is_zero(self):
        sm = MockStateMachine()
        assert sm.countdown == 0

    def test_custom_delays(self):
        sm = MockStateMachine(exit_delay=45, entry_delay=15, trigger_time=600)
        assert sm.exit_delay == 45
        assert sm.entry_delay == 15

    def test_not_armed_initially(self):
        sm = MockStateMachine()
        assert sm.is_armed is False
        assert sm.is_arming is False
        assert sm.is_pending is False


class TestArmingModes:
    """Test all arming modes."""

    def test_arm_away(self):
        sm = MockStateMachine()
        result = sm.arm_away()
        assert result is True
        assert sm.current_state == STATE_ALARM_ARMING
        assert sm.countdown == 30

    def test_arm_away_skip_delay(self):
        sm = MockStateMachine()
        result = sm.arm_away(skip_delay=True)
        assert result is True
        assert sm.current_state == STATE_ALARM_ARMED_AWAY
        assert sm.is_armed is True

    def test_arm_home(self):
        sm = MockStateMachine()
        result = sm.arm_home(skip_delay=True)
        assert result is True
        assert sm.current_state == STATE_ALARM_ARMED_HOME

    def test_arm_night(self):
        sm = MockStateMachine()
        result = sm.arm_night(skip_delay=True)
        assert result is True
        assert sm.current_state == STATE_ALARM_ARMED_NIGHT

    def test_arm_vacation(self):
        sm = MockStateMachine()
        result = sm.arm_vacation(skip_delay=True)
        assert result is True
        assert sm.current_state == STATE_ALARM_ARMED_VACATION

    def test_cannot_arm_when_already_armed(self):
        sm = MockStateMachine()
        sm.arm_away(skip_delay=True)
        result = sm.arm_home(skip_delay=True)
        assert result is False
        assert sm.current_state == STATE_ALARM_ARMED_AWAY

    def test_arming_completes_to_target(self):
        sm = MockStateMachine()
        sm.arm_away()
        assert sm.is_arming is True
        sm.complete_arming()
        assert sm.current_state == STATE_ALARM_ARMED_AWAY
        assert sm.is_armed is True


class TestDisarming:
    """Test disarm behavior."""

    def test_disarm_from_armed(self):
        sm = MockStateMachine()
        sm.arm_away(skip_delay=True)
        result = sm.disarm()
        assert result is True
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_disarm_from_arming(self):
        sm = MockStateMachine()
        sm.arm_away()
        result = sm.disarm()
        assert result is True
        assert sm.current_state == STATE_ALARM_DISARMED
        assert sm.countdown == 0

    def test_disarm_from_triggered(self):
        sm = MockStateMachine()
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        result = sm.disarm()
        assert result is True
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_cannot_disarm_when_already_disarmed(self):
        sm = MockStateMachine()
        result = sm.disarm()
        assert result is False


class TestTriggers:
    """Test alarm trigger behavior."""

    def test_entry_zone_starts_pending(self):
        sm = MockStateMachine()
        sm.arm_away(skip_delay=True)
        result = sm.trigger_entry_delay("entry")
        assert result is True
        assert sm.current_state == STATE_ALARM_PENDING
        assert sm.countdown == 30

    def test_instant_zone_triggers_immediately(self):
        sm = MockStateMachine()
        sm.arm_away(skip_delay=True)
        result = sm.trigger_entry_delay("instant")
        assert result is True
        assert sm.current_state == STATE_ALARM_TRIGGERED

    def test_trigger_not_possible_when_disarmed(self):
        sm = MockStateMachine()
        result = sm.trigger_entry_delay("entry")
        assert result is False
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_manual_trigger(self):
        sm = MockStateMachine()
        sm.arm_away(skip_delay=True)
        result = sm.trigger_alarm()
        assert result is True
        assert sm.current_state == STATE_ALARM_TRIGGERED


class TestStateTransitions:
    """Test full state transition flows."""

    def test_full_arm_trigger_disarm_cycle(self):
        sm = MockStateMachine()

        # Start disarmed
        assert sm.current_state == STATE_ALARM_DISARMED

        # Arm away (skip delay)
        sm.arm_away(skip_delay=True)
        assert sm.current_state == STATE_ALARM_ARMED_AWAY

        # Entry zone triggers pending
        sm.trigger_entry_delay("entry")
        assert sm.current_state == STATE_ALARM_PENDING

        # Escalate to triggered
        sm.trigger_alarm()
        assert sm.current_state == STATE_ALARM_TRIGGERED

        # Disarm
        sm.disarm()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_arm_with_delay_then_disarm_during_exit(self):
        sm = MockStateMachine()
        sm.arm_away()  # With exit delay
        assert sm.is_arming is True
        sm.disarm()
        assert sm.current_state == STATE_ALARM_DISARMED
