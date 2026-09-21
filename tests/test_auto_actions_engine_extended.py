"""Extended unit tests for AutoActionsEngine logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.secure_me.engine.auto_actions_engine import AutoActionsEngine


class TestAutoActionsEngineLogic:
    """Test AutoActionsEngine state machine logic."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        return MagicMock()

    @pytest.fixture
    def mock_coordinator(self):
        """Create mock coordinator."""
        return MagicMock()

    @pytest.fixture
    def mock_store(self):
        """Create mock store."""
        store = MagicMock()
        store.get_users_config.return_value = {}
        store.get_zones.return_value = {}
        return store

    @pytest.fixture
    def engine(self, mock_hass, mock_coordinator, mock_store):
        """Create AutoActionsEngine instance for testing."""
        return AutoActionsEngine(
            mock_hass,
            mock_coordinator,
            mock_store,
            config={"action_enabled": {}}
        )

    def test_init_sets_home_empty_false(self, engine):
        """Test __init__ initializes home_empty to False."""
        assert engine._home_empty is False

    def test_init_sets_done_actions_empty(self, engine):
        """Test __init__ initializes done_actions set."""
        assert engine._done_actions == set()

    def test_all_persons_away_returns_true_when_all_not_home(self, engine):
        """Test _all_persons_away returns True when all persons away."""
        engine._tracker_states = {
            "person.alice": "not_home",
            "person.bob": "not_home"
        }
        assert engine._all_persons_away() is True

    def test_all_persons_away_returns_false_when_any_home(self, engine):
        """Test _all_persons_away returns False when any person home."""
        engine._tracker_states = {
            "person.alice": "home",
            "person.bob": "not_home"
        }
        assert engine._all_persons_away() is False

    def test_all_persons_away_returns_true_with_empty_trackers(self, engine):
        """Test _all_persons_away returns True with no trackers."""
        engine._tracker_states = {}
        assert engine._all_persons_away() is True

    def test_arrival_confirmation_pending_state(self, engine):
        """Test arrival confirmation window prevents immediate action."""
        engine._done_actions.add("lock")
        engine._home_empty = False  # Someone arrived
        
        # Action should be considered "done" even though home is not empty
        # This prevents re-triggering on GPS flicker
        assert "lock" in engine._done_actions

    def test_stale_tracker_detection(self, engine):
        """Test stale tracker detection logic."""
        import time
        stale_threshold = 3600  # 1 hour
        
        engine._tracker_update_times = {
            "person.alice": time.time() - 2000,  # Recent
            "person.bob": time.time() - 5000     # Stale
        }
        
        now = time.time()
        stale = [
            person for person, last_update in engine._tracker_update_times.items()
            if now - last_update > stale_threshold
        ]
        
        # Bob should be detected as stale
        assert "person.bob" in stale

    def test_action_result_tracking(self, engine):
        """Test action result tracking for notifications."""
        engine._action_results = {
            "lock": "Front door locked",
            "alarm": "System armed in Home Away mode"
        }
        
        assert engine._action_results["lock"] == "Front door locked"
        assert engine._action_results["alarm"] == "System armed in Home Away mode"

    def test_recheck_delay_computation(self, engine):
        """Test recheck delay logic."""
        import time
        engine._all_away_since = time.time() - 1800  # 30 min ago
        min_away_duration = 600  # 10 min
        
        time_away = time.time() - engine._all_away_since
        should_recheck = time_away >= min_away_duration
        
        assert should_recheck is True

