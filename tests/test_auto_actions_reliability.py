"""Tests for AutoActionsManager reliability features added 2026-08-29:
stale-tracker timeout, the periodic fallback re-check, honest failure
reporting, and the one-shot auto-arm retry.

These three closely-related fixes had NO test coverage at all before this
file (test_auto_actions.py, added for the v1.5.4 presence-consolidation
work, predates all of them):

  1. AA_STALE_TRACKER_TIMEOUT grace period in _all_persons_away() -- a
     tracker permanently stuck on "unknown"/"unavailable" now stops
     blocking the "home empty" determination after a configurable timeout,
     instead of blocking forever.
  2. _periodic_stale_check() -- the 5-minute fallback timer that actually
     re-evaluates presence once a stale timeout elapses, since
     _all_persons_away() is otherwise only re-checked from a tracker's own
     state_changed event.
  3. Honest failure reporting + one-shot retry -- a failed auto-arm (e.g.
     blocked by an open sensor) used to be silently recorded as "completed"
     in the summary notification, visible only in the HA log. It's now
     tracked as action + "_failed" with a reason, reported as FAILED in the
     notification, and given exactly one automatic retry after
     AutoActionsManager._ALARM_RETRY_DELAY seconds.

Per the project's testing rule (see test_coordinator_trigger.py /
test_auto_actions.py), these tests exercise the real AutoActionsManager
class. The store/coordinator are lightweight data-layer stand-ins, not
mirrors of AutoActionsManager's own logic.
"""
# VERSION = "1.0.0"

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from custom_components.secure_me.auto_actions import AutoActionsManager
from custom_components.secure_me.const import (
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMED_AWAY,
)

from .test_auto_actions import FakeAutoActionsStore, _aa_config


class FakeZoneManager:
    """Minimal zone_manager stand-in -- only what _do_alarm() reads."""

    def __init__(self, open_sensors=None):
        self._open_sensors = open_sensors or []

    def get_all_open_sensors(self):
        return self._open_sensors


class FakeReliabilityCoordinator:
    """Coordinator stand-in with a controllable arm outcome, for exercising
    the failure/retry path that FakeAutoActionsCoordinator (in
    test_auto_actions.py) doesn't need."""

    def __init__(self, arm_results=None, open_sensors=None):
        self.modules = {}
        self.alarm_state = STATE_ALARM_DISARMED
        self.arm_away_calls = 0
        self.zone_manager = FakeZoneManager(open_sensors)
        # Queue of True/False outcomes consumed one at a time by
        # async_arm_away(); the last value is reused once exhausted.
        self._arm_results = list(arm_results) if arm_results is not None else [True]

    async def async_arm_away(self, skip_delay: bool = False, **kwargs) -> bool:
        self.arm_away_calls += 1
        result = self._arm_results.pop(0) if len(self._arm_results) > 1 else self._arm_results[0]
        if result:
            self.alarm_state = STATE_ALARM_ARMED_AWAY
        return result


# -----------------------------------------------------------------------------
# 1. Stale-tracker timeout grace period
# -----------------------------------------------------------------------------

