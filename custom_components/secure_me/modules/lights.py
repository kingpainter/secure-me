"""Lights module for Secure Me alarm system."""
# VERSION = "0.3.3"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

# Emergency light settings
EMERGENCY_BRIGHTNESS = 255
FLASH_DELAY_MS = 500


class LightsModule(AlarmModule):
    """Lights control module with backup/restore and emergency mode."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize lights module.
        
        Config options:
            - lights: List of light entity IDs to control
            - turn_off_on_arm: Turn off lights when arming (default: True)
            - restore_on_disarm: Restore light states when disarming (default: True)
            - emergency_mode: Enable red/blue flashing on trigger (default: True)
            - flash_duration: Seconds to flash lights (default: 300)
        """
        super().__init__(hass, config)
        
        self.lights = config.get("lights", [])
        self.turn_off_on_arm = config.get("turn_off_on_arm", True)
        self.restore_on_disarm = config.get("restore_on_disarm", True)
        self.emergency_mode = config.get("emergency_mode", True)
        self.flash_duration = config.get("flash_duration", 300)
        
        self._flash_task = None
        
    async def async_arm(self, mode: str) -> bool:
        """Handle lights when arming.
        
        - Backup current states
        - Turn off lights (optional)
        """
        if not self.enabled:
            return True
            
        try:
            # Backup all light states
            for light in self.lights:
                self.backup_state(light)
                
            # Turn off lights if configured
            if self.turn_off_on_arm:
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.lights}
                )
                _LOGGER.info("Lights module: Lights turned off, states backed up")
            else:
                _LOGGER.info("Lights module: Light states backed up")
                
            return True
            
        except Exception as err:
            _LOGGER.error("Lights module arm failed: %s", err)
            return False
            
    async def async_disarm(self) -> bool:
        """Handle lights when disarming.
        
        - Stop emergency flashing (if active)
        - Restore backed up states (optional)
        """
        if not self.enabled:
            return True
            
        try:
            # Stop flashing if active
            if self._flash_task:
                self._flash_task.cancel()
                self._flash_task = None
                
            # Restore light states if configured
            if self.restore_on_disarm:
                for light in self.lights:
                    await self._restore_light_state(light)
                _LOGGER.info("Lights module: Light states restored")
            else:
                # Just turn off lights
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.lights}
                )
                _LOGGER.info("Lights module: Lights turned off")
                
            # Clear backup
            self.clear_backup()
            
            return True
            
        except Exception as err:
            _LOGGER.error("Lights module disarm failed: %s", err)
            return False
            
    async def async_trigger(self) -> bool:
        """Handle lights when alarm triggers.
        
        - Turn on all lights at max brightness
        - Start red/blue flashing (if enabled)
        """
        if not self.enabled:
            return True
            
        try:
            # Turn on all lights at max brightness
            await self.async_call_service(
                "light",
                "turn_on",
                service_data={"brightness": EMERGENCY_BRIGHTNESS},
                target={"entity_id": self.lights}
            )
            
            # Start emergency flashing if enabled
            if self.emergency_mode:
                self._flash_task = asyncio.create_task(
                    self._emergency_flash()
                )
                
            _LOGGER.info("Lights module: Emergency mode activated")
            return True
            
        except Exception as err:
            _LOGGER.error("Lights module trigger failed: %s", err)
            return False
            
    async def async_test(self) -> dict[str, Any]:
        """Test lights module functionality.
        
        Tests:
        - Light availability
        - Backup/restore capability
        - Emergency mode
        """
        results = {
            "success": True,
            "message": "Lights module test passed",
            "details": {
                "lights": [],
                "backup_restore": False,
                "emergency_flash": False,
            }
        }
        
        # Test each light
        for light in self.lights:
            light_info = {
                "entity_id": light,
                "available": False,
                "state": None,
                "brightness": None,
            }
            
            light_info["available"] = self.is_entity_available(light)
            state = self.hass.states.get(light)
            
            if state:
                light_info["state"] = state.state
                light_info["brightness"] = state.attributes.get("brightness")
                
            if not light_info["available"]:
                results["success"] = False
                results["message"] = f"Light {light} unavailable"
                
            results["details"]["lights"].append(light_info)
            
        # Test backup/restore (if lights are on)
        test_light = self.lights[0] if self.lights else None
        if test_light and self.get_entity_state(test_light) == "on":
            # Backup state
            self.backup_state(test_light)
            backup = self.get_backup_state(test_light)
            
            if backup:
                results["details"]["backup_restore"] = True
                self.clear_backup(test_light)
                
        # Test emergency flash (brief test)
        if self.lights:
            try:
                # Flash red once
                await self.async_call_service(
                    "light",
                    "turn_on",
                    service_data={
                        "brightness": EMERGENCY_BRIGHTNESS,
                        "rgb_color": [255, 0, 0]
                    },
                    target={"entity_id": self.lights[0]}
                )
                await asyncio.sleep(0.5)
                
                # Turn off
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.lights[0]}
                )
                
                results["details"]["emergency_flash"] = True
            except Exception:
                pass
                
        return results
        
    async def async_shutdown(self) -> None:
        """Cleanup on shutdown."""
        if self._flash_task:
            self._flash_task.cancel()
            self._flash_task = None
        await super().async_shutdown()
        
    async def _restore_light_state(self, light: str) -> None:
        """Restore a light to its backed up state.
        
        Args:
            light: Light entity ID
        """
        backup = self.get_backup_state(light)
        if not backup:
            return
            
        if backup["state"] == "off":
            await self.async_call_service(
                "light",
                "turn_off",
                target={"entity_id": light}
            )
        else:
            # Restore with attributes
            service_data = {}
            attrs = backup.get("attributes", {})
            
            if "brightness" in attrs:
                service_data["brightness"] = attrs["brightness"]
            if "rgb_color" in attrs:
                service_data["rgb_color"] = attrs["rgb_color"]
            if "color_temp" in attrs:
                service_data["color_temp"] = attrs["color_temp"]
                
            await self.async_call_service(
                "light",
                "turn_on",
                service_data=service_data if service_data else None,
                target={"entity_id": light}
            )
            
    async def _emergency_flash(self) -> None:
        """Flash lights red/blue for emergency mode.
        
        Flashes for configured duration or until cancelled.
        """
        try:
            end_time = asyncio.get_event_loop().time() + self.flash_duration
            
            while asyncio.get_event_loop().time() < end_time:
                # Flash red
                await self.async_call_service(
                    "light",
                    "turn_on",
                    service_data={
                        "brightness": EMERGENCY_BRIGHTNESS,
                        "rgb_color": [255, 0, 0]  # Red
                    },
                    target={"entity_id": self.lights}
                )
                await asyncio.sleep(FLASH_DELAY_MS / 1000)
                
                # Turn off
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.lights}
                )
                await asyncio.sleep(FLASH_DELAY_MS / 1000)
                
                # Flash blue
                await self.async_call_service(
                    "light",
                    "turn_on",
                    service_data={
                        "brightness": EMERGENCY_BRIGHTNESS,
                        "rgb_color": [0, 0, 255]  # Blue
                    },
                    target={"entity_id": self.lights}
                )
                await asyncio.sleep(FLASH_DELAY_MS / 1000)
                
                # Turn off
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.lights}
                )
                await asyncio.sleep(FLASH_DELAY_MS / 1000)
                
        except asyncio.CancelledError:
            # Flashing cancelled (normal on disarm)
            pass
        except Exception as err:
            _LOGGER.error("Emergency flash failed: %s", err)
