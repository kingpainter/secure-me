"""Climate module for Secure Me alarm system."""
# VERSION = "1.5.3"

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
        """Set climate to away mode when arming."""
        if not self.enabled or not self.away_mode:
            return True

        for climate in self.climates:
            self.backup_state(climate)
            state = self.hass.states.get(climate)
            if not state:
                continue

            preset_modes = state.attributes.get("preset_modes", [])
            if "away" in preset_modes:
                await self.async_call_service_with_retry(
                    "climate", "set_preset_mode",
                    service_data={"preset_mode": "away"},
                    target={"entity_id": climate},
                    action=f"climate_away:{climate}",
                )
            elif self.away_temperature:
                await self.async_call_service_with_retry(
                    "climate", "set_temperature",
                    service_data={"temperature": self.away_temperature},
                    target={"entity_id": climate},
                    action=f"climate_temp:{climate}",
                )

        _LOGGER.info("Climate module: Set to away mode")
        return True

    async def async_disarm(self) -> bool:
        """Restore climate settings when disarming."""
        if not self.enabled:
            return True

        if self.restore_on_disarm:
            for climate in self.climates:
                await self._restore_climate_state(climate)
            _LOGGER.info("Climate module: Settings restored")
        else:
            for climate in self.climates:
                state = self.hass.states.get(climate)
                if state and "home" in state.attributes.get("preset_modes", []):
                    await self.async_call_service_with_retry(
                        "climate", "set_preset_mode",
                        service_data={"preset_mode": "home"},
                        target={"entity_id": climate},
                        action=f"climate_home:{climate}",
                    )
            _LOGGER.info("Climate module: Set to home mode")

        self.clear_backup()
        return True

    async def async_trigger(self) -> bool:
        """No action on trigger (keep away mode)."""
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test climate module functionality."""
        results: dict[str, Any] = {
            "success": True,
            "message": "Climate module test passed",
            "details": {"climates": [], "total_zones": len(self.climates)},
        }
        # Collected instead of overwriting results["message"] each time --
        # with more than one climate zone, only the LAST issue used to survive
        # in the summary (details per-zone were always correct).
        messages: list[str] = []

        for climate in self.climates:
            state = self.hass.states.get(climate)
            climate_info: dict[str, Any] = {
                "entity_id": climate,
                "available": self.is_entity_available(climate),
                "current_temperature": state.attributes.get("current_temperature") if state else None,
                "target_temperature": state.attributes.get("temperature") if state else None,
                "preset_mode": state.attributes.get("preset_mode") if state else None,
                "preset_modes": state.attributes.get("preset_modes", []) if state else [],
                "hvac_mode": state.state if state else None,
            }

            if not climate_info["available"]:
                results["success"] = False
                messages.append(f"Climate {climate} unavailable")

            if "away" not in climate_info["preset_modes"] and not self.away_temperature:
                messages.append(f"Climate {climate} does not support away mode")

            results["details"]["climates"].append(climate_info)

        if messages:
            results["message"] = "; ".join(messages)

        return results

    async def _restore_climate_state(self, climate: str) -> None:
        """Restore a climate entity to its backed up state."""
        backup = self.get_backup_state(climate)
        if not backup:
            return

        attrs = backup.get("attributes", {})
        preset_mode = attrs.get("preset_mode")
        if preset_mode and preset_mode != "away":
            await self.async_call_service_with_retry(
                "climate", "set_preset_mode",
                service_data={"preset_mode": preset_mode},
                target={"entity_id": climate},
                action=f"climate_restore_preset:{climate}",
            )
        elif attrs.get("temperature"):
            await self.async_call_service_with_retry(
                "climate", "set_temperature",
                service_data={"temperature": attrs["temperature"]},
                target={"entity_id": climate},
                action=f"climate_restore_temp:{climate}",
            )
