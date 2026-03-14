"""Module manager for Secure Me alarm system."""
# VERSION = "1.0.0"

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    MODULE_CAMERA,
    MODULE_CLIMATE,
    MODULE_LIGHTS,
    MODULE_LOCK,
    MODULE_SIREN,
    MODULE_TTS,
)
from .modules import (
    AlarmModule,
    CameraModule,
    ClimateModule,
    LightsModule,
    LockModule,
    SirenModule,
    TTSModule,
)

_LOGGER = logging.getLogger(__name__)

# Module class mapping
MODULE_CLASSES = {
    MODULE_CAMERA: CameraModule,
    MODULE_CLIMATE: ClimateModule,
    MODULE_LIGHTS: LightsModule,
    MODULE_LOCK: LockModule,
    MODULE_SIREN: SirenModule,
    MODULE_TTS: TTSModule,
}


class ModuleManager:
    """Manage alarm system modules."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize module manager.
        
        Args:
            hass: Home Assistant instance
            config: Module configuration from coordinator
        """
        self.hass = hass
        self.config = config
        self._modules: dict[str, AlarmModule] = {}
        
    async def async_initialize(self) -> bool:
        """Initialize all configured modules.
        
        Returns:
            True if all modules initialized successfully
        """
        _LOGGER.info("Initializing module manager")
        
        modules_config = self.config.get("modules", {})
        
        for module_name, module_config in modules_config.items():
            if not module_config.get("enabled", True):
                _LOGGER.debug("Module %s is disabled, skipping", module_name)
                continue
                
            # Get module class
            module_class = MODULE_CLASSES.get(module_name)
            if not module_class:
                _LOGGER.error("Unknown module: %s", module_name)
                continue
                
            try:
                # Create and initialize module
                module = module_class(self.hass, module_config)
                await module.async_initialize()
                self._modules[module_name] = module
                _LOGGER.info("Module %s initialized", module_name)
            except Exception as err:
                _LOGGER.error("Failed to initialize module %s: %s", module_name, err)
                
        _LOGGER.info("Module manager initialized with %d modules", len(self._modules))
        return True
        
    async def async_shutdown(self) -> None:
        """Shutdown all modules."""
        _LOGGER.info("Shutting down module manager")
        
        for module_name, module in self._modules.items():
            try:
                await module.async_shutdown()
            except Exception as err:
                _LOGGER.error("Failed to shutdown module %s: %s", module_name, err)
                
        self._modules.clear()
        
    async def async_arm(self, mode: str) -> dict[str, bool]:
        """Execute arm action on all modules.
        
        Args:
            mode: Arming mode
            
        Returns:
            Dict mapping module name to success status
        """
        results = {}
        
        for module_name, module in self._modules.items():
            try:
                success = await module.async_arm(mode)
                results[module_name] = success
                if not success:
                    _LOGGER.warning("Module %s arm failed", module_name)
            except Exception as err:
                _LOGGER.error("Module %s arm raised exception: %s", module_name, err)
                results[module_name] = False
                
        return results
        
    async def async_disarm(self) -> dict[str, bool]:
        """Execute disarm action on all modules.
        
        Returns:
            Dict mapping module name to success status
        """
        results = {}
        
        for module_name, module in self._modules.items():
            try:
                success = await module.async_disarm()
                results[module_name] = success
                if not success:
                    _LOGGER.warning("Module %s disarm failed", module_name)
            except Exception as err:
                _LOGGER.error("Module %s disarm raised exception: %s", module_name, err)
                results[module_name] = False
                
        return results
        
    async def async_trigger(self) -> dict[str, bool]:
        """Execute trigger action on all modules.
        
        Returns:
            Dict mapping module name to success status
        """
        results = {}
        
        for module_name, module in self._modules.items():
            try:
                success = await module.async_trigger()
                results[module_name] = success
                if not success:
                    _LOGGER.warning("Module %s trigger failed", module_name)
            except Exception as err:
                _LOGGER.error("Module %s trigger raised exception: %s", module_name, err)
                results[module_name] = False
                
        return results
        
    async def async_test_all(self) -> dict[str, dict[str, Any]]:
        """Test all modules.
        
        Returns:
            Dict mapping module name to test results
        """
        results = {}
        
        for module_name, module in self._modules.items():
            try:
                test_result = await module.async_test()
                results[module_name] = test_result
            except Exception as err:
                _LOGGER.error("Module %s test raised exception: %s", module_name, err)
                results[module_name] = {
                    "success": False,
                    "message": f"Test failed: {err}",
                    "details": {},
                }
                
        return results
        
    def get_module(self, module_name: str) -> AlarmModule | None:
        """Get a specific module.
        
        Args:
            module_name: Module name
            
        Returns:
            Module instance or None if not found
        """
        return self._modules.get(module_name)
        
    def is_module_enabled(self, module_name: str) -> bool:
        """Check if a module is enabled.
        
        Args:
            module_name: Module name
            
        Returns:
            True if module is loaded and enabled
        """
        module = self._modules.get(module_name)
        return module is not None and module.enabled
        
    @property
    def enabled_modules(self) -> list[str]:
        """Get list of enabled module names."""
        return list(self._modules.keys())
        
    @property
    def module_count(self) -> int:
        """Get count of enabled modules."""
        return len(self._modules)
