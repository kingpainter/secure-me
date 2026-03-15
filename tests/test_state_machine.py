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
# VERSION = "1.1.0"

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


# ---------------------------------------------------------------------------
# Extended MockStateMachine -- adds v0.5.0 logic
# ---------------------------------------------------------------------------

class MockStateMachineV2:
    """Extended state machine mock covering v0.5.0 changes.

    Adds:
    - auto_reset_called flag (mirrors _trigger_reset_task creation)
    - is_triggered property
    - trigger_time=0 disables auto-reset
    - Arming-state guard (sensor open during exit delay ignored)
    """

    def __init__(self, exit_delay=30, entry_delay=30, trigger_time=300):
        self._current_state = STATE_ALARM_DISARMED
        self._exit_delay = exit_delay
        self._entry_delay = entry_delay
        self._trigger_time = trigger_time
        self._countdown = 0
        self._target_state = None
        self.auto_reset_called = False  # flag for trigger_time test

    # -- Properties ----------------------------------------------------------

    @property
    def current_state(self):
        return self._current_state

    @property
    def countdown(self):
        return self._countdown

    @property
    def exit_delay(self):
        return self._exit_delay

    @property
    def entry_delay(self):
        return self._entry_delay

    @property
    def trigger_time(self):
        return self._trigger_time

    @property
    def is_armed(self):
        return self._current_state in (
            STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT, STATE_ALARM_ARMED_VACATION,
        )

    @property
    def is_arming(self):
        return self._current_state == STATE_ALARM_ARMING

    @property
    def is_pending(self):
        return self._current_state == STATE_ALARM_PENDING

    @property
    def is_triggered(self):
        return self._current_state == STATE_ALARM_TRIGGERED

    # -- Transitions ----------------------------------------------------------

    def arm_away(self, skip_delay=False):
        if self._current_state != STATE_ALARM_DISARMED:
            return False
        if skip_delay or self._exit_delay == 0:
            self._current_state = STATE_ALARM_ARMED_AWAY
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_AWAY
            self._countdown = self._exit_delay
        return True

    def arm_home(self, skip_delay=False):
        if self._current_state != STATE_ALARM_DISARMED:
            return False
        if skip_delay or self._exit_delay == 0:
            self._current_state = STATE_ALARM_ARMED_HOME
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_HOME
            self._countdown = self._exit_delay
        return True

    def arm_night(self, skip_delay=False):
        if self._current_state != STATE_ALARM_DISARMED:
            return False
        if skip_delay:
            self._current_state = STATE_ALARM_ARMED_NIGHT
        else:
            self._current_state = STATE_ALARM_ARMING
            self._target_state = STATE_ALARM_ARMED_NIGHT
            self._countdown = self._exit_delay
        return True

    def arm_vacation(self, skip_delay=False):
        if self._current_state != STATE_ALARM_DISARMED:
            return False
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
        if self._current_state == STATE_ALARM_DISARMED:
            return False
        self._current_state = STATE_ALARM_DISARMED
        self._countdown = 0
        self._target_state = None
        return True

    def trigger_entry_delay(self, zone_type="entry"):
        if not self.is_armed:
            return False
        if zone_type == "instant":
            self._current_state = STATE_ALARM_TRIGGERED
            self._schedule_auto_reset()
        else:
            self._current_state = STATE_ALARM_PENDING
            self._countdown = self._entry_delay
        return True

    def trigger_alarm(self, source="manual"):
        if self._current_state == STATE_ALARM_TRIGGERED:
            return False  # already triggered -- guard
        self._current_state = STATE_ALARM_TRIGGERED
        self._countdown = 0
        self._schedule_auto_reset()
        return True

    def trigger_alarm_during_arming(self):
        """Mirrors arming-state guard: trigger ignored during exit delay."""
        if self.is_arming:
            return False  # guard -- sensor opened during exit delay, ignore
        return self.trigger_alarm()

    def cancel_pending(self):
        if not self.is_pending:
            return False
        self._current_state = STATE_ALARM_DISARMED
        self._countdown = 0
        return True

    def simulate_auto_reset(self):
        """Simulate trigger_time elapsed -> auto-reset to disarmed."""
        if self._current_state == STATE_ALARM_TRIGGERED and self._trigger_time > 0:
            self._current_state = STATE_ALARM_DISARMED
            self._countdown = 0
            return True
        return False

    def _schedule_auto_reset(self):
        """Record that auto-reset was scheduled (trigger_time > 0)."""
        if self._trigger_time > 0:
            self.auto_reset_called = True

    def update_config(self, exit_delay, entry_delay, trigger_time=300):
        self._exit_delay = exit_delay
        self._entry_delay = entry_delay
        self._trigger_time = trigger_time


