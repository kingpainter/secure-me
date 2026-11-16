"""Typed per-entry runtime data for Secure Me config entries."""

# VERSION = "2.3.0"
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .coordinator import SecureMeCoordinator


@dataclass
class SecureMeRuntimeData:
    """Objects owned by one loaded Secure Me config entry."""

    coordinator: SecureMeCoordinator
    undo_update_listener: Callable[[], None] | None = None


SecureMeConfigEntry = ConfigEntry[SecureMeRuntimeData]
