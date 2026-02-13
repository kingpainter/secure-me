"""Siren module for Secure Me alarm system."""
# VERSION = "0.3.0"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

# Default settings
DEFAULT_VOLUME = 100
DEFAULT_RINGTONE_ID = 0  # Police siren
DEFAULT_FLASH_DURATION = 300  # 5 minutes


class SirenModule(AlarmModule):
    """Siren control module for Xiaomi Gateway."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize siren module.
        
        Config options:
            - gateway_mac: Xiaomi Gateway MAC address
            - gateway_light: Gateway light entity ID
            - volume: Siren volume 0-100 (default: 100)
            - ringtone_id: Ringtone ID (default: 0 = police)
            - flash_duration: Seconds to flash light (default: 300)
            - sound_on_trigger: Play sound when triggered (default: True)
            - light_on_trigger: Flash light when triggered (default: True)
        """
        super().__init__(hass, config)
        
        self.gateway_mac = config.get("gateway_mac")
        self.gateway_light = config.get("gateway_light")
        self.volume = config.get("volume", DEFAULT_VOLUME)
        self.ringtone_id = config.get("ringtone_id", DEFAULT_RINGTONE_ID)
        self.flash_duration = config.get("flash_duration", DEFAULT_FLASH_DURATION)
        self.sound_on_trigger = config.get("sound_on_trigger", True)
        self.light_on_trigger = config.get("light_on_trigger", True)
        
        self._flash_task = None
        
    async def async_arm(self, mode: str) -> bool:
        """No action needed when arming."""
        return True
        
    async def async_disarm(self) -> bool:
        """Stop siren when disarming.
        
        - Stop sound
        - Stop light flashing
        """
        if not self.enabled:
            return True
            
        try:
            # Stop ringtone
            if self.gateway_mac:
                await self.hass.services.async_call(
                    "xiaomi_aqara",
                    "stop_ringtone",
                    service_data={"gw_mac": self.gateway_mac},
                    blocking=True,
                )
                
            # Stop light flashing
            if self._flash_task:
                self._flash_task.cancel()
                self._flash_task = None
                
            # Turn off gateway light
            if self.gateway_light:
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.gateway_light}
                )
                
            _LOGGER.info("Siren module: Siren stopped")
            return True
            
        except Exception as err:
            _LOGGER.error("Siren module disarm failed: %s", err)
            return False
            
    async def async_trigger(self) -> bool:
        """Activate siren when alarm triggers.
        
        - Play alarm sound
        - Flash gateway light red/blue
        """
        if not self.enabled:
            return True
            
        try:
            # Play ringtone
            if self.sound_on_trigger and self.gateway_mac:
                await self.hass.services.async_call(
                    "xiaomi_aqara",
                    "play_ringtone",
                    service_data={
                        "gw_mac": self.gateway_mac,
                        "ringtone_id": self.ringtone_id,
                        "ringtone_vol": self.volume,
                    },
                    blocking=True,
                )
                
            # Start light flashing
            if self.light_on_trigger and self.gateway_light:
                self._flash_task = asyncio.create_task(
                    self._flash_gateway_light()
                )
                
            _LOGGER.info("Siren module: Alarm activated (sound: %s, light: %s)",
                        self.sound_on_trigger, self.light_on_trigger)
            return True
            
        except Exception as err:
            _LOGGER.error("Siren module trigger failed: %s", err)
            return False
            
    async def async_test(self) -> dict[str, Any]:
        """Test siren module functionality.
        
        Tests:
        - Gateway availability
        - Light availability
        - Brief sound test (2 seconds)
        - Brief light test
        """
        results = {
            "success": True,
            "message": "Siren module test passed",
            "details": {
                "gateway_mac": self.gateway_mac,
                "gateway_light": None,
                "sound_test": False,
                "light_test": False,
            }
        }
        
        # Test gateway light
        if self.gateway_light:
            available = self.is_entity_available(self.gateway_light)
            results["details"]["gateway_light"] = {
                "entity_id": self.gateway_light,
                "available": available,
                "state": self.get_entity_state(self.gateway_light),
            }
            
            if not available:
                results["success"] = False
                results["message"] = f"Gateway light {self.gateway_light} unavailable"
                
        # Test sound (brief 2 second beep at low volume)
        if self.gateway_mac:
            try:
                await self.hass.services.async_call(
                    "xiaomi_aqara",
                    "play_ringtone",
                    service_data={
                        "gw_mac": self.gateway_mac,
                        "ringtone_id": self.ringtone_id,
                        "ringtone_vol": 30,  # Low volume for test
                    },
                    blocking=True,
                )
                await asyncio.sleep(2)
                await self.hass.services.async_call(
                    "xiaomi_aqara",
                    "stop_ringtone",
                    service_data={"gw_mac": self.gateway_mac},
                    blocking=True,
                )
                results["details"]["sound_test"] = True
            except Exception as err:
                _LOGGER.error("Siren sound test failed: %s", err)
                results["success"] = False
                results["message"] = "Siren sound test failed"
                
        # Test light (brief red/blue flash)
        if self.gateway_light:
            try:
                # Flash red
                await self.async_call_service(
                    "light",
                    "turn_on",
                    service_data={
                        "brightness": 255,
                        "rgb_color": [255, 0, 0]
                    },
                    target={"entity_id": self.gateway_light}
                )
                await asyncio.sleep(1)
                
                # Flash blue
                await self.async_call_service(
                    "light",
                    "turn_on",
                    service_data={
                        "brightness": 255,
                        "rgb_color": [0, 0, 255]
                    },
                    target={"entity_id": self.gateway_light}
                )
                await asyncio.sleep(1)
                
                # Turn off
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.gateway_light}
                )
                
                results["details"]["light_test"] = True
            except Exception as err:
                _LOGGER.error("Siren light test failed: %s", err)
                
        return results
        
    async def async_shutdown(self) -> None:
        """Cleanup on shutdown."""
        if self._flash_task:
            self._flash_task.cancel()
            self._flash_task = None
            
        # Stop ringtone if playing
        if self.gateway_mac:
            try:
                await self.hass.services.async_call(
                    "xiaomi_aqara",
                    "stop_ringtone",
                    service_data={"gw_mac": self.gateway_mac},
                    blocking=False,
                )
            except Exception:
                pass
                
        await super().async_shutdown()
        
    async def _flash_gateway_light(self) -> None:
        """Flash gateway light red/blue for alarm.
        
        Flashes for configured duration or until cancelled.
        """
        if not self.gateway_light:
            return
            
        try:
            end_time = asyncio.get_event_loop().time() + self.flash_duration
            
            while asyncio.get_event_loop().time() < end_time:
                # Flash red
                await self.async_call_service(
                    "light",
                    "turn_on",
                    service_data={
                        "brightness": 255,
                        "rgb_color": [255, 0, 0]  # Red
                    },
                    target={"entity_id": self.gateway_light}
                )
                await asyncio.sleep(0.5)
                
                # Turn off
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.gateway_light}
                )
                await asyncio.sleep(0.5)
                
                # Flash blue
                await self.async_call_service(
                    "light",
                    "turn_on",
                    service_data={
                        "brightness": 255,
                        "rgb_color": [0, 0, 255]  # Blue
                    },
                    target={"entity_id": self.gateway_light}
                )
                await asyncio.sleep(0.5)
                
                # Turn off
                await self.async_call_service(
                    "light",
                    "turn_off",
                    target={"entity_id": self.gateway_light}
                )
                await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            # Flashing cancelled (normal on disarm)
            pass
        except Exception as err:
            _LOGGER.error("Gateway light flash failed: %s", err)
