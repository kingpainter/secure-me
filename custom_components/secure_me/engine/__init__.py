#!/usr/bin/env python3
"""Secure Me engine modules.

Engines are testable, standalone state machines that:
- Have NO direct HA dependencies (except logger/hass as parameters)
- Can be unit tested without a running HA instance
- Are called by coordinator.py for orchestration

Engines follow the Heat Manager pattern for clean separation of concerns.
"""

from __future__ import annotations

from .base_engine import BaseEngine
from .floorplan_engine import FloorplanEngine
from .notification_engine import NotificationEngine

__all__ = [
    "BaseEngine",
    "FloorplanEngine",
    "NotificationEngine",
]
