"""Tests for AutoActionsManager -- v1.5.4 presence-consolidation changes.

Covers three behavioural changes made when AutoActionsManager became the
sole presence-based automation system (replacing the removed
PresenceMonitor class in coordinator.py):

  1. Scoped tracking -- AutoActionsManager previously reacted to every
     person.* entity in the whole HA instance. It now only reacts to the
     person_entity/tracker_entity configured on enabled Secure Me user
     profiles (async_refresh_trackers()). A person.* entity not tied to a
     Secure Me user (guest, test account, another integration's person)
     must no longer be able to block or trigger Auto Actions.

  2. Initial-presence check at startup -- hass.bus.async_listen("state_changed")
     only fires on FUTURE changes. If the house is already empty (all
     tracked users not_home) when HA restarts, no state_changed event would
     ever occur to kick off _on_home_empty() without an explicit check.
     async_start() now runs _check_initial_presence() to close that gap.

  3. Fake Presence re-checked at execution time -- previously the Fake
     Presence block flags were only checked once, at the moment the house
     was first found empty (_on_home_empty() -> _schedule_action()). If
     Fake Presence was toggled on AFTER an action was scheduled but BEFORE
     its delay elapsed, the action would still fire unblocked.
     _run_action_after_delay() now re-checks the block flags immediately
     before executing.

These tests exercise the real AutoActionsManager class (per the project's
testing rule: no hand-written mirror implementations of the class under
test). The store and coordinator it depends on are lightweight fakes --
not mirrors of AutoActionsManager's own logic, just data-layer stand-ins,
the same role MockConfigEntry/MockHass play in conftest.py for other
tests.
"""
# VERSION = "1.5.4"

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from custom_components.secure_me.auto_actions import AutoActionsManager
from custom_components.secure_me.const import (
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_ARMED_HOME_ALONE,
    EVENT_ALARM_DISARMED,
)


class FakeAutoActionsStore:
    """Minimal store stand-in exposing only what AutoActionsManager reads."""

    def __init__(self, users=None, auto_actions=None, fake_presence=None):
        self._users = users or {}
        self._auto_actions = auto_actions or {}
        self._fake_presence = fake_presence or {"active": False}

    def get_users(self):
        return self._users

    def get_auto_actions(self):
        return self._auto_actions

    def get_fake_presence_v2(self):
        return self._fake_presence


class FakeAutoActionsCoordinator:
    """Minimal coordinator stand-in -- records arm_away calls, no real modules."""

    def __init__(self):
        self.modules = {}
        self.alarm_state = STATE_ALARM_DISARMED
        self.arm_away_calls = 0

    async def async_arm_away(self, skip_delay: bool = False, **kwargs) -> bool:
        self.arm_away_calls += 1
        self.alarm_state = STATE_ALARM_ARMED_AWAY
        return True


# Auto Actions config helper -- alarm-only, zero/short delays, unless overridden.
def _aa_config(**overrides) -> dict:
    cfg = {
        "auto_lock_enabled": False,
        "auto_alarm_enabled": True,
        "auto_alarm_delay": 0,
        "auto_camera_enabled": False,
        "auto_camera_delay": 0,
        "arrival_confirmation_delay": 60,
        "notify_all_users": False,
        "recheck_on_disarm": False,
        "recheck_delay": 0,
        "recheck_min_away_duration": 0,
        "recheck_include_lock": True,
        "recheck_include_alarm": True,
        "recheck_include_camera": True,
    }
    cfg.update(overrides)
    return cfg


# -----------------------------------------------------------------------------
# 1. Scoped tracking (Secure Me users only, not every person.* entity)
# -----------------------------------------------------------------------------

