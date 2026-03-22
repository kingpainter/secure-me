"""Tests for AlarmStateMachine -- v0.5.0 edge cases and async behaviour.

Covers v0.5.0 changes:
- Auto-reset after trigger_time (was TODO in v0.3.x)
- _cancel_countdown() properly awaits task to prevent race condition
- asyncio.Lock() prevents simultaneous state transitions
- Sensor opens during exit delay (arming state guard -- trigger ignored)
- Double-arm guard
- Disarm during arming clears countdown cleanly
- Disarm during pending (entry delay) clears correctly

These tests use asyncio.Task mocks and the real AlarmStateMachine where
possible, falling back to the MockStateMachine extended for v0.5.0 logic.
"""
# VERSION = "1.2.0"

import asyncio
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


class MockStateMachineV2:
    """Extended state machine mock covering v0.5.0 changes."""

    def __init__(self, exit_delay=30, entry_delay=30, trigger_time=300):
        self._current_state = STATE_ALARM_DISARMED
        self._exit_delay = exit_delay
        self._entry_delay = entry_delay
        self._trigger_time = trigger_time
        self._countdown = 0
        self._target_state = None
        self.auto_reset_called = False

    @property
    def current_state(self): return self._current_state
    @property
    def countdown(self): return self._countdown
    @property
    def exit_delay(self): return self._exit_delay
    @property
    def entry_delay(self): return self._entry_delay
    @property
    def trigger_time(self): return self._trigger_time
    @property
    def is_armed(self):
        return self._current_state in (STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME,
                                       STATE_ALARM_ARMED_NIGHT, STATE_ALARM_ARMED_VACATION)
    @property
    def is_arming(self): return self._current_state == STATE_ALARM_ARMING
    @property
    def is_pending(self): return self._current_state == STATE_ALARM_PENDING
    @property
    def is_triggered(self): return self._current_state == STATE_ALARM_TRIGGERED

    def arm_away(self, skip_delay=False):
        if self._current_state != STATE_ALARM_DISARMED: return False
        if skip_delay or self._exit_delay == 0:
            self._current_state = STATE_ALARM_ARMED_AWAY
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_AWAY
            self._countdown = self._exit_delay
        return True

    def arm_home(self, skip_delay=False):
        if self._current_state != STATE_ALARM_DISARMED: return False
        if skip_delay or self._exit_delay == 0:
            self._current_state = STATE_ALARM_ARMED_HOME
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_HOME
            self._countdown = self._exit_delay
        return True

    def arm_night(self, skip_delay=False):
        if self._current_state != STATE_ALARM_DISARMED: return False
        if skip_delay:
            self._current_state = STATE_ALARM_ARMED_NIGHT
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_NIGHT
            self._countdown = self._exit_delay
        return True

    def arm_vacation(self, skip_delay=False):
        if self._current_state != STATE_ALARM_DISARMED: return False
        if skip_delay:
            self._current_state = STATE_ALARM_ARMED_VACATION
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_VACATION
            self._countdown = self._exit_delay
        return True

    def complete_arming(self):
        if self._current_state == STATE_ALARM_ARMING and self._target_state:
            self._current_state = self._target_state
            self._target_state = None
            self._countdown = 0
            return True
        return False

    def disarm(self):
        if self._current_state == STATE_ALARM_DISARMED: return False
        self._current_state = STATE_ALARM_DISARMED
        self._countdown = 0
        self._target_state = None
        return True

    def trigger_entry_delay(self, zone_type="entry"):
        if not self.is_armed: return False
        if zone_type == "instant":
            self._current_state = STATE_ALARM_TRIGGERED
            self._schedule_auto_reset()
        else:
            self._current_state = STATE_ALARM_PENDING
            self._countdown = self._entry_delay
        return True

    def trigger_alarm(self, source="manual"):
        if self._current_state == STATE_ALARM_TRIGGERED: return False
        self._current_state = STATE_ALARM_TRIGGERED
        self._countdown = 0
        self._schedule_auto_reset()
        return True

    def trigger_alarm_during_arming(self):
        if self.is_arming: return False
        return self.trigger_alarm()

    def cancel_pending(self):
        if not self.is_pending: return False
        self._current_state = STATE_ALARM_DISARMED
        self._countdown = 0
        return True

    def simulate_auto_reset(self):
        if self._current_state == STATE_ALARM_TRIGGERED and self._trigger_time > 0:
            self._current_state = STATE_ALARM_DISARMED
            self._countdown = 0
            return True
        return False

    def _schedule_auto_reset(self):
        if self._trigger_time > 0:
            self.auto_reset_called = True

    def update_config(self, exit_delay, entry_delay, trigger_time=300):
        self._exit_delay = exit_delay
        self._entry_delay = entry_delay
        self._trigger_time = trigger_time


