"""Camera module for Secure Me alarm system."""
# VERSION = "0.2.0"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

# Default POE delay for cameras to come online (seconds)
DEFAULT_POE_DELAY = 120


class CameraModule(AlarmModule):
    """Camera control module with POE optimization."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize camera module.
        
        Config options:
            - poe_switches: List of POE switch entity IDs
            - cameras: List of camera entity IDs
            - recording_entities: List of recording mode select entities
            - poe_delay: Seconds to wait for cameras after POE on (default: 120)
            - auto_record: Enable 24/7 recording when armed (default: False)
        """
        super().__init__(hass, config)
        
        self.poe_switches = config.get("poe_switches", [])
        self.cameras = config.get("cameras", [])
        self.recording_entities = config.get("recording_entities", [])
        self.poe_delay = config.get("poe_delay", DEFAULT_POE_DELAY)
        self.auto_record = config.get("auto_record", False)
        
        self._poe_was_on = False
        
    async def async_arm(self, mode: str) -> bool:
        """Turn on cameras when arming.
        
        Smart POE logic:
        - Check if POE already on (saves 120s!)
        - Only wait for delay if POE was off
        - Enable recording if configured
        """
        if not self.enabled:
            return True
            
        try:
            # Check if POE already on (optimization!)
            self._poe_was_on = await self._check_poe_status()
            
            if self._poe_was_on:
                _LOGGER.info(
                    "Camera module: POE already ON - skipping %ds delay! ⚡",
                    self.poe_delay
                )
            else:
                _LOGGER.info(
                    "Camera module: Turning on POE switches and waiting %ds",
                    self.poe_delay
                )
                
                # Turn on POE switches
                for switch in self.poe_switches:
                    await self.async_call_service(
                        "switch",
                        "turn_on",
                        target={"entity_id": switch}
                    )
                
                # Wait for cameras to come online (only if POE was off!)
                await asyncio.sleep(self.poe_delay)
            
            # Enable recording if configured
            if self.auto_record and self.recording_entities:
                for entity in self.recording_entities:
                    await self.async_call_service(
                        "select",
                        "select_option",
                        service_data={"option": "always"},
                        target={"entity_id": entity}
                    )
                    
            _LOGGER.info("Camera module: Cameras activated")
            return True
            
        except Exception as err:
            _LOGGER.error("Camera module arm failed: %s", err)
            return False
            
    async def async_disarm(self) -> bool:
        """Turn off cameras when disarming.
        
        - Disable recording
        - Turn off POE switches (saves power)
        """
        if not self.enabled:
            return True
            
        try:
            # Disable recording
            if self.recording_entities:
                for entity in self.recording_entities:
                    await self.async_call_service(
                        "select",
                        "select_option",
                        service_data={"option": "never"},
                        target={"entity_id": entity}
                    )
                    
            # Short delay before powering off
            await asyncio.sleep(15)
            
            # Turn off POE switches
            for switch in self.poe_switches:
                await self.async_call_service(
                    "switch",
                    "turn_off",
                    target={"entity_id": switch}
                )
                
            _LOGGER.info("Camera module: Cameras deactivated")
            return True
            
        except Exception as err:
            _LOGGER.error("Camera module disarm failed: %s", err)
            return False
            
    async def async_trigger(self) -> bool:
        """No action needed on trigger (cameras already recording)."""
        return True
        
    async def async_test(self) -> dict[str, Any]:
        """Test camera module functionality.
        
        Tests:
        - POE switches available
        - Cameras available
        - Recording entities available
        - POE optimization detection
        """
        results = {
            "success": True,
            "message": "Camera module test passed",
            "details": {
                "poe_switches": [],
                "cameras": [],
                "recording_entities": [],
                "poe_optimization": False,
            }
        }
        
        # Test POE switches
        for switch in self.poe_switches:
            available = self.is_entity_available(switch)
            state = self.get_entity_state(switch)
            results["details"]["poe_switches"].append({
                "entity_id": switch,
                "available": available,
                "state": state,
            })
            if not available:
                results["success"] = False
                results["message"] = f"POE switch {switch} unavailable"
                
        # Test cameras
        for camera in self.cameras:
            available = self.is_entity_available(camera)
            state = self.get_entity_state(camera)
            results["details"]["cameras"].append({
                "entity_id": camera,
                "available": available,
                "state": state,
            })
            
        # Test recording entities
        for entity in self.recording_entities:
            available = self.is_entity_available(entity)
            state = self.get_entity_state(entity)
            results["details"]["recording_entities"].append({
                "entity_id": entity,
                "available": available,
                "current_mode": state,
            })
            
        # Test POE optimization
        poe_on = await self._check_poe_status()
        results["details"]["poe_optimization"] = {
            "currently_on": poe_on,
            "delay_saved": f"{self.poe_delay}s if already on",
        }
        
        return results
        
    async def _check_poe_status(self) -> bool:
        """Check if all POE switches are currently on.
        
        Returns:
            True if all switches are on, False otherwise
        """
        if not self.poe_switches:
            return False
            
        for switch in self.poe_switches:
            state = self.get_entity_state(switch)
            if state != "on":
                return False
                
        return True
