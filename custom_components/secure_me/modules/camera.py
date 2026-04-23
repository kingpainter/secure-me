"""Camera module for Secure Me alarm system."""
# VERSION = "1.4.2"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

# POE delay configuration (seconds)
DEFAULT_POE_DELAY = 120
MIN_POE_DELAY = 30
MAX_POE_DELAY = 300


class CameraModule(AlarmModule):
    """Camera control module with POE optimization and retry logic."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        self.poe_switches = config.get("poe_switches", [])
        self.cameras = config.get("cameras", [])
        self.recording_entities = config.get("recording_entities", [])
        self.poe_delay = self._validate_poe_delay(config.get("poe_delay", DEFAULT_POE_DELAY))
        self.auto_record = config.get("auto_record", False)
        self._poe_was_on = False

        _LOGGER.info(
            "Camera module initialized: %d POE switches, %d cameras, delay=%ds",
            len(self.poe_switches), len(self.cameras), self.poe_delay,
        )

    async def async_arm(self, mode: str) -> bool:
        if not self.enabled:
            return True

        self._poe_was_on = await self._check_poe_status()

        if self._poe_was_on:
            _LOGGER.info("Camera module: POE already ON - skipping %ds delay", self.poe_delay)
        else:
            _LOGGER.info("Camera module: POE OFF - turning on, waiting %ds", self.poe_delay)
            for switch in self.poe_switches:
                await self.async_call_service_with_retry(
                    "switch", "turn_on",
                    target={"entity_id": switch},
                    action=f"poe_on:{switch}",
                )
            await asyncio.sleep(self.poe_delay)
            _LOGGER.info("Camera module: initialization complete")

        if self.auto_record and self.recording_entities:
            for entity in self.recording_entities:
                await self.async_call_service_with_retry(
                    "select", "select_option",
                    service_data={"option": "always"},
                    target={"entity_id": entity},
                    action=f"recording_on:{entity}",
                )

        _LOGGER.info("Camera module: Cameras activated")
        return True

    async def async_disarm(self) -> bool:
        if not self.enabled:
            return True

        if self.recording_entities:
            for entity in self.recording_entities:
                await self.async_call_service_with_retry(
                    "select", "select_option",
                    service_data={"option": "never"},
                    target={"entity_id": entity},
                    action=f"recording_off:{entity}",
                )

        await asyncio.sleep(15)

        for switch in self.poe_switches:
            await self.async_call_service_with_retry(
                "switch", "turn_off",
                target={"entity_id": switch},
                action=f"poe_off:{switch}",
            )

        _LOGGER.info("Camera module: Cameras deactivated")
        return True

    async def async_trigger(self) -> bool:
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test camera module with smart POE handling.

        Logic (from v3.0.3 alarm test):
        1. Check if POE is already ON (save initial state)
        2. POE already ON  -> test cameras immediately (no wait, saves poe_delay seconds)
        3. POE is OFF      -> turn on POE, wait poe_delay seconds,
                             test cameras, then restore POE to OFF
        4. Camera unavailable after POE on -> FAIL
        5. No POE switches -> test cameras directly
        """
        poe_configured = bool(self.poe_switches)
        poe_initially_on = await self._check_poe_status()

        results: dict[str, Any] = {
            "success": True,
            "message": "Camera module test passed",
            "details": {
                "poe_switches": [],
                "cameras": [],
                "recording_entities": [],
                "poe_status": {
                    "configured": poe_configured,
                    "initially_on": poe_initially_on,
                    "delay": f"{self.poe_delay}s",
                    "auto_record": self.auto_record,
                },
            },
        }

        # Always check POE switch availability first
        for switch in self.poe_switches:
            available = self.is_entity_available(switch)
            results["details"]["poe_switches"].append({
                "entity_id": switch,
                "available": available,
                "state": self.get_entity_state(switch),
            })
            if not available:
                results["success"] = False
                results["message"] = f"POE switch {switch} unavailable"
                return results

        # POE is OFF: turn on, wait for cameras to boot, then test
        if poe_configured and not poe_initially_on:
            _LOGGER.info(
                "Camera test: POE is OFF — turning on and waiting %ds for cameras to boot",
                self.poe_delay,
            )
            results["details"]["poe_status"]["powered_on_for_test"] = True

            for switch in self.poe_switches:
                await self.async_call_service_with_retry(
                    "switch", "turn_on",
                    target={"entity_id": switch},
                    action=f"test_poe_on:{switch}",
                )

            await asyncio.sleep(self.poe_delay)

        elif poe_configured and poe_initially_on:
            # POE already on — test immediately, save poe_delay seconds
            _LOGGER.info("Camera test: POE already ON — testing feeds immediately (no wait)")
            results["details"]["poe_status"]["powered_on_for_test"] = False
            await asyncio.sleep(2)

        # Test cameras (POE is now on, or no POE configured)
        for camera in self.cameras:
            available = self.is_entity_available(camera)
            results["details"]["cameras"].append({
                "entity_id": camera,
                "available": available,
                "state": self.get_entity_state(camera),
            })
            if not available:
                results["success"] = False
                results["message"] = f"Camera {camera} unavailable after POE on"

        for entity in self.recording_entities:
            results["details"]["recording_entities"].append({
                "entity_id": entity,
                "available": self.is_entity_available(entity),
                "current_mode": self.get_entity_state(entity),
            })

        # Restore POE to OFF if it was off before the test
        if poe_configured and not poe_initially_on:
            _LOGGER.info("Camera test: restoring POE to OFF (initial state)")
            for switch in self.poe_switches:
                await self.async_call_service(
                    "switch", "turn_off",
                    target={"entity_id": switch},
                )

        return results

    async def _check_poe_status(self) -> bool:
        """Return True if all POE switches are on."""
        if not self.poe_switches:
            return False
        return all(self.get_entity_state(s) == "on" for s in self.poe_switches)

    def _validate_poe_delay(self, delay: int) -> int:
        """Clamp POE delay to acceptable range."""
        if delay < MIN_POE_DELAY:
            _LOGGER.warning("POE delay %ds too short, using minimum %ds", delay, MIN_POE_DELAY)
            return MIN_POE_DELAY
        if delay > MAX_POE_DELAY:
            _LOGGER.warning("POE delay %ds too long, using maximum %ds", delay, MAX_POE_DELAY)
            return MAX_POE_DELAY
        return delay
