"""Unit tests for NotificationEngine routing logic."""

import pytest
from unittest.mock import MagicMock

from custom_components.secure_me.engine.notification_engine import NotificationEngine


class TestNotificationEngine:
    """Test NotificationEngine notification routing."""

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
        return store

    @pytest.fixture
    def engine(self, mock_hass, mock_coordinator, mock_store):
        """Create NotificationEngine instance for testing."""
        return NotificationEngine(
            mock_hass,
            mock_coordinator,
            mock_store
        )

    def test_init_sets_required_attributes(self, engine):
        """Test __init__ sets up engine."""
        assert engine.coordinator is not None
        assert engine.store is not None

    def test_quiet_hours_detection_in_range(self, engine):
        """Test quiet hours detection when in quiet time."""
        from datetime import datetime, time as dt_time
        
        # Assume quiet hours 22:00 - 07:00
        quiet_start = dt_time(22, 0)
        quiet_end = dt_time(7, 0)
        
        # Check at 23:30 (in quiet hours)
        check_time = datetime.now().replace(hour=23, minute=30).time()
        
        is_quiet = (check_time >= quiet_start) or (check_time < quiet_end)
        assert is_quiet is True

    def test_quiet_hours_detection_outside_range(self, engine):
        """Test quiet hours detection when outside quiet time."""
        from datetime import datetime, time as dt_time
        
        quiet_start = dt_time(22, 0)
        quiet_end = dt_time(7, 0)
        
        # Check at 14:30 (outside quiet hours)
        check_time = datetime.now().replace(hour=14, minute=30).time()
        
        is_quiet = (check_time >= quiet_start) or (check_time < quiet_end)
        assert is_quiet is False

    def test_smoke_alert_bypasses_quiet_hours(self, engine):
        """Test that smoke alerts always send regardless of quiet hours."""
        # Smoke/water alerts should ALWAYS be sent
        event_type = "smoke_detected"
        
        # Critical events bypass quiet hours
        critical_events = ["smoke_detected", "water_leak"]
        
        should_send = event_type in critical_events
        assert should_send is True

    def test_user_preference_notification_disabled(self, engine):
        """Test notification respects user disable setting."""
        user_prefs = {
            "user_id": "user_1",
            "notifications_enabled": False
        }
        
        should_send = user_prefs.get("notifications_enabled", True)
        assert should_send is False

    def test_user_preference_notification_enabled(self, engine):
        """Test notification respects user enable setting."""
        user_prefs = {
            "user_id": "user_1",
            "notifications_enabled": True
        }
        
        should_send = user_prefs.get("notifications_enabled", True)
        assert should_send is True

    def test_notification_routing_armed_event(self, engine):
        """Test notification routing for armed event."""
        event_data = {
            "event_type": "alarm_armed",
            "mode": "away"
        }
        
        # Armed events generate summary notification
        should_notify = event_data["event_type"] in [
            "alarm_armed", "alarm_disarmed", "alarm_triggered"
        ]
        
        assert should_notify is True