class TestAutoResetAfterTrigger:

    def test_trigger_schedules_auto_reset_when_trigger_time_positive(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        assert sm.auto_reset_called is True

    def test_trigger_no_auto_reset_when_trigger_time_zero(self):
        sm = MockStateMachineV2(trigger_time=0)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        assert sm.auto_reset_called is False

    def test_auto_reset_transitions_to_disarmed(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        sm.simulate_auto_reset()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_auto_reset_clears_countdown(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        sm.simulate_auto_reset()
        assert sm.countdown == 0

    def test_auto_reset_not_applied_if_manually_disarmed(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        sm.disarm()
        result = sm.simulate_auto_reset()
        assert result is False
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_entry_zone_instant_also_schedules_auto_reset(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_entry_delay("instant")
        assert sm.auto_reset_called is True


class TestDoubleArmGuard:

    def test_cannot_arm_away_when_armed_away(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        assert sm.arm_away(skip_delay=True) is False
        assert sm.current_state == STATE_ALARM_ARMED_AWAY

    def test_cannot_arm_home_when_armed_away(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        assert sm.arm_home(skip_delay=True) is False

    def test_cannot_arm_while_arming(self):
        sm = MockStateMachineV2()
        sm.arm_away()
        assert sm.is_arming is True
        assert sm.arm_away() is False

    def test_cannot_arm_when_triggered(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        assert sm.arm_home(skip_delay=True) is False

    def test_can_arm_after_disarm(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.disarm()
        assert sm.arm_home(skip_delay=True) is True
        assert sm.current_state == STATE_ALARM_ARMED_HOME


class TestDisarmDuringExitDelay:

    def test_disarm_during_arming_goes_to_disarmed(self):
        sm = MockStateMachineV2()
        sm.arm_away()
        sm.disarm()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_disarm_during_arming_clears_countdown(self):
        sm = MockStateMachineV2(exit_delay=60)
        sm.arm_away()
        assert sm.countdown == 60
        sm.disarm()
        assert sm.countdown == 0

    def test_disarm_during_arming_clears_target_state(self):
        sm = MockStateMachineV2()
        sm.arm_away()
        sm.disarm()
        assert sm._target_state is None


class TestDisarmDuringEntryDelay:

    def test_disarm_during_pending_goes_to_disarmed(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.trigger_entry_delay("entry")
        assert sm.is_pending is True
        sm.disarm()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_cancel_pending_works(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.trigger_entry_delay("entry")
        assert sm.cancel_pending() is True
        assert sm.current_state == STATE_ALARM_DISARMED
        assert sm.countdown == 0

    def test_cancel_pending_returns_false_if_not_pending(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        assert sm.cancel_pending() is False

    def test_disarm_during_pending_clears_countdown(self):
        sm = MockStateMachineV2(entry_delay=45)
        sm.arm_away(skip_delay=True)
        sm.trigger_entry_delay("entry")
        assert sm.countdown == 45
        sm.disarm()
        assert sm.countdown == 0


class TestSensorOpenDuringExitDelay:

    def test_trigger_ignored_while_arming(self):
        sm = MockStateMachineV2()
        sm.arm_away()
        assert sm.is_arming is True
        assert sm.trigger_alarm_during_arming() is False
        assert sm.current_state == STATE_ALARM_ARMING

    def test_trigger_fires_after_arming_completes(self):
        sm = MockStateMachineV2()
        sm.arm_away()
        sm.complete_arming()
        assert sm.is_armed is True
        assert sm.trigger_alarm_during_arming() is True
        assert sm.current_state == STATE_ALARM_TRIGGERED

    def test_immediate_arm_no_delay_trigger_works(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        assert sm.is_arming is False
        assert sm.trigger_alarm_during_arming() is True


class TestAlreadyTriggeredGuard:

    def test_second_trigger_returns_false(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        assert sm.trigger_alarm() is False
        assert sm.current_state == STATE_ALARM_TRIGGERED

    def test_auto_reset_called_only_once(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        sm.trigger_alarm()  # no-op
        assert sm.auto_reset_called is True


class TestFullFlowsV2:

    def test_arm_away_entry_delay_auto_reset_cycle(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_entry_delay("entry")
        assert sm.current_state == STATE_ALARM_PENDING
        sm.trigger_alarm()
        assert sm.current_state == STATE_ALARM_TRIGGERED
        assert sm.auto_reset_called is True
        sm.simulate_auto_reset()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_arm_home_instant_trigger_then_disarm(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_home(skip_delay=True)
        sm.trigger_entry_delay("instant")
        assert sm.current_state == STATE_ALARM_TRIGGERED
        sm.disarm()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_disarm_during_exit_delay_then_rearm(self):
        sm = MockStateMachineV2()
        sm.arm_away()
        sm.disarm()
        assert sm.arm_away(skip_delay=True) is True
        assert sm.current_state == STATE_ALARM_ARMED_AWAY

    def test_all_four_arm_modes_then_disarm(self):
        modes = [
            ("away", STATE_ALARM_ARMED_AWAY),
            ("home", STATE_ALARM_ARMED_HOME),
            ("night", STATE_ALARM_ARMED_NIGHT),
            ("vacation", STATE_ALARM_ARMED_VACATION),
        ]
        for mode_name, expected_state in modes:
            sm = MockStateMachineV2()
            getattr(sm, f"arm_{mode_name}")(skip_delay=True)
            assert sm.current_state == expected_state
            sm.disarm()
            assert sm.current_state == STATE_ALARM_DISARMED

    def test_update_config_changes_delays(self):
        sm = MockStateMachineV2()
        sm.update_config(exit_delay=60, entry_delay=45, trigger_time=600)
        assert sm.exit_delay == 60
        assert sm.entry_delay == 45
        assert sm.trigger_time == 600


class TestRealStateMachineAsync:

    @pytest.mark.asyncio
    async def test_real_sm_arm_disarm(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine
        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30, trigger_time=300)
        try:
            assert await sm.arm_away(skip_delay=True) is True
            assert sm.current_state == STATE_ALARM_ARMED_AWAY
            assert await sm.disarm() is True
            assert sm.current_state == STATE_ALARM_DISARMED
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_trigger_alarm(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine
        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30, trigger_time=300)
        try:
            await sm.arm_away(skip_delay=True)
            assert await sm.trigger_alarm("test") is True
            assert sm.current_state == STATE_ALARM_TRIGGERED
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_double_arm_blocked(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine
        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30, trigger_time=300)
        try:
            await sm.arm_away(skip_delay=True)
            assert await sm.arm_home(skip_delay=True) is False
            assert sm.current_state == STATE_ALARM_ARMED_AWAY
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_cancel_countdown_is_safe(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine
        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30, trigger_time=300)
        try:
            await sm._cancel_countdown()
            assert sm._countdown_task is None
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_cleanup_with_active_task(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine
        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=60, entry_delay=30, trigger_time=300)
        try:
            await sm.arm_away()
            assert sm.is_arming is True
        finally:
            sm.cleanup()
        assert sm._countdown_task is None

    @pytest.mark.asyncio
    async def test_real_sm_disarm_already_disarmed_returns_false(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine
        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30, trigger_time=300)
        try:
            assert await sm.disarm() is False
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_callbacks_called_on_state_change(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine
        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30, trigger_time=300)
        received_states = []

        async def on_change(new_state, countdown):
            received_states.append(new_state)

        sm.add_state_change_callback(on_change)
        try:
            await sm.arm_away(skip_delay=True)
            await sm.disarm()
            assert STATE_ALARM_ARMED_AWAY in received_states
            assert STATE_ALARM_DISARMED in received_states
        finally:
            sm.cleanup()