class TestScopedTracking:
    """AutoActionsManager must only watch person_entity from enabled Secure Me
    users -- not every person.* entity in the HA instance (the pre-v1.5.4
    behaviour, which the removed PresenceMonitor never had either)."""

    @pytest.mark.asyncio
    async def test_only_configured_users_are_tracked(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        hass.states.async_set("person.guest", "not_home")  # NOT a Secure Me user

        store = FakeAutoActionsStore(users={
            "u1": {"enabled": True, "person_entity": "person.flemming"},
        })
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._tracker_entities == {"person.flemming"}
        assert "person.guest" not in manager._tracker_entities

    @pytest.mark.asyncio
    async def test_disabled_user_not_tracked(self, hass):
        store = FakeAutoActionsStore(users={
            "u1": {"enabled": True, "person_entity": "person.flemming"},
            "u2": {"enabled": False, "person_entity": "person.disabled_user"},
        })
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._tracker_entities == {"person.flemming"}

    @pytest.mark.asyncio
    async def test_tracker_entity_legacy_field_fallback(self, hass):
        """person_entity is the canonical field name; tracker_entity is the
        legacy fallback for older profiles -- both must work."""
        store = FakeAutoActionsStore(users={
            "u1": {"enabled": True, "tracker_entity": "person.legacy_field_user"},
        })
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._tracker_entities == {"person.legacy_field_user"}

    @pytest.mark.asyncio
    async def test_untracked_person_state_change_is_ignored(self, hass):
        """An unrelated person.* entity leaving home must not start Auto
        Actions -- regression guard for the pre-v1.5.4 startswith('person.')
        filter that reacted to everything."""
        hass.states.async_set("person.flemming", "home")
        hass.states.async_set("person.guest", "home")

        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(),
        )
        coordinator = FakeAutoActionsCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)
        manager.async_start()
        await asyncio.sleep(0.05)  # let the initial-presence check task run

        hass.states.async_set("person.guest", "not_home")
        await asyncio.sleep(0.05)

        assert manager._home_empty is False
        assert coordinator.arm_away_calls == 0

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_refresh_trackers_picks_up_new_user_without_restart(self, hass):
        """Mirrors what ws_save_user calls after a Users-tab edit."""
        store = FakeAutoActionsStore(users={
            "u1": {"enabled": True, "person_entity": "person.flemming"},
        })
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()
        assert manager._tracker_entities == {"person.flemming"}

        store._users["u2"] = {"enabled": True, "person_entity": "person.kids"}
        manager.async_refresh_trackers()

        assert manager._tracker_entities == {"person.flemming", "person.kids"}


# -----------------------------------------------------------------------------
# 6. Granular recheck controls (delay, min-away-duration, per-action include)
# -----------------------------------------------------------------------------

class TestRecheckGranularControls:
    """Fine-tuning knobs for AA_RECHECK_ON_DISARM: recheck_delay,
    recheck_min_away_duration, and recheck_include_lock/alarm/camera."""

    @pytest.mark.asyncio
    async def test_recheck_delay_postpones_execution(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(recheck_on_disarm=True, recheck_delay=1),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.05)

        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.1)
        assert coordinator.arm_away_calls == 0  # still waiting out recheck_delay

        await asyncio.sleep(1.1)
        assert coordinator.arm_away_calls == 1

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_min_away_duration_blocks_recently_emptied_house(self, hass):
        """A house that JUST became empty must not satisfy a long
        recheck_min_away_duration, even if recheck_delay itself has elapsed."""
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(
                recheck_on_disarm=True, recheck_delay=0, recheck_min_away_duration=300,
            ),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.05)
        assert manager._all_away_since is not None  # just set moments ago

        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.1)

        assert coordinator.arm_away_calls == 0  # 300s minimum not met
        assert manager._home_empty is False

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_min_away_duration_allows_long_standing_empty_house(self, hass):
        """A house that's been continuously empty well past the minimum must
        be honoured -- guards against the min-away check being overzealous."""
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(
                recheck_on_disarm=True, recheck_delay=0, recheck_min_away_duration=300,
            ),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.05)
        # Simulate the house having been empty for a long time already
        manager._all_away_since = time.monotonic() - 400

        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.1)

        assert coordinator.arm_away_calls == 1

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_include_flags_restrict_action_types(self, hass):
        """recheck_include_alarm=False must exclude alarm from THIS recheck
        cycle even though auto_alarm_enabled is globally True -- the include
        flags only narrow, they never widen what's globally enabled."""
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(
                auto_lock_enabled=True,
                recheck_on_disarm=True, recheck_delay=0, recheck_min_away_duration=0,
                recheck_include_alarm=False,
            ),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.05)

        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.1)

        assert coordinator.arm_away_calls == 0
        assert "lock" in manager._done_actions
        assert "alarm" not in manager._done_actions
        assert "alarm_skipped" not in manager._done_actions

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_no_include_flags_selected_does_nothing(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(
                recheck_on_disarm=True, recheck_delay=0, recheck_min_away_duration=0,
                recheck_include_lock=False, recheck_include_alarm=False,
                recheck_include_camera=False,
            ),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.05)

        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.1)

        assert coordinator.arm_away_calls == 0
        assert manager._home_empty is False  # _on_home_empty() never even called

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_arrival_cancels_pending_recheck(self, hass):
        """A person confirmed home while the recheck delay is still counting
        down must cancel the pending recheck task and reset _all_away_since."""
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(
                recheck_on_disarm=True, recheck_delay=1, recheck_min_away_duration=0,
                arrival_confirmation_delay=0,
            ),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.05)

        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.05)  # recheck task now waiting out its 1s delay

        # Person comes home before the recheck delay elapses
        hass.states.async_set("person.flemming", "home")
        await asyncio.sleep(0.1)  # arrival confirmation (delay=0) resolves almost immediately

        await asyncio.sleep(1.1)  # wait past what would have been the recheck delay
        assert coordinator.arm_away_calls == 0
        assert manager._all_away_since is None

        await manager.async_stop()


