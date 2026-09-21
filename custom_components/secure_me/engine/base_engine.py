"""Base engine class for Secure Me engines.

All engines inherit from BaseEngine to provide:
- Consistent lifecycle management (async_start, async_stop)
- Logging infrastructure
- State tracking patterns
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class BaseEngine:
    """Base class for Secure Me state machine engines.
    
    Engines are testable, HA-agnostic state machines that handle:
    - State tracking
    - Delayed actions
    - Event callback registration
    
    Coordinator orchestrates engine lifecycle and event delivery.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict[str, Any],
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize engine.
        
        Args:
            hass: Home Assistant instance (used for callbacks/tasks)
            config: Configuration dict for this engine
            logger: Optional logger (defaults to _LOGGER)
        """
        self.hass = hass
        self.config = config
        self.logger = logger or _LOGGER
        self._running = False
        self._cleanup_tasks: list[Callable[[], asyncio.Task]] = []

    async def async_start(self) -> None:
        """Start the engine.
        
        Called once by coordinator after all initialization complete.
        Override in subclass to set up event listeners, timers, etc.
        """
        self._running = True
        self.logger.debug(f"{self.__class__.__name__} started")

    async def async_stop(self) -> None:
        """Stop the engine.
        
        Called on integration unload. Cleans up all tasks and listeners.
        Override in subclass to add custom cleanup.
        """
        self._running = False
        
        # Cancel all registered cleanup tasks
        for cleanup in self._cleanup_tasks:
            try:
                task = cleanup()
                if isinstance(task, asyncio.Task):
                    task.cancel()
            except Exception as e:
                self.logger.warning(f"Error during cleanup: {e}")
        
        self._cleanup_tasks.clear()
        self.logger.debug(f"{self.__class__.__name__} stopped")

    def register_cleanup(self, cleanup_fn: Callable[[], asyncio.Task]) -> None:
        """Register a cleanup function to call on async_stop().
        
        Usage:
            unsub = async_track_state_change(...)
            self.register_cleanup(unsub)
        """
        self._cleanup_tasks.append(cleanup_fn)

    def is_running(self) -> bool:
        """Check if engine is currently running."""
        return self._running
