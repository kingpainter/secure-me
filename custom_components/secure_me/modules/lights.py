"""Lights module for Secure Me alarm system."""
# VERSION = "1.4.2"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

EMERGENCY_BRIGHTNESS = 255
FLASH_DELAY_MS = 500


class LightsModule(AlarmModule):
    """Lights control module with backup/restore and emergency mode."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize lights module.

        Config options:
            - lights: List of light entity IDs to flash (red/blue)
            - steady_lights: List of light entity IDs to turn on white 100% (no flash)
            - turn_off_on_arm: Turn off lights when arming (default: True)
            - restore_on_disarm: Restore light states when disarming (default: True)
            - emergency_mode: Enable red/blue flashing on trigger (default: True)
            - flash_duration: Seconds to flash lights (default: 300)
        """
        super().__init__(hass, config)

        self.lights = config.get("lights", [])
        self.steady_lights = config.get("steady_lights", [])
        self.turn_off_on_arm = config.get("turn_off_on_arm", True)
        self.restore_on_disarm = config.get("restore_on_disarm", True)
        self.emergency_mode = config.get("emergency_mode", True)
        self.flash_duration = config.get("flash_duration", 300)
        self._flash_task = None

    async def async_arm(self, mode: str) -> bool:
        """Backup light states and optionally turn off when arming."""
        if not self.enabled:
            return True

        all_lights = self.lights + self.steady_lights
        for light in all_lights:
            self.backup_state(light)

        if self.turn_off_on_arm:
            if all_lights:
                await self.async_call_service_with_retry(
                    "light", "turn_off",
                    target={"entity_id": all_lights},
                    action="lights_off_on_arm",
                )
            _LOGGER.info("Lights module: Lights turned off, states backed up")
        else:
            _LOGGER.info("Lights module: Light states backed up")

        return True

    async def async_disarm(self) -> bool:
        """Stop emergency flashing and restore light states."""
        if not self.enabled:
            return True

        if self._flash_task:
            self._flash_task.cancel()
            self._flash_task = None

        all_lights = self.lights + self.steady_lights
        if self.restore_on_disarm:
            for light in all_lights:
                await self._restore_light_state(light)
            _LOGGER.info("Lights module: Light states restored")
        else:
            if all_lights:
                await self.async_call_service_with_retry(
                    "light", "turn_off",
                    target={"entity_id": all_lights},
                    action="lights_off_on_disarm",
                )
            _LOGGER.info("Lights module: Lights turned off")

        self.clear_backup()
        return True

    async def async_trigger(self) -> bool:
        """Turn on lights at max brightness and start emergency flashing."""
        if not self.enabled:
            return True

        # Steady white lights: turn on immediately at full white brightness
        if self.steady_lights:
            await self.async_call_service_with_retry(
                "light", "turn_on",
                service_data={
                    "brightness": EMERGENCY_BRIGHTNESS,
                    "rgb_color": [255, 255, 255],
                },
                target={"entity_id": self.steady_lights},
                action="steady_lights_on_trigger",
            )
            _LOGGER.info("Lights module: %d steady white light(s) activated", len(self.steady_lights))

        # Flash lights: initial full brightness then start flash loop
        if self.lights:
            await self.async_call_service_with_retry(
                "light", "turn_on",
                service_data={"brightness": EMERGENCY_BRIGHTNESS},
                target={"entity_id": self.lights},
                action="lights_on_trigger",
            )
            if self.emergency_mode:
                self._flash_task = asyncio.create_task(self._emergency_flash())

        _LOGGER.info("Lights module: Emergency mode activated")
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test lights module functionality."""
        results: dict[str, Any] = {
            "success": True,
            "message": "Lights module test passed",
            "details": {"lights": [], "backup_restore": False, "emergency_flash": False},
        }

        for light in self.lights:
            state = self.hass.states.get(light)
            light_info = {
                "entity_id": light,
                "available": self.is_entity_available(light),
                "state": state.state if state else None,
                "brightness": state.attributes.get("brightness") if state else None,
            }
            if not light_info["available"]:
                results["success"] = False
                results["message"] = f"Light {light} unavailable"
            results["details"]["lights"].append(light_info)

        # Backup/restore test
        test_light = self.lights[0] if self.lights else None
        if test_light and self.get_entity_state(test_light) == "on":
            self.backup_state(test_light)
            if self.get_backup_state(test_light):
                results["details"]["backup_restore"] = True
                self.clear_backup(test_light)

        # Brief flash test
        if self.lights:
            try:
                await self.async_call_service(
                    "light", "turn_on",
                    service_data={"brightness": EMERGENCY_BRIGHTNESS, "rgb_color": [255, 0, 0]},
                    target={"entity_id": self.lights[0]},
                )
                await asyncio.sleep(0.5)
                await self.async_call_service("light", "turn_off", target={"entity_id": self.lights[0]})
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
        """Restore a light to its backed up state."""
        backup = self.get_backup_state(light)
        if not backup:
            return

        if backup["state"] == "off":
            await self.async_call_service("light", "turn_off", target={"entity_id": light})
        else:
            attrs = backup.get("attributes", {})
            service_data: dict[str, Any] = {}
            for key in ("brightness", "rgb_color", "color_temp"):
                if key in attrs:
                    service_data[key] = attrs[key]
            # Pass service_data only if non-empty to avoid HA rejecting empty dict
            await self.async_call_service(
                "light", "turn_on",
                service_data=service_data if service_data else None,
                target={"entity_id": light},
            )

    async def _emergency_flash(self) -> None:
        """Flash lights red/blue for emergency (loops until cancelled)."""
        try:
            end_time = asyncio.get_event_loop().time() + self.flash_duration
            while asyncio.get_event_loop().time() < end_time:
                for color, label in (([255, 0, 0], "red"), ([0, 0, 255], "blue")):
                    await self.async_call_service(
                        "light", "turn_on",
                        service_data={"brightness": EMERGENCY_BRIGHTNESS, "rgb_color": color},
                        target={"entity_id": self.lights},
                    )
                    await asyncio.sleep(FLASH_DELAY_MS / 1000)
                    await self.async_call_service("light", "turn_off", target={"entity_id": self.lights})
                    await asyncio.sleep(FLASH_DELAY_MS / 1000)
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.error("Emergency flash failed: %s", err)