# -----------------------------------------------------------------------------
# 2. Initial-presence check at startup
# -----------------------------------------------------------------------------

class TestInitialPresenceCheck:
    """async_start() must detect an already-empty house at HA startup, since
    hass.bus.async_listen only fires on future state changes."""

    @pytest.mark.asyncio
    async def test_all_tracked_users_already_away_triggers_actions(self, hass):
        hass.states.async_set("person.flemming", "not_home")

        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(),
        )
        coordinator = FakeAutoActionsCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.1)  # let _check_initial_presence() + 0-delay action run

        assert manager._home_empty is True
        assert coordinator.arm_away_calls == 1

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_someone_home_at_startup_does_not_trigger(self, hass):
        hass.states.async_set("person.flemming", "home")

        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(),
        )
        coordinator = FakeAutoActionsCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.05)

        assert manager._home_empty is False
        assert coordinator.arm_away_calls == 0

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_no_tracked_users_does_not_error(self, hass):
        """No Secure Me users configured at all -- must not crash or trigger."""
        store = FakeAutoActionsStore(users={}, auto_actions=_aa_config())
        coordinator = FakeAutoActionsCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.05)

        assert manager._home_empty is False
        assert coordinator.arm_away_calls == 0

        await manager.async_stop()


# -----------------------------------------------------------------------------
# 3. Fake Presence re-checked at execution time (race-condition fix)
# -----------------------------------------------------------------------------

class TestFakePresenceExecutionTimeRecheck:
    """Fake Presence toggled ON after an action is scheduled but before its
    delay elapses must still block that action -- not just Fake Presence
    active at the moment the house was first found empty."""

    @pytest.mark.asyncio
    async def test_fake_presence_enabled_mid_countdown_blocks_action(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        fp = {"active": False, "block_alarm": True, "block_locks": False, "block_cameras": False}

        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(auto_alarm_delay=1),
            fake_presence=fp,
        )
        coordinator = FakeAutoActionsCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.1)  # initial check runs; Fake Presence inactive -> action scheduled

        assert manager._home_empty is True
        assert coordinator.arm_away_calls == 0  # still counting down the 1s delay

        # Fake Presence turns on mid-countdown, now blocking alarm
        fp["active"] = True

        await asyncio.sleep(1.1)  # let the 1s delay elapse

        assert coordinator.arm_away_calls == 0  # blocked at execution time, not just scheduling time
        assert "alarm_skipped" in manager._done_actions

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_fake_presence_inactive_throughout_action_still_runs(self, hass):
        """Control case: without the mid-countdown toggle, the action must
        still run normally -- guards against the re-check being overzealous
        and blocking everything."""
        hass.states.async_set("person.flemming", "not_home")
        fp = {"active": False, "block_alarm": True, "block_locks": False, "block_cameras": False}

        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(auto_alarm_delay=0),
            fake_presence=fp,
        )
        coordinator = FakeAutoActionsCoordinator()
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.1)

        assert coordinator.arm_away_calls == 1
        assert "alarm" in manager._done_actions

        await manager.async_stop()


# -----------------------------------------------------------------------------
# Helper-method regression tests
# -----------------------------------------------------------------------------

