"""Base module class for Secure Me alarm system."""
# VERSION = "0.3.6"

import logging
from abc import ABC, abstractmethod
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class AlarmModule(ABC):
    """Base class for all alarm system modules."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the module.
        
        Args:
            hass: Home Assistant instance
            config: Module configuration from coordinator
        """
        self.hass = hass
        self.config = config
        self._enabled = config.get("enabled", True)
        self._state_backup = {}
        
    @property
    def enabled(self) -> bool:
        """Return if module is enabled."""
        return self._enabled
        
    @property
    def module_name(self) -> str:
        """Return module name."""
        return self.__class__.__name__.replace("Module", "")
        
    @abstractmethod
    async def async_arm(self, mode: str) -> bool:
        """Execute when alarm is armed.
        
        Args:
            mode: Arming mode (away, home, night, vacation)
            
        Returns:
            True if successful, False otherwise
        """
        
    @abstractmethod
    async def async_disarm(self) -> bool:
        """Execute when alarm is disarmed.
        
        Returns:
            True if successful, False otherwise
        """
        
    @abstractmethod
    async def async_trigger(self) -> bool:
        """Execute when alarm is triggered.
        
        Returns:
            True if successful, False otherwise
        """
        
    @abstractmethod
    async def async_test(self) -> dict[str, Any]:
        """Test module functionality.
        
        Returns:
            Dict with test results:
            {
                "success": bool,
                "message": str,
                "details": dict
            }
        """
        
    async def async_initialize(self) -> bool:
        """Initialize module on startup.
        
        Returns:
            True if successful, False otherwise
        """
        _LOGGER.info("%s module initialized", self.module_name)
        return True
        
    async def async_shutdown(self) -> None:
        """Cleanup when module is shut down."""
        _LOGGER.info("%s module shutdown", self.module_name)
    
    async def async_cleanup(self) -> None:
        """Cleanup method called by coordinator.
        
        This is an alias for async_shutdown() to maintain compatibility
        with coordinator's cleanup calls.
        """
        await self.async_shutdown()
        
    def backup_state(self, entity_id: str) -> None:
        """Backup current state of an entity.
        
        Args:
            entity_id: Entity to backup
        """
        state = self.hass.states.get(entity_id)
        if state:
            self._state_backup[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes),
            }
            _LOGGER.debug("Backed up state for %s", entity_id)
            
    def get_backup_state(self, entity_id: str) -> dict[str, Any] | None:
        """Get backed up state for an entity.
        
        Args:
            entity_id: Entity to get backup for
            
        Returns:
            Backup dict or None if not found
        """
        return self._state_backup.get(entity_id)
        
    def clear_backup(self, entity_id: str | None = None) -> None:
        """Clear state backup.
        
        Args:
            entity_id: Specific entity to clear, or None for all
        """
        if entity_id:
            self._state_backup.pop(entity_id, None)
        else:
            self._state_backup.clear()
            
    async def async_call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
    ) -> bool:
        """Call a Home Assistant service with error handling.
        
        Args:
            domain: Service domain
            service: Service name
            service_data: Service data
            target: Service target
            
        Returns:
            True if successful, False otherwise
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
                self.module_name,
                domain,
                service,
                err,
            )
            return False
            
    def is_entity_available(self, entity_id: str) -> bool:
        """Check if entity is available.
        
        Args:
            entity_id: Entity to check
            
        Returns:
            True if available, False otherwise
        """
        state = self.hass.states.get(entity_id)
        return state is not None and state.state not in ("unavailable", "unknown")
        
    def get_entity_state(self, entity_id: str) -> str | None:
        """Get entity state.
        
        Args:
            entity_id: Entity to check
            
        Returns:
            Entity state or None if not found
        """
        state = self.hass.states.get(entity_id)
        return state.state if state else None
        
    def enable(self) -> None:
        """Enable the module."""
        self._enabled = True
        _LOGGER.info("%s module enabled", self.module_name)
        
    def disable(self) -> None:
        """Disable the module."""
        self._enabled = False
        _LOGGER.info("%s module disabled", self.module_name)