class TestStaleTrackerTimeout:
    """A tracker stuck on unknown/unavailable stops blocking 'all away'
    once AA_STALE_TRACKER_TIMEOUT has elapsed -- but not before."""

    @pytest.mark.asyncio
    async def test_stale_tracker_blocks_before_timeout(self, hass):
        hass.states.async_set("person.flemming", "unknown")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(stale_tracker_timeout=1800),
        )
        manager = AutoActionsManager(hass, FakeReliabilityCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._all_persons_away() is False

    @pytest.mark.asyncio
    async def test_stale_tracker_stops_blocking_after_timeout(self, hass):
        hass.states.async_set("person.flemming", "unknown")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(stale_tracker_timeout=1),
        )
        manager = AutoActionsManager(hass, FakeReliabilityCoordinator(), store)
        manager.async_refresh_trackers()
        # Simulate the tracker having been stale for longer than the 1s timeout.
        manager._tracker_stale_since["person.flemming"] = time.monotonic() - 5

        assert manager._all_persons_away() is True

    @pytest.mark.asyncio
    async def test_second_tracker_showing_home_still_blocks_despite_stale_timeout(self, hass):
        """A stale timeout elapsing on ONE tracker must never override a
        different tracker that is clearly still home."""
        hass.states.async_set("person.flemming", "unknown")
        hass.states.async_set("person.partner", "home")
        store = FakeAutoActionsStore(
            users={
                "u1": {"enabled": True, "person_entity": "person.flemming"},
                "u2": {"enabled": True, "person_entity": "person.partner"},
            },
            auto_actions=_aa_config(stale_tracker_timeout=1),
        )
        manager = AutoActionsManager(hass, FakeReliabilityCoordinator(), store)
        manager.async_refresh_trackers()
        manager._tracker_stale_since["person.flemming"] = time.monotonic() - 5

        assert manager._all_persons_away() is False

    @pytest.mark.asyncio
    async def test_stale_since_starts_clock_on_first_check_instead_of_assuming_stale(self, hass):
        """A tracker already unknown when the manager starts (no prior
        state_changed event recorded it) must NOT be treated as already
        stale past the timeout -- the clock starts now."""
        hass.states.async_set("person.flemming", "unknown")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(stale_tracker_timeout=1800),
        )
        manager = AutoActionsManager(hass, FakeReliabilityCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._all_persons_away() is False
        assert "person.flemming" in manager._tracker_stale_since

    @pytest.mark.asyncio
    async def test_tracker_recovering_to_not_home_clears_stale_tracking(self, hass):
        hass.states.async_set("person.flemming", "unknown")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
        )
        coordinator = FakeReliabilityCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)
        manager.async_start()
        await asyncio.sleep(0.05)
        assert "person.flemming" in manager._tracker_stale_since

        hass.states.async_set("person.flemming", "not_home")
        await asyncio.sleep(0.05)

        assert "person.flemming" not in manager._tracker_stale_since
        await manager.async_stop()


# -----------------------------------------------------------------------------
# 2. Periodic fallback re-check
# -----------------------------------------------------------------------------

class TestPeriodicStaleCheck:
    """_periodic_stale_check() re-evaluates presence on its own 5-minute
    cadence, independent of any state_changed event."""

    @pytest.mark.asyncio
    async def test_periodic_check_triggers_home_empty_when_all_away(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(),
        )
        coordinator = FakeReliabilityCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)
        manager.async_refresh_trackers()
        manager._send_summary_notification = AsyncMock()
        # Force _home_empty False so the check isn't a no-op, without going
        # through async_start()'s own initial-presence check.
        manager._home_empty = False

        manager._periodic_stale_check()
        await asyncio.sleep(0.05)

        assert manager._home_empty is True
        assert coordinator.arm_away_calls == 1

    @pytest.mark.asyncio
    async def test_periodic_check_does_nothing_when_already_empty(self, hass):
        """Must not re-fire _on_home_empty() (and reset done_actions/results)
        every 5 minutes while already in an empty-house cycle."""
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
        )
        coordinator = FakeReliabilityCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)
        manager.async_refresh_trackers()
        manager._home_empty = True  # already in a cycle

        manager._periodic_stale_check()
        await asyncio.sleep(0.05)

        assert coordinator.arm_away_calls == 0

    @pytest.mark.asyncio
    async def test_periodic_check_does_nothing_when_someone_home(self, hass):
        hass.states.async_set("person.flemming", "home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
        )
        coordinator = FakeReliabilityCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)
        manager.async_refresh_trackers()

        manager._periodic_stale_check()
        await asyncio.sleep(0.05)

        assert manager._home_empty is False
        assert coordinator.arm_away_calls == 0


# -----------------------------------------------------------------------------
# 3. Honest failure reporting for a rejected auto-arm
# -----------------------------------------------------------------------------