class TestAllPersonsAwayFailSafe:
    """_all_persons_away() must treat unclear tracker states as "not away",
    never as "away" -- the same fail-safe direction the removed
    PresenceMonitor's _all_away() used."""

    @pytest.mark.asyncio
    async def test_unavailable_tracker_is_not_away(self, hass):
        hass.states.async_set("person.flemming", "unavailable")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
        )
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._all_persons_away() is False

    @pytest.mark.asyncio
    async def test_unknown_tracker_is_not_away(self, hass):
        hass.states.async_set("person.flemming", "unknown")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
        )
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._all_persons_away() is False

    @pytest.mark.asyncio
    async def test_missing_tracker_state_is_not_away(self, hass):
        """Entity configured but no state exists yet in HA (e.g. device
        tracker integration not yet loaded) -- must not be treated as away."""
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.never_seen"}},
        )
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._all_persons_away() is False

    @pytest.mark.asyncio
    async def test_no_tracked_entities_is_not_away(self, hass):
        """Empty tracker set (no Secure Me users configured) must return
        False, not True -- an empty set should never be read as "everyone
        is away"."""
        store = FakeAutoActionsStore(users={})
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._all_persons_away() is False

    @pytest.mark.asyncio
    async def test_all_tracked_not_home_is_away(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        hass.states.async_set("person.partner", "not_home")
        store = FakeAutoActionsStore(users={
            "u1": {"enabled": True, "person_entity": "person.flemming"},
            "u2": {"enabled": True, "person_entity": "person.partner"},
        })
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._all_persons_away() is True

    @pytest.mark.asyncio
    async def test_one_tracked_home_blocks_away(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        hass.states.async_set("person.partner", "home")
        store = FakeAutoActionsStore(users={
            "u1": {"enabled": True, "person_entity": "person.flemming"},
            "u2": {"enabled": True, "person_entity": "person.partner"},
        })
        manager = AutoActionsManager(hass, FakeAutoActionsCoordinator(), store)
        manager.async_refresh_trackers()

        assert manager._all_persons_away() is False


# -----------------------------------------------------------------------------
# 4. Skip ALL actions when already armed in any mode (not just alarm re-arm)
# -----------------------------------------------------------------------------

class TestSkipAllWhenAlreadyArmed:
    """_on_home_empty() must skip scheduling ANY action (lock/alarm/camera) --
    not just re-arming -- when the alarm is already armed, regardless of
    which mode. Previously only _do_alarm() itself guarded against
    re-arming (by checking for STATE_ALARM_DISARMED); lock and camera had
    no equivalent guard and would still fire even while e.g. armed_home_alone.
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("armed_state", [
        STATE_ALARM_ARMED_AWAY,
        STATE_ALARM_ARMED_HOME,
        STATE_ALARM_ARMED_NIGHT,
        STATE_ALARM_ARMED_VACATION,
        STATE_ALARM_ARMED_HOME_ALONE,
    ])
    async def test_no_actions_scheduled_when_already_armed(self, hass, armed_state):
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(auto_lock_enabled=True, auto_camera_enabled=True),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = armed_state
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.1)  # let the initial-presence check run

        assert manager._home_empty is False
        assert coordinator.arm_away_calls == 0

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_actions_still_run_normally_once_disarmed(self, hass):
        """Control case: with the alarm actually disarmed, actions must still
        schedule and run normally -- guards against the new check being
        overzealous and blocking everything."""
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_DISARMED
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.1)

        assert manager._home_empty is True
        assert coordinator.arm_away_calls == 1

        await manager.async_stop()


# -----------------------------------------------------------------------------
# 5. Re-check after remote disarm (AA_RECHECK_ON_DISARM, opt-in)
# -----------------------------------------------------------------------------

class TestRecheckOnDisarm:
    """AA_RECHECK_ON_DISARM (default off): when enabled, disarming while
    every tracked user is still away re-starts the empty-house cycle,
    since no tracker transition would otherwise ever notify Auto Actions."""

    @pytest.mark.asyncio
    async def test_disabled_by_default_ignores_disarm(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(),  # recheck_on_disarm defaults to False
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.05)
        assert manager._home_empty is False  # already armed -- skipped

        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.05)

        assert manager._home_empty is False  # recheck disabled -- still nothing
        assert coordinator.arm_away_calls == 0

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_enabled_reschedules_when_all_still_away(self, hass):
        hass.states.async_set("person.flemming", "not_home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(recheck_on_disarm=True),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_AWAY
        manager = AutoActionsManager(hass, coordinator, store)
        manager._send_summary_notification = AsyncMock()

        manager.async_start()
        await asyncio.sleep(0.05)
        assert manager._home_empty is False  # already armed at startup -- skipped

        # Remote disarm (e.g. via the app) -- nobody's tracker changes
        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.1)

        assert manager._home_empty is True
        assert coordinator.arm_away_calls == 1

        await manager.async_stop()

    @pytest.mark.asyncio
    async def test_enabled_but_someone_home_does_not_reschedule(self, hass):
        hass.states.async_set("person.flemming", "home")
        store = FakeAutoActionsStore(
            users={"u1": {"enabled": True, "person_entity": "person.flemming"}},
            auto_actions=_aa_config(recheck_on_disarm=True),
        )
        coordinator = FakeAutoActionsCoordinator()
        coordinator.alarm_state = STATE_ALARM_ARMED_HOME
        manager = AutoActionsManager(hass, coordinator, store)

        manager.async_start()
        await asyncio.sleep(0.05)

        coordinator.alarm_state = STATE_ALARM_DISARMED
        hass.bus.async_fire(EVENT_ALARM_DISARMED, {})
        await asyncio.sleep(0.05)

        assert manager._home_empty is False
        assert coordinator.arm_away_calls == 0

        await manager.async_stop()
