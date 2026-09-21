"""Floorplan Engine for Secure Me.

Pure state machine for floorplan management:
  - Tracks rooms, openings, markers (in-memory state)
  - Calculates room status from opening states
  - No direct HA dependencies (except hass for callbacks/tasks)

State is persisted by store.py, engine is the computation layer.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base_engine import BaseEngine

_LOGGER = logging.getLogger(__name__)


class FloorplanEngine(BaseEngine):
    """Manages floorplan state: rooms, openings, markers.
    
    Pure state machine that can be tested without Home Assistant.
    Coordinator persists state to store.py.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize FloorplanEngine."""
        super().__init__(hass, config or {})
        
        # In-memory state
        self.rooms: dict[str, dict[str, Any]] = {}
        self.openings: dict[str, dict[str, Any]] = {}
        self.markers: dict[str, dict[str, Any]] = {}
        
        # Metadata
        self.floorplan_image_url: str | None = None
        self.floorplan_width: int = 0
        self.floorplan_height: int = 0

    async def async_start(self) -> None:
        """Start the engine."""
        await super().async_start()
        self.logger.debug("FloorplanEngine started")

    async def async_stop(self) -> None:
        """Stop the engine."""
        await super().async_stop()
        self.logger.debug("FloorplanEngine stopped")

    def load_state(self, state: dict[str, Any]) -> None:
        """Load floorplan state from store config.
        
        Args:
            state: Dict with rooms, openings, markers from store
        """
        self.rooms = state.get("rooms", {})
        self.openings = state.get("openings", {})
        self.markers = state.get("markers", {})
        self.floorplan_image_url = state.get("image_url")
        self.floorplan_width = state.get("width", 0)
        self.floorplan_height = state.get("height", 0)
        self.logger.debug(f"Loaded floorplan state: {len(self.rooms)} rooms, {len(self.openings)} openings")

    def get_state(self) -> dict[str, Any]:
        """Get current floorplan state for persistence.
        
        Returns:
            Dict ready for store.py
        """
        return {
            "rooms": self.rooms,
            "openings": self.openings,
            "markers": self.markers,
            "image_url": self.floorplan_image_url,
            "width": self.floorplan_width,
            "height": self.floorplan_height,
        }

    def set_floorplan_image(
        self, image_url: str, width: int, height: int
    ) -> None:
        """Update floorplan image metadata.
        
        Args:
            image_url: URL to the floorplan image
            width: Image width in pixels
            height: Image height in pixels
        """
        self.floorplan_image_url = image_url
        self.floorplan_width = width
        self.floorplan_height = height
        self.logger.debug(f"Updated floorplan image: {image_url} ({width}x{height})")

    def clear_floorplan_image(self) -> None:
        """Clear floorplan image (but keep rooms/openings/markers)."""
        self.floorplan_image_url = None
        self.floorplan_width = 0
        self.floorplan_height = 0
        self.logger.debug("Cleared floorplan image")

    def add_room(self, room_id: str, room_data: dict[str, Any]) -> None:
        """Add or update a room.
        
        Args:
            room_id: Unique room identifier
            room_data: Room metadata (name, position, etc.)
        """
        self.rooms[room_id] = room_data
        self.logger.debug(f"Added room: {room_id}")

    def remove_room(self, room_id: str) -> None:
        """Remove a room."""
        if room_id in self.rooms:
            del self.rooms[room_id]
            self.logger.debug(f"Removed room: {room_id}")

    def add_opening(self, opening_id: str, opening_data: dict[str, Any]) -> None:
        """Add or update an opening (door/window).
        
        Args:
            opening_id: Unique opening identifier
            opening_data: Opening metadata (name, room_id, type, state, etc.)
        """
        self.openings[opening_id] = opening_data
        self.logger.debug(f"Added opening: {opening_id}")

    def remove_opening(self, opening_id: str) -> None:
        """Remove an opening."""
        if opening_id in self.openings:
            del self.openings[opening_id]
            self.logger.debug(f"Removed opening: {opening_id}")

    def update_opening_state(self, opening_id: str, state: str) -> None:
        """Update an opening's state (open/closed).
        
        Args:
            opening_id: Opening identifier
            state: New state (open/closed)
        """
        if opening_id in self.openings:
            self.openings[opening_id]["state"] = state
            self.logger.debug(f"Updated opening {opening_id} state: {state}")

    def get_room_status(self, room_id: str) -> dict[str, Any]:
        """Calculate room status from opening states.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Dict with room metadata and opening status summary
        """
        if room_id not in self.rooms:
            return {}

        room = self.rooms[room_id]
        room_openings = [
            o for o in self.openings.values()
            if o.get("room_id") == room_id
        ]

        any_open = any(o.get("state") == "open" for o in room_openings)
        all_closed = all(o.get("state") == "closed" for o in room_openings)

        return {
            "room_id": room_id,
            "name": room.get("name", "Unknown"),
            "any_open": any_open,
            "all_closed": all_closed,
            "opening_count": len(room_openings),
            "openings": room_openings,
        }

    def set_markers(self, markers: dict[str, Any]) -> None:
        """Update floorplan markers.
        
        Args:
            markers: Dict of marker data
        """
        self.markers = markers or {}
        self.logger.debug(f"Updated {len(self.markers)} floorplan markers")

    def get_summary(self) -> dict[str, Any]:
        """Get summary of floorplan state.
        
        Returns:
            Summary dict for WebSocket client
        """
        open_count = sum(1 for o in self.openings.values() if o.get("state") == "open")
        
        return {
            "image_url": self.floorplan_image_url,
            "image_width": self.floorplan_width,
            "image_height": self.floorplan_height,
            "rooms": len(self.rooms),
            "openings": len(self.openings),
            "openings_open": open_count,
            "markers": len(self.markers),
            "is_configured": bool(self.floorplan_image_url),
        }
