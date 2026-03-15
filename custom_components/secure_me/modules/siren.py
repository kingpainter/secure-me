"""Siren module for Secure Me alarm system."""
# VERSION = "1.1.0"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

DEFAULT_VOLUME = 100
DEFAULT_RINGTONE_ID = 0
DEFAULT_FLASH_DURATION = 300


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
        """No action when arming."""
        return True

    async def async_disarm(self) -> bool:
        """Stop siren and light when disarming."""
        if not self.enabled:
            return True

        if self.gateway_mac:
            await self.async_call_service_with_retry(
                "xiaomi_aqara", "stop_ringtone",
                service_data={"gw_mac": self.gateway_mac},
                action="siren_stop",
            )

        if self._flash_task:
            self._flash_task.cancel()
            self._flash_task = None

        if self.gateway_light:
            await self.async_call_service_with_retry(
                "light", "turn_off",
                target={"entity_id": self.gateway_light},
                action="siren_light_off",
            )

        _LOGGER.info("Siren module: Siren stopped")
        return True

    async def async_trigger(self) -> bool:
        """Activate siren and flash light when alarm triggers."""
        if not self.enabled:
            return True

        if self.sound_on_trigger and self.gateway_mac:
            await self.async_call_service_with_retry(
                "xiaomi_aqara", "play_ringtone",
                service_data={
                    "gw_mac": self.gateway_mac,
                    "ringtone_id": self.ringtone_id,
                    "ringtone_vol": self.volume,
                },
                action="siren_play",
            )

        if self.light_on_trigger and self.gateway_light:
            self._flash_task = asyncio.create_task(self._flash_gateway_light())

        _LOGGER.info("Siren module: Alarm activated (sound=%s, light=%s)",
                     self.sound_on_trigger, self.light_on_trigger)
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test siren module — brief 2s sound + light flash."""
        results: dict[str, Any] = {
            "success": True,
            "message": "Siren module test passed",
            "details": {
                "gateway_mac": self.gateway_mac,
                "gateway_light": None,
                "sound_test": False,
                "light_test": False,
            },
        }

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

        if self.gateway_mac:
            try:
                await self.async_call_service(
                    "xiaomi_aqara", "play_ringtone",
                    service_data={"gw_mac": self.gateway_mac, "ringtone_id": self.ringtone_id, "ringtone_vol": 30},
                )
                await asyncio.sleep(2)
                await self.async_call_service(
                    "xiaomi_aqara", "stop_ringtone",
                    service_data={"gw_mac": self.gateway_mac},
                )
                results["details"]["sound_test"] = True
            except Exception as err:
                _LOGGER.error("Siren sound test failed: %s", err)
                results["success"] = False
                results["message"] = "Siren sound test failed"

        if self.gateway_light:
            try:
                for color in ([255, 0, 0], [0, 0, 255]):
                    await self.async_call_service(
                        "light", "turn_on",
                        service_data={"brightness": 255, "rgb_color": color},
                        target={"entity_id": self.gateway_light},
                    )
                    await asyncio.sleep(1)
                await self.async_call_service("light", "turn_off", target={"entity_id": self.gateway_light})
                results["details"]["light_test"] = True
            except Exception as err:
                _LOGGER.error("Siren light test failed: %s", err)

        return results

    async def async_shutdown(self) -> None:
        """Cleanup on shutdown."""
        if self._flash_task:
            self._flash_task.cancel()
            self._flash_task = None
        if self.gateway_mac:
            try:
                await self.hass.services.async_call(
                    "xiaomi_aqara", "stop_ringtone",
                    service_data={"gw_mac": self.gateway_mac},
                    blocking=False,
                )
            except Exception:
                pass
        await super().async_shutdown()

    async def _flash_gateway_light(self) -> None:
        """Flash gateway light red/blue for alarm (loops until cancelled)."""
        if not self.gateway_light:
            return
        try:
            end_time = asyncio.get_event_loop().time() + self.flash_duration
            while asyncio.get_event_loop().time() < end_time:
                for color in ([255, 0, 0], [0, 0, 255]):
                    await self.async_call_service(
                        "light", "turn_on",
                        service_data={"brightness": 255, "rgb_color": color},
                        target={"entity_id": self.gateway_light},
                    )
                    await asyncio.sleep(0.5)
                    await self.async_call_service("light", "turn_off", target={"entity_id": self.gateway_light})
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.error("Gateway light flash failed: %s", err)