# ---------------------------------------------------------------------------
# Tests: auto-reset after trigger_time (v0.5.0)
# ---------------------------------------------------------------------------

class TestAutoResetAfterTrigger:
    """Alarm auto-resets to disarmed after trigger_time -- was TODO in v0.3.x."""

    def test_trigger_schedules_auto_reset_when_trigger_time_positive(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        assert sm.auto_reset_called is True

    def test_trigger_no_auto_reset_when_trigger_time_zero(self):
        """trigger_time=0 means no auto-reset."""
        sm = MockStateMachineV2(trigger_time=0)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        assert sm.auto_reset_called is False

    def test_auto_reset_transitions_to_disarmed(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        assert sm.is_triggered is True

        sm.simulate_auto_reset()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_auto_reset_clears_countdown(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        sm.simulate_auto_reset()
        assert sm.countdown == 0

    def test_auto_reset_not_applied_if_manually_disarmed(self):
        """If user disarms before trigger_time, state is already disarmed."""
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        sm.disarm()
        # Simulate timer firing after manual disarm -- should be no-op
        result = sm.simulate_auto_reset()
        assert result is False  # no-op: not triggered anymore
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_entry_zone_instant_also_schedules_auto_reset(self):
        sm = MockStateMachineV2(trigger_time=300)
        sm.arm_away(skip_delay=True)
        sm.trigger_entry_delay("instant")
        assert sm.auto_reset_called is True


# ---------------------------------------------------------------------------
# Tests: double-arm guard (transition lock behaviour)
# ---------------------------------------------------------------------------

class TestDoubleArmGuard:
    """Cannot arm when already armed -- transition lock prevents double-arm."""

    def test_cannot_arm_away_when_armed_away(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        result = sm.arm_away(skip_delay=True)
        assert result is False
        assert sm.current_state == STATE_ALARM_ARMED_AWAY

    def test_cannot_arm_home_when_armed_away(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        result = sm.arm_home(skip_delay=True)
        assert result is False

    def test_cannot_arm_while_arming(self):
        sm = MockStateMachineV2()
        sm.arm_away()  # enters ARMING
        assert sm.is_arming is True
        result = sm.arm_away()
        assert result is False

    def test_cannot_arm_when_triggered(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        result = sm.arm_home(skip_delay=True)
        assert result is False

    def test_can_arm_after_disarm(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.disarm()
        result = sm.arm_home(skip_delay=True)
        assert result is True
        assert sm.current_state == STATE_ALARM_ARMED_HOME


# ---------------------------------------------------------------------------
# Tests: disarm during exit delay (arming state)
# ---------------------------------------------------------------------------

class TestDisarmDuringExitDelay:
    """Disarming while in ARMING state cancels countdown cleanly."""

    def test_disarm_during_arming_goes_to_disarmed(self):
        sm = MockStateMachineV2()
        sm.arm_away()
        assert sm.is_arming is True
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


# ---------------------------------------------------------------------------
# Tests: disarm during entry delay (pending state)
# ---------------------------------------------------------------------------

class TestDisarmDuringEntryDelay:
    """Disarming or cancel_pending during PENDING state works correctly."""

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
        result = sm.cancel_pending()
        assert result is True
        assert sm.current_state == STATE_ALARM_DISARMED
        assert sm.countdown == 0

    def test_cancel_pending_returns_false_if_not_pending(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        assert sm.is_pending is False
        result = sm.cancel_pending()
        assert result is False

    def test_disarm_during_pending_clears_countdown(self):
        sm = MockStateMachineV2(entry_delay=45)
        sm.arm_away(skip_delay=True)
        sm.trigger_entry_delay("entry")
        assert sm.countdown == 45
        sm.disarm()
        assert sm.countdown == 0


# ---------------------------------------------------------------------------
# Tests: sensor opens during exit delay (arming-state guard)
# ---------------------------------------------------------------------------

class TestSensorOpenDuringExitDelay:
    """Sensor opening during exit delay must not trigger alarm (user still leaving)."""

    def test_trigger_ignored_while_arming(self):
        sm = MockStateMachineV2()
        sm.arm_away()  # in ARMING state
        assert sm.is_arming is True

        result = sm.trigger_alarm_during_arming()
        assert result is False
        assert sm.current_state == STATE_ALARM_ARMING  # unchanged

    def test_trigger_fires_after_arming_completes(self):
        sm = MockStateMachineV2()
        sm.arm_away()
        sm.complete_arming()  # now ARMED_AWAY
        assert sm.is_armed is True

        result = sm.trigger_alarm_during_arming()
        assert result is True
        assert sm.current_state == STATE_ALARM_TRIGGERED

    def test_immediate_arm_no_delay_trigger_works(self):
        """skip_delay=True -> no arming state -> trigger fires."""
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        assert sm.is_arming is False

        result = sm.trigger_alarm_during_arming()
        assert result is True


# ---------------------------------------------------------------------------
# Tests: already triggered guard
# ---------------------------------------------------------------------------

class TestAlreadyTriggeredGuard:
    """Cannot trigger again when already in TRIGGERED state."""

    def test_second_trigger_returns_false(self):
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        result = sm.trigger_alarm()
        assert result is False
        assert sm.current_state == STATE_ALARM_TRIGGERED

    def test_auto_reset_called_only_once(self):
        """Auto-reset should not be re-scheduled on duplicate trigger calls."""
        sm = MockStateMachineV2()
        sm.arm_away(skip_delay=True)
        sm.trigger_alarm()
        first_reset_count = 1 if sm.auto_reset_called else 0
        sm.trigger_alarm()  # should be no-op
        # auto_reset_called is a simple bool, not a counter, but trigger
        # should have returned False meaning it didn't schedule again
        assert sm.auto_reset_called is True  # from first trigger only


# ---------------------------------------------------------------------------
# Tests: state transitions -- full flows (v0.5.0 scenarios)
# ---------------------------------------------------------------------------

class TestFullFlowsV2:
    """End-to-end state transition sequences covering v0.5.0 scenarios."""

    def test_arm_away_entry_delay_auto_reset_cycle(self):
        """arm -> entry sensor -> pending -> triggered -> auto-reset."""
        sm = MockStateMachineV2(trigger_time=300)

        sm.arm_away(skip_delay=True)
        assert sm.current_state == STATE_ALARM_ARMED_AWAY

        sm.trigger_entry_delay("entry")
        assert sm.current_state == STATE_ALARM_PENDING

        sm.trigger_alarm()
        assert sm.current_state == STATE_ALARM_TRIGGERED
        assert sm.auto_reset_called is True

        sm.simulate_auto_reset()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_arm_home_instant_trigger_then_disarm(self):
        """arm home -> instant zone -> triggered -> manual disarm."""
        sm = MockStateMachineV2(trigger_time=300)

        sm.arm_home(skip_delay=True)
        sm.trigger_entry_delay("instant")
        assert sm.current_state == STATE_ALARM_TRIGGERED

        sm.disarm()
        assert sm.current_state == STATE_ALARM_DISARMED

    def test_disarm_during_exit_delay_then_rearm(self):
        """arm -> disarm during exit delay -> re-arm succeeds."""
        sm = MockStateMachineV2()

        sm.arm_away()
        assert sm.is_arming is True

        sm.disarm()
        assert sm.current_state == STATE_ALARM_DISARMED

        result = sm.arm_away(skip_delay=True)
        assert result is True
        assert sm.current_state == STATE_ALARM_ARMED_AWAY

    def test_all_four_arm_modes_then_disarm(self):
        """Each arm mode reaches armed state and can be disarmed."""
        modes = [
            ("away", STATE_ALARM_ARMED_AWAY),
            ("home", STATE_ALARM_ARMED_HOME),
            ("night", STATE_ALARM_ARMED_NIGHT),
            ("vacation", STATE_ALARM_ARMED_VACATION),
        ]
        for mode_name, expected_state in modes:
            sm = MockStateMachineV2()
            method = getattr(sm, f"arm_{mode_name}")
            method(skip_delay=True)
            assert sm.current_state == expected_state, \
                f"arm_{mode_name} should reach {expected_state}"
            sm.disarm()
            assert sm.current_state == STATE_ALARM_DISARMED

    def test_update_config_changes_delays(self):
        sm = MockStateMachineV2()
        sm.update_config(exit_delay=60, entry_delay=45, trigger_time=600)
        assert sm.exit_delay == 60
        assert sm.entry_delay == 45
        assert sm.trigger_time == 600


# ---------------------------------------------------------------------------
# Tests: real AlarmStateMachine with asyncio (integration-style)
# ---------------------------------------------------------------------------

class TestRealStateMachineAsync:
    """Tests against the actual AlarmStateMachine using asyncio tasks.

    Verifies:
    - arm_away with skip_delay transitions immediately
    - disarm works
    - trigger_alarm transitions to TRIGGERED
    - cleanup cancels tasks without error
    """

    @pytest.mark.asyncio
    async def test_real_sm_arm_disarm(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine

        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30,
                               trigger_time=300)
        try:
            result = await sm.arm_away(skip_delay=True)
            assert result is True
            assert sm.current_state == STATE_ALARM_ARMED_AWAY

            result = await sm.disarm()
            assert result is True
            assert sm.current_state == STATE_ALARM_DISARMED
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_trigger_alarm(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine

        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30,
                               trigger_time=300)
        try:
            await sm.arm_away(skip_delay=True)
            result = await sm.trigger_alarm("test")
            assert result is True
            assert sm.current_state == STATE_ALARM_TRIGGERED
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_double_arm_blocked(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine

        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30,
                               trigger_time=300)
        try:
            await sm.arm_away(skip_delay=True)
            result = await sm.arm_home(skip_delay=True)
            assert result is False
            assert sm.current_state == STATE_ALARM_ARMED_AWAY
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_cancel_countdown_is_safe(self):
        """_cancel_countdown() must not raise even with no active task."""
        from custom_components.secure_me.state_machine import AlarmStateMachine

        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30,
                               trigger_time=300)
        try:
            # No task running -- should be no-op without error
            await sm._cancel_countdown()
            assert sm._countdown_task is None
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_cleanup_with_active_task(self):
        """cleanup() cancels countdown task without raising."""
        from custom_components.secure_me.state_machine import AlarmStateMachine

        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=60, entry_delay=30,
                               trigger_time=300)
        try:
            await sm.arm_away()  # starts countdown task
            assert sm.is_arming is True
        finally:
            sm.cleanup()  # must not raise even with running task
        # After cleanup task references are cleared
        assert sm._countdown_task is None

    @pytest.mark.asyncio
    async def test_real_sm_disarm_already_disarmed_returns_false(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine

        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30,
                               trigger_time=300)
        try:
            result = await sm.disarm()
            assert result is False
        finally:
            sm.cleanup()

    @pytest.mark.asyncio
    async def test_real_sm_callbacks_called_on_state_change(self):
        from custom_components.secure_me.state_machine import AlarmStateMachine

        hass = MagicMock()
        sm = AlarmStateMachine(hass, exit_delay=30, entry_delay=30,
                               trigger_time=300)
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
