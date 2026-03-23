"""Camera module for Secure Me alarm system."""
# VERSION = "1.2.0"

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
        """Initialize camera module.

        Config options:
            - poe_switches: List of POE switch entity IDs
            - cameras: List of camera entity IDs for verification
            - recording_entities: List of recording mode select entities
            - poe_delay: Seconds to wait after POE on (30-300, default: 120)
            - auto_record: Enable 24/7 recording when armed (default: False)
        """
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
        """Turn on cameras when arming (with retry on POE switches)."""
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
        """Turn off cameras when disarming (with retry)."""
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
        """No action on trigger (cameras already recording)."""
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test camera module functionality.

        POE-aware test logic:
        - If POE switches are configured and ALL are off: skip camera test.
          Cameras are intentionally powered down and cannot be tested.
          This is not a failure.
        - If POE is on (or no POE switches configured): test cameras normally.
          Unavailable cameras are reported as failures.
        """
        poe_on = await self._check_poe_status()
        poe_configured = bool(self.poe_switches)

        results: dict[str, Any] = {
            "success": True,
            "message": "Camera module test passed",
            "details": {
                "poe_switches": [],
                "cameras": [],
                "recording_entities": [],
                "poe_status": {
                    "configured": poe_configured,
                    "on": poe_on,
                    "delay": f"{self.poe_delay}s",
                    "auto_record": self.auto_record,
                },
            },
        }

        # Always check POE switch availability
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

        # If POE is configured but off: cameras are intentionally powered down
        if poe_configured and not poe_on:
            results["message"] = "Camera test skipped — POE is off (cameras intentionally powered down)"
            results["details"]["skipped"] = True
            # Do not mark as failure — this is expected behaviour
            return results

        # POE is on (or no POE configured): test cameras
        for camera in self.cameras:
            available = self.is_entity_available(camera)
            results["details"]["cameras"].append({
                "entity_id": camera,
                "available": available,
                "state": self.get_entity_state(camera),
            })
            if not available:
                results["success"] = False
                results["message"] = f"Camera {camera} unavailable (POE is on)"

        for entity in self.recording_entities:
            results["details"]["recording_entities"].append({
                "entity_id": entity,
                "available": self.is_entity_available(entity),
                "current_mode": self.get_entity_state(entity),
            })

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
