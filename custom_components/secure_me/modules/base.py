"""Base module class for Secure Me alarm system."""
# VERSION = "1.2.0"

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from homeassistant.core import HomeAssistant

from ..const import (
    DEFAULT_RETRY_MAX,
    DEFAULT_RETRY_DELAY,
    DEFAULT_RETRY_BACKOFF,
    NOTIFY_ID_MODULE_ERROR,
    NOTIFY_ID_RECOVERY,
    ERROR_RETRY_EXHAUSTED_EN,
    ERROR_RECOVERY_OK_EN,
)

_LOGGER = logging.getLogger(__name__)


class AlarmModule(ABC):
    """Base class for all alarm system modules."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the module."""
        self.hass = hass
        self.config = config
        self._enabled = config.get("enabled", True)
        self._state_backup = {}

        # Retry configuration (can be overridden per module via config)
        self._retry_max: int = config.get("retry_max", DEFAULT_RETRY_MAX)
        self._retry_delay: float = config.get("retry_delay", DEFAULT_RETRY_DELAY)
        self._retry_backoff: float = config.get("retry_backoff", DEFAULT_RETRY_BACKOFF)

        # Track consecutive errors for graceful degradation
        self._consecutive_errors: int = 0
        self._degraded: bool = False

    @property
    def enabled(self) -> bool:
        """Return if module is enabled."""
        return self._enabled

    @property
    def degraded(self) -> bool:
        """Return True if module is in degraded (error) state."""
        return self._degraded

    @property
    def module_name(self) -> str:
        """Return module name."""
        return self.__class__.__name__.replace("Module", "")

    @abstractmethod
    async def async_arm(self, mode: str) -> bool:
        """Execute when alarm is armed."""

    @abstractmethod
    async def async_disarm(self) -> bool:
        """Execute when alarm is disarmed."""

    @abstractmethod
    async def async_trigger(self) -> bool:
        """Execute when alarm is triggered."""

    @abstractmethod
    async def async_test(self) -> dict[str, Any]:
        """Test module functionality."""

    async def async_initialize(self) -> bool:
        """Initialize module on startup."""
        _LOGGER.info("%s module initialized", self.module_name)
        return True

    async def async_shutdown(self) -> None:
        """Cleanup when module is shut down."""
        _LOGGER.info("%s module shutdown", self.module_name)

    async def async_cleanup(self) -> None:
        """Cleanup method called by coordinator."""
        await self.async_shutdown()

    # ── Retry & Graceful Degradation ────────────────────────────────────────

    async def async_call_service_with_retry(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
        action: str = "service_call",
    ) -> bool:
        """Call a HA service with exponential backoff retry.

        Attempts the call up to self._retry_max times.
        Delay doubles each attempt: delay, delay*backoff, delay*backoff^2 ...

        On final failure:
        - Sets module to degraded state
        - Fires persistent_notification to the user
        - Logs error

        On success after retry:
        - Clears degraded state
        - Fires recovery notification if previously degraded
        """
        delay = self._retry_delay

        for attempt in range(1, self._retry_max + 1):
            try:
                await self.hass.services.async_call(
                    domain,
                    service,
                    service_data=service_data,
                    target=target,
                    blocking=True,
                )
                # Success
                if attempt > 1:
                    _LOGGER.info(
                        "%s: %s succeeded on attempt %d/%d",
                        self.module_name, action, attempt, self._retry_max,
                    )
                self._on_success(action)
                return True

            except Exception as err:
                _LOGGER.warning(
                    "%s: %s failed (attempt %d/%d): %s",
                    self.module_name, action, attempt, self._retry_max, err,
                )
                if attempt < self._retry_max:
                    await asyncio.sleep(delay)
                    delay *= self._retry_backoff

        # All retries exhausted
        self._on_failure(action)
        return False

    async def async_call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
    ) -> bool:
        """Call a HA service — single attempt with error handling.

        For operations that should NOT retry (e.g. test calls, state reads).
        Use async_call_service_with_retry() for critical alarm operations.
        """
        try:
            await self.hass.services.async_call(
                domain,
                service,
                service_data=service_data,
                target=target,
                blocking=True,
            )
            return True
        except Exception as err:
            _LOGGER.error(
                "%s module failed to call service %s.%s: %s",
                self.module_name, domain, service, err,
            )
            return False

    def _on_success(self, action: str) -> None:
        """Handle successful service call — clear degraded state if set."""
        previously_degraded = self._degraded
        self._consecutive_errors = 0
        self._degraded = False

        if previously_degraded:
            _LOGGER.info("%s: recovered from degraded state after '%s'", self.module_name, action)
            msg = ERROR_RECOVERY_OK_EN.format(module=self.module_name)
            self.hass.components.persistent_notification.async_create(
                message=msg,
                title="Secure Me - Recovery",
                notification_id=f"{NOTIFY_ID_RECOVERY}_{self.module_name.lower()}",
            )

    def _on_failure(self, action: str) -> None:
        """Handle exhausted retries — set degraded state and notify user."""
        self._consecutive_errors += 1
        self._degraded = True

        msg = ERROR_RETRY_EXHAUSTED_EN.format(
            module=self.module_name,
            retries=self._retry_max,
            action=action,
        )
        _LOGGER.error(
            "%s: all %d retries exhausted for '%s' — module set to degraded",
            self.module_name, self._retry_max, action,
        )
        self.hass.components.persistent_notification.async_create(
            message=msg,
            title="Secure Me - Module Error",
            notification_id=f"{NOTIFY_ID_MODULE_ERROR}_{self.module_name.lower()}",
        )

    # ── State backup / restore ───────────────────────────────────────────────

    def backup_state(self, entity_id: str) -> None:
        """Backup current state of an entity."""
        state = self.hass.states.get(entity_id)
        if state:
            self._state_backup[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes),
            }
            _LOGGER.debug("Backed up state for %s", entity_id)

    def get_backup_state(self, entity_id: str) -> dict[str, Any] | None:
        """Get backed up state for an entity."""
        return self._state_backup.get(entity_id)

    def clear_backup(self, entity_id: str | None = None) -> None:
        """Clear state backup."""
        if entity_id:
            self._state_backup.pop(entity_id, None)
        else:
            self._state_backup.clear()

    # ── Entity helpers ───────────────────────────────────────────────────────

    def is_entity_available(self, entity_id: str) -> bool:
        """Check if entity is available."""
        state = self.hass.states.get(entity_id)
        return state is not None and state.state not in ("unavailable", "unknown")

    def get_entity_state(self, entity_id: str) -> str | None:
        """Get entity state."""
        state = self.hass.states.get(entity_id)
        return state.state if state else None

    def enable(self) -> None:
        """Enable the module."""
        self._enabled = True
        self._degraded = False
        self._consecutive_errors = 0
        _LOGGER.info("%s module enabled", self.module_name)

    def disable(self) -> None:
        """Disable the module."""
        self._enabled = False
        _LOGGER.info("%s module disabled", self.module_name)

