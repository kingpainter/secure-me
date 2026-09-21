"""Secure Me engine modules.

Engines are testable, standalone state machines that:
- Have NO direct HA dependencies (except logger/hass as parameters)
- Can be unit tested without a running HA instance
- Are called by coordinator.py for orchestration

Engines follow the Heat Manager pattern for clean separation of concerns.
"""

from .base_engine import BaseEngine
from .auto_actions_engine import AutoActionsEngine
from .floorplan_engine import FloorplanEngine
from .notification_engine import NotificationEngine

__all__ = [
    "BaseEngine",
    "AutoActionsEngine",
    "FloorplanEngine",
    "NotificationEngine",
]