class TestFailedAutoArmReporting:
    """A rejected auto-arm (e.g. blocked by an open sensor) must be tracked
    as action + '_failed' with a reason -- never silently as 'completed'."""

    @pytest.mark.asyncio
    async def test_blocked_arm_is_tracked_as_failed_not_completed(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(auto_alarm_delay=0),
        )
        coordinator = FakeReliabilityCoordinator(
            arm_results=[False], open_sensors=["binary_sensor.front_door"],
        )
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()
        # Prevent the real retry from firing mid-test and double-counting calls.
        manager._retry_alarm_after_delay = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.1)

        assert "alarm_failed" in manager._done_actions
        assert "alarm" not in manager._done_actions
        assert "binary_sensor.front_door" in manager._action_results["alarm"]

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_summary_notification_reports_failed_with_reason(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(auto_alarm_delay=0),
        )
        coordinator = FakeReliabilityCoordinator(
            arm_results=[False], open_sensors=["binary_sensor.front_door"],
        )
        manager = AutoActionsManager(hass, coordinator, store)
        manager._retry_alarm_after_delay = AsyncMock()

        sent_messages = []

        async def _capture_notification():
            sent_messages.append(True)

        manager._send_summary_notification = _capture_notification

        manager.async_start()
        await asyncio.sleep(0.1)

        assert sent_messages  # notification was triggered once all settled

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_successful_arm_is_tracked_as_completed_not_failed(self, hass):
        """Control case: a normal successful auto-arm must still be tracked
        as a plain completed action, not regressed by the failure-path change."""
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(auto_alarm_delay=0),
        )
        coordinator = FakeReliabilityCoordinator(arm_results=[True])
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.1)

        assert "alarm" in manager._done_actions
        assert "alarm_failed" not in manager._done_actions

        await manager.async_stop()


# -----------------------------------------------------------------------------
# 4. One-shot auto-arm retry
# -----------------------------------------------------------------------------

class TestAlarmRetry:
    """A failed auto-arm gets exactly one automatic retry
    (_ALARM_RETRY_DELAY seconds later); a second failure is not retried
    again."""

    @pytest.mark.asyncio
    async def test_retry_succeeding_clears_failed_and_marks_done(self, hass):
        store = FakeAutoActionsStore(users={"u1": {"enabled": True, "person_entity": "person.flemming"}})
        coordinator = FakeReliabilityCoordinator(arm_results=[True])
        manager = AutoActionsManager(hass, coordinator, store)
        manager._home_empty = True
        manager._done_actions.add("alarm_failed")
        manager._send_summary_notification = AsyncMock()

        await manager._retry_alarm_after_delay(0)

        assert "alarm" in manager._done_actions
        assert "alarm_failed" not in manager._done_actions
        assert coordinator.arm_away_calls == 1

    @pytest.mark.asyncio
    async def test_retry_failing_again_does_not_reschedule_itself(self, hass):
        store = FakeAutoActionsStore(users={"u1": {"enabled": True, "person_entity": "person.flemming"}})
        coordinator = FakeReliabilityCoordinator(
            arm_results=[False], open_sensors=["binary_sensor.front_door"],
        )
        manager = AutoActionsManager(hass, coordinator, store)
        manager._home_empty = True
        manager._done_actions.add("alarm_failed")
        manager._send_summary_notification = AsyncMock()

        await manager._retry_alarm_after_delay(0)

        # Still failed, and critically: no second retry task queued.
        assert "alarm_failed" in manager._done_actions
        assert "alarm" not in manager._done_actions
        assert "alarm_retry" not in manager._action_tasks

    @pytest.mark.asyncio
    async def test_retry_aborted_if_home_no_longer_empty(self, hass):
        store = FakeAutoActionsStore(users={"u1": {"enabled": True, "person_entity": "person.flemming"}})
        coordinator = FakeReliabilityCoordinator(arm_results=[True])
        manager = AutoActionsManager(hass, coordinator, store)
        manager._home_empty = False  # someone came home in the meantime

        await manager._retry_alarm_after_delay(0)

        assert coordinator.arm_away_calls == 0

    @pytest.mark.asyncio
    async def test_retry_aborted_if_already_armed_by_something_else(self, hass):
        store = FakeAutoActionsStore(users={"u1": {"enabled": True, "person_entity": "person.flemming"}})
        coordinator = FakeReliabilityCoordinator(arm_results=[True])
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY  # armed manually in the meantime
        manager = AutoActionsManager(hass, coordinator, store)
        manager._home_empty = True

        await manager._retry_alarm_after_delay(0)

        assert coordinator.arm_away_calls == 0

    @pytest.mark.asyncio
    async def test_failed_arm_schedules_exactly_one_retry_task(self, hass):
        """End-to-end: a real failure from _run_action_after_delay must
        result in exactly one 'alarm_retry' task being queued."""
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(auto_alarm_delay=0),
        )
        coordinator = FakeReliabilityCoordinator(
            arm_results=[False], open_sensors=["binary_sensor.front_door"],
        )
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.1)

        assert "alarm_retry" in manager._action_tasks
        assert not manager._action_tasks["alarm_retry"].done()

        await manager.async_stop()
