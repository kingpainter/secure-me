"""Tests for Fake Presence v2 selective blocking in AutoActionsManager.

Fake Presence v2's whole point is that it does NOT have to block
everything at once -- each of the three auto-actions (lock, alarm, camera)
has its own independent block flag (FP_BLOCK_LOCKS, FP_BLOCK_ALARM,
FP_BLOCK_CAMERAS), so e.g. cameras can keep recording while the alarm is
deliberately not auto-armed. Before this file, that selectivity had no
direct test coverage: test_auto_actions.py's
TestFakePresenceExecutionTimeRecheck only exercises the alarm flag, and
only the execution-time re-check race, not the initial scheduling-time
block or the other two action types.

This file covers, at both scheduling time (_schedule_action, called from
_on_home_empty) and independently for each action type:
  - Each of the three block flags blocking only its own action.
  - Unblocked action types still running normally while a sibling is
    blocked (selectivity, not an all-or-nothing kill switch).
  - Fake Presence configured but not active at all (fp["active"] = False)
    blocking nothing, regardless of which block_* flags are set.

Per the project's testing rule, these use the real AutoActionsManager
against the real `hass` fixture -- no mirror re-implementations.
"""
# VERSION = "1.0.0"

import asyncio
from unittest.mock import AsyncMock

import pytest

from custom_components.secure_me.auto_actions import AutoActionsManager
from custom_components.secure_me.const import STATE_ALARM_DISARMED

from .test_auto_actions import FakeAutoActionsStore, FakeAutoActionsCoordinator, _aa_config


def _fp(active: bool, block_alarm=False, block_locks=False, block_cameras=False) -> dict:
    return {
        "active": active,
        "block_alarm": block_alarm,
        "block_locks": block_locks,
        "block_cameras": block_cameras,
    }


def _make_manager(hass, fp: dict, **aa_overrides) -> tuple[AutoActionsManager, FakeAutoActionsCoordinator]:
    hass.states.async_set("person.flemming", "not_home")
    store = FakeAutoActionsStore(
        users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
        auto_actions=_aa_config(
            auto_lock_enabled=True, auto_lock_delay=0,
            auto_camera_enabled=True, auto_camera_delay=0,
            auto_alarm_delay=0,
            **aa_overrides,
        ),
        fake_presence=fp,
    )
    coordinator = FakeAutoActionsCoordinator()
    coordinator.alarm_state = STATE_ALARM_DISARMED
    manager = AutoActionsManager(hass, coordinator, store)
    manager._send_summary_notification = AsyncMock()
    return manager, coordinator


class TestSelectiveBlockingAtSchedulingTime:
    """_on_home_empty() -> _schedule_action(): each block_* flag must only
    affect its own action type, both alone and in combination."""

    @pytest.mark.asyncio
    async def test_block_alarm_only_blocks_alarm(self, hass):
        manager, coordinator = _make_manager(hass, _fp(True, block_alarm=True))
        manager.async_start()
        await asyncio.sleep(0.1)

        assert "alarm_skipped" in manager._done_actions
        assert coordinator.arm_away_calls == 0
        assert "lock" in manager._done_actions
        assert "camera" in manager._done_actions

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_block_locks_only_blocks_lock(self, hass):
        manager, coordinator = _make_manager(hass, _fp(True, block_locks=True))
        manager.async_start()
        await asyncio.sleep(0.1)

        assert "lock_skipped" in manager._done_actions
        assert "alarm" in manager._done_actions
        assert coordinator.arm_away_calls == 1
        assert "camera" in manager._done_actions

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_block_cameras_only_blocks_camera(self, hass):
        manager, coordinator = _make_manager(hass, _fp(True, block_cameras=True))
        manager.async_start()
        await asyncio.sleep(0.1)

        assert "camera_skipped" in manager._done_actions
        assert "alarm" in manager._done_actions
        assert coordinator.arm_away_calls == 1
        assert "lock" in manager._done_actions

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_block_alarm_and_cameras_but_not_locks(self, hass):
        """Two of three blocked, one still runs -- confirms selectivity is
        not accidentally all-or-nothing."""
        manager, coordinator = _make_manager(
            hass, _fp(True, block_alarm=True, block_cameras=True)
        )
        manager.async_start()
        await asyncio.sleep(0.1)

        assert "alarm_skipped" in manager._done_actions
        assert "camera_skipped" in manager._done_actions
        assert "lock" in manager._done_actions
        assert coordinator.arm_away_calls == 0

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_all_three_blocked(self, hass):
        manager, coordinator = _make_manager(
            hass, _fp(True, block_alarm=True, block_locks=True, block_cameras=True)
        )
        manager.async_start()
        await asyncio.sleep(0.1)

        assert "alarm_skipped" in manager._done_actions
        assert "lock_skipped" in manager._done_actions
        assert "camera_skipped" in manager._done_actions
        assert coordinator.arm_away_calls == 0

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_inactive_fake_presence_blocks_nothing_even_with_flags_set(self, hass):
        """The block_* flags are only honoured while Fake Presence itself
        is active -- a stale/pre-configured flag set must not leak through
        while Fake Presence is off."""
        manager, coordinator = _make_manager(
            hass, _fp(False, block_alarm=True, block_locks=True, block_cameras=True)
        )
        manager.async_start()
        await asyncio.sleep(0.1)

        assert "alarm" in manager._done_actions
        assert "lock" in manager._done_actions
        assert "camera" in manager._done_actions
        assert coordinator.arm_away_calls == 1

        await manager.async_stop()


class TestSelectiveBlockingSummaryNotification:
    """The summary notification's per-action wording must reflect selective
    blocking accurately -- skipped actions labelled distinctly from
    completed ones."""

    @pytest.mark.asyncio
    async def test_summary_only_sent_once_all_three_settle(self, hass):
        """With one action blocked (instant) and two running (instant delay),
        the summary must still wait for all three before firing -- not skip
        ahead just because the blocked one resolves first."""
        hass.states.async_set("person.flemming", "not_home")
        fp = _fp(True, block_alarm=True)
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(
                auto_lock_enabled=True, auto_lock_delay=0,
                auto_camera_enabled=True, auto_camera_delay=0,
                auto_alarm_delay=0,
            ),
            fake_presence=fp,
        )
        coordinator = FakeAutoActionsCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)

        notified = []

        async def _capture():
            notified.append(dict(manager._done_actions))

        manager._send_summary_notification = _capture

        manager.async_start()
        await hass.async_block_till_done()
        await asyncio.sleep(0.1)
        await hass.async_block_till_done()

        assert len(notified) == 1
        final = notified[0]
        assert "alarm_skipped" in final
        assert "lock" in final
        assert "camera" in final

        await manager.async_stop()
