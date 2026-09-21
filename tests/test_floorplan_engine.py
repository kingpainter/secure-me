"""Unit tests for FloorplanEngine state management."""

import pytest
from unittest.mock import MagicMock

from custom_components.secure_me.engine.floorplan_engine import FloorplanEngine


class TestFloorplanEngine:
    """Test FloorplanEngine state management."""

    @pytest.fixture
    def engine(self):
        """Create FloorplanEngine instance for testing."""
        return FloorplanEngine()

    def test_init_creates_empty_state(self, engine):
        """Test __init__ creates empty rooms and openings."""
        assert engine.rooms == {}
        assert engine.openings == {}
        assert engine.markers == {}

    def test_add_room(self, engine):
        """Test add_room creates room entry."""
        engine.add_room("room_1", {"name": "Living Room"})
        
        assert "room_1" in engine.rooms
        assert engine.rooms["room_1"]["name"] == "Living Room"

    def test_remove_room(self, engine):
        """Test remove_room deletes room."""
        engine.add_room("room_1", {"name": "Living Room"})
        assert "room_1" in engine.rooms
        
        engine.remove_room("room_1")
        assert "room_1" not in engine.rooms

    def test_add_opening(self, engine):
        """Test add_opening creates opening entry."""
        engine.add_opening("opening_1", {
            "room_id": "room_1",
            "name": "Front Door",
            "state": "closed"
        })
        
        assert "opening_1" in engine.openings
        assert engine.openings["opening_1"]["room_id"] == "room_1"

    def test_update_opening_state(self, engine):
        """Test update_opening_state modifies state."""
        engine.add_opening("opening_1", {
            "room_id": "room_1",
            "name": "Front Door",
            "state": "closed"
        })
        
        engine.update_opening_state("opening_1", "open")
        assert engine.openings["opening_1"]["state"] == "open"

    def test_get_room_status_no_openings(self, engine):
        """Test get_room_status with no openings."""
        engine.add_room("room_1", {"name": "Living Room"})
        status = engine.get_room_status("room_1")
        
        assert status["room_id"] == "room_1"
        assert status["name"] == "Living Room"
        assert status["any_open"] is False
        assert status["openings"] == []

    def test_get_room_status_with_open_opening(self, engine):
        """Test get_room_status detects open openings."""
        engine.add_room("room_1", {"name": "Living Room"})
        engine.add_opening("opening_1", {
            "room_id": "room_1",
            "name": "Front Door",
            "state": "open"
        })
        
        status = engine.get_room_status("room_1")
        assert status["any_open"] is True
        assert len(status["openings"]) == 1

    def test_get_summary(self, engine):
        """Test get_summary returns full state."""
        engine.add_room("room_1", {"name": "Living Room"})
        engine.add_opening("opening_1", {
            "room_id": "room_1",
            "name": "Front Door",
            "state": "closed"
        })
        
        summary = engine.get_summary()
        assert "rooms" in summary
        assert "openings" in summary
        assert summary["rooms"]["room_1"]["name"] == "Living Room"

    def test_load_and_save_state(self, engine):
        """Test state can be loaded and saved."""
        # Create some state
        engine.add_room("room_1", {"name": "Living Room"})
        engine.add_opening("opening_1", {
            "room_id": "room_1",
            "name": "Front Door",
            "state": "closed"
        })
        
        # Save state
        saved_state = engine.get_state()
        
        # Create new engine and load state
        new_engine = FloorplanEngine()
        new_engine.load_state(saved_state)
        
        # Verify state was restored
        assert new_engine.get_room_status("room_1")["name"] == "Living Room"

