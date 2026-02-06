"""Climate module for Secure Me alarm system."""
# VERSION = "0.2.0"

import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)


class ClimateModule(AlarmModule):
    """Climate control module for multi-zone heating/cooling."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize climate module.
        
        Config options:
            - climates: List of climate entity IDs
            - away_mode: Set to away when arming (default: True)
            - restore_on_disarm: Restore previous preset (default: True)
            - away_temperature: Temperature for away mode (optional)
        """
        super().__init__(hass, config)
        
        self.climates = config.get("climates", [])
        self.away_mode = config.get("away_mode", True)
        self.restore_on_disarm = config.get("restore_on_disarm", True)
        self.away_temperature = config.get("away_temperature")
        
    async def async_arm(self, mode: str) -> bool:
        """Set climate to away mode when arming.
        
        - Backup current presets/temperatures
        - Set to away mode (if supported)
        """
        if not self.enabled or not self.away_mode:
            return True
            
        try:
            for climate in self.climates:
                # Backup current state
                self.backup_state(climate)
                
                # Get current preset modes
                state = self.hass.states.get(climate)
                if not state:
                    continue
                    
                preset_modes = state.attributes.get("preset_modes", [])
                
                # Set to away if supported
                if "away" in preset_modes:
                    await self.async_call_service(
                        "climate",
                        "set_preset_mode",
                        service_data={"preset_mode": "away"},
                        target={"entity_id": climate}
                    )
                elif self.away_temperature:
                    # Set away temperature if preset not available
                    await self.async_call_service(
                        "climate",
                        "set_temperature",
                        service_data={"temperature": self.away_temperature},
                        target={"entity_id": climate}
                    )
                    
            _LOGGER.info("Climate module: Set to away mode")
            return True
            
        except Exception as err:
            _LOGGER.error("Climate module arm failed: %s", err)
            return False
            
    async def async_disarm(self) -> bool:
        """Restore climate settings when disarming.
        
        - Restore previous presets/temperatures
        """
        if not self.enabled:
            return True
            
        try:
            if self.restore_on_disarm:
                for climate in self.climates:
                    await self._restore_climate_state(climate)
                _LOGGER.info("Climate module: Settings restored")
            else:
                # Just set to comfort/home mode
                for climate in self.climates:
                    state = self.hass.states.get(climate)
                    if state:
                        preset_modes = state.attributes.get("preset_modes", [])
                        if "home" in preset_modes:
                            await self.async_call_service(
                                "climate",
                                "set_preset_mode",
                                service_data={"preset_mode": "home"},
                                target={"entity_id": climate}
                            )
                _LOGGER.info("Climate module: Set to home mode")
                
            # Clear backup
            self.clear_backup()
            
            return True
            
        except Exception as err:
            _LOGGER.error("Climate module disarm failed: %s", err)
            return False
            
    async def async_trigger(self) -> bool:
        """No action needed on trigger (keep away mode)."""
        return True
        
    async def async_test(self) -> dict[str, Any]:
        """Test climate module functionality.
        
        Tests:
        - Climate entity availability
        - Current states
        - Supported preset modes
        - Temperature settings
        """
        results = {
            "success": True,
            "message": "Climate module test passed",
            "details": {
                "climates": [],
                "total_zones": len(self.climates),
            }
        }
        
        for climate in self.climates:
            climate_info = {
                "entity_id": climate,
                "available": False,
                "current_temperature": None,
                "target_temperature": None,
                "preset_mode": None,
                "preset_modes": [],
                "hvac_mode": None,
            }
            
            climate_info["available"] = self.is_entity_available(climate)
            state = self.hass.states.get(climate)
            
            if state:
                climate_info["current_temperature"] = state.attributes.get("current_temperature")
                climate_info["target_temperature"] = state.attributes.get("temperature")
                climate_info["preset_mode"] = state.attributes.get("preset_mode")
                climate_info["preset_modes"] = state.attributes.get("preset_modes", [])
                climate_info["hvac_mode"] = state.state
                
            if not climate_info["available"]:
                results["success"] = False
                results["message"] = f"Climate {climate} unavailable"
                
            # Check if away mode is supported
            if "away" not in climate_info["preset_modes"] and not self.away_temperature:
                results["message"] = f"Climate {climate} doesn't support away mode"
                
            results["details"]["climates"].append(climate_info)
            
        return results
        
    async def _restore_climate_state(self, climate: str) -> None:
        """Restore a climate entity to its backed up state.
        
        Args:
            climate: Climate entity ID
        """
        backup = self.get_backup_state(climate)
        if not backup:
            return
            
        attrs = backup.get("attributes", {})
        
        # Restore preset mode if available
        preset_mode = attrs.get("preset_mode")
        if preset_mode and preset_mode != "away":
            await self.async_call_service(
                "climate",
                "set_preset_mode",
                service_data={"preset_mode": preset_mode},
                target={"entity_id": climate}
            )
        else:
            # Restore temperature
            temperature = attrs.get("temperature")
            if temperature:
                await self.async_call_service(
                    "climate",
                    "set_temperature",
                    service_data={"temperature": temperature},
                    target={"entity_id": climate}
                )
