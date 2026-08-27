"""Siren module for Secure Me alarm system."""
# VERSION = "1.5.5"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

DEFAULT_VOLUME = 100
DEFAULT_RINGTONE_ID = 0
DEFAULT_FLASH_DURATION = 300

# Domains supported as on/off siren triggers (no volume support)
ONOFF_DOMAINS = {"switch", "input_boolean"}


class SirenModule(AlarmModule):
    """Siren control module supporting native siren entities, switch/input_boolean-based sirens, and Xiaomi Gateway."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize siren module.

        Config options:
            - sirens: list of siren entries, each with:
                  entity_id: siren.*, switch.*, or input_boolean.* entity
                  pattern:   continuous / intermittent / rapid
                  duration:  seconds (default 300)
                  volume:    0-100 (default 80, ignored for switch/input_boolean)
            - gateway_mac: Xiaomi Gateway MAC address (legacy)
            - gateway_light: Gateway light entity ID (legacy)
            - flash_duration: Seconds to flash light (default: 300)
            - sound_on_trigger: Play sound when triggered (default: True)
            - light_on_trigger: Flash light when triggered (default: True)
        """
        super().__init__(hass, config)

        # Generic entity list (new style)
        self.sirens: list[dict[str, Any]] = config.get("sirens", [])

        # Xiaomi Gateway (legacy)
        self.gateway_mac = config.get("gateway_mac")
        self.gateway_light = config.get("gateway_light")
        self.volume = config.get("volume", DEFAULT_VOLUME)
        self.ringtone_id = config.get("ringtone_id", DEFAULT_RINGTONE_ID)
        self.flash_duration = config.get("flash_duration", DEFAULT_FLASH_DURATION)
        self.sound_on_trigger = config.get("sound_on_trigger", True)
        self.light_on_trigger = config.get("light_on_trigger", True)
        self._flash_task = None
        self._duration_tasks: list[asyncio.Task] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _domain(self, entity_id: str) -> str:
        """Return HA domain of an entity_id."""
        return entity_id.split(".")[0] if "." in entity_id else ""

    async def _turn_on_entity(self, entity_id: str, volume: int = 80) -> bool:
        """Turn on a siren, switch, or input_boolean entity.

        Returns True only if a supported domain action was actually attempted.
        An unsupported domain (misconfigured/renamed entity) now fires the
        module's degraded notification instead of only logging a warning --
        previously this failed completely silently, both during a real
        trigger and during the Test tab's functional test.
        """
        domain = self._domain(entity_id)
        if domain == "siren":
            return await self.async_call_service_with_retry(
                "siren", "turn_on",
                target={"entity_id": entity_id},
                service_data={"volume_level": volume / 100.0},
                action=f"siren_on_{entity_id}",
            )
        elif domain in ONOFF_DOMAINS:
            return await self.async_call_service_with_retry(
                "homeassistant", "turn_on",
                target={"entity_id": entity_id},
                action=f"onoff_siren_on_{entity_id}",
            )
        else:
            _LOGGER.warning("Siren module: unsupported domain '%s' for entity %s", domain, entity_id)
            self._on_failure(f"unsupported_domain:{entity_id}")
            return False

    async def _turn_off_entity(self, entity_id: str) -> bool:
        """Turn off a siren, switch, or input_boolean entity.

        Returns True only if a supported domain action was actually attempted.
        """
        domain = self._domain(entity_id)
        if domain == "siren":
            return await self.async_call_service_with_retry(
                "siren", "turn_off",
                target={"entity_id": entity_id},
                action=f"siren_off_{entity_id}",
            )
        elif domain in ONOFF_DOMAINS:
            return await self.async_call_service_with_retry(
                "homeassistant", "turn_off",
                target={"entity_id": entity_id},
                action=f"onoff_siren_off_{entity_id}",
            )
        else:
            _LOGGER.warning("Siren module: unsupported domain '%s' for entity %s", domain, entity_id)
            self._on_failure(f"unsupported_domain:{entity_id}")
            return False

    async def _auto_off_after(self, entity_id: str, duration: int) -> None:
        """Auto-turn-off entity after duration seconds."""
        try:
            await asyncio.sleep(duration)
            await self._turn_off_entity(entity_id)
            _LOGGER.info("Siren module: auto-off after %ds for %s", duration, entity_id)
        except asyncio.CancelledError:
            pass
        except Exception as err:
            _LOGGER.error("Siren auto-off failed for %s: %s", entity_id, err)

    def _cancel_duration_tasks(self) -> None:
        """Cancel all running auto-off tasks."""
        for task in self._duration_tasks:
            task.cancel()
        self._duration_tasks.clear()

    # ------------------------------------------------------------------
    # AlarmModule interface
    # ------------------------------------------------------------------

    async def async_arm(self, mode: str) -> bool:
        """No action when arming."""
        return True

    async def async_disarm(self) -> bool:
        """Stop all sirens when disarming."""
        if not self.enabled:
            return True

        self._cancel_duration_tasks()

        # Generic entities
        for entry in self.sirens:
            entity_id = entry.get("entity_id", "")
            if entity_id:
                await self._turn_off_entity(entity_id)

        # Legacy Xiaomi Gateway
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

        _LOGGER.info("Siren module: all sirens stopped")
        return True

    async def async_trigger(self) -> bool:
        """Activate all configured sirens when alarm triggers."""
        if not self.enabled:
            return True

        self._cancel_duration_tasks()

        # Generic entities (siren.*, switch.*, input_boolean.*)
        for entry in self.sirens:
            entity_id = entry.get("entity_id", "")
            if not entity_id:
                continue
            volume = int(entry.get("volume", 80))
            duration = int(entry.get("duration", 300))
            await self._turn_on_entity(entity_id, volume)
            task = asyncio.create_task(self._auto_off_after(entity_id, duration))
            self._duration_tasks.append(task)

        # Legacy Xiaomi Gateway
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

        _LOGGER.info("Siren module: alarm triggered (%d entity sirens, gateway=%s)",
                     len(self.sirens), bool(self.gateway_mac))
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test siren module — brief 2s activation of all entities."""
        results: dict[str, Any] = {
            "success": True,
            "message": "Siren module test passed",
            "details": {
                "gateway_mac": self.gateway_mac,
                "gateway_light": None,
                "entities_tested": [],
                "sound_test": False,
                "light_test": False,
            },
        }
        # Collected instead of overwriting results["message"] each time --
        # with more than one siren/gateway problem, only the LAST one used to
        # survive in the summary (details per-entity were always correct).
        messages: list[str] = []

        # Test generic entities
        for entry in self.sirens:
            entity_id = entry.get("entity_id", "")
            if not entity_id:
                continue
            available = self.is_entity_available(entity_id)
            entity_result = {
                "entity_id": entity_id,
                "domain": self._domain(entity_id),
                "available": available,
                "state": self.get_entity_state(entity_id),
                "test_fired": False,
            }
            if available:
                try:
                    turned_on = await self._turn_on_entity(entity_id, 50)
                    await asyncio.sleep(2)
                    turned_off = await self._turn_off_entity(entity_id)
                    entity_result["test_fired"] = bool(turned_on and turned_off)
                    if not entity_result["test_fired"]:
                        results["success"] = False
                        messages.append(f"Test failed for {entity_id} (unsupported domain or service call failed)")
                except Exception as err:
                    _LOGGER.error("Siren entity test failed for %s: %s", entity_id, err)
                    results["success"] = False
                    messages.append(f"Test failed for {entity_id}")
            else:
                results["success"] = False
                messages.append(f"Entity {entity_id} unavailable")
            results["details"]["entities_tested"].append(entity_result)

        # Legacy gateway light info
        if self.gateway_light:
            available = self.is_entity_available(self.gateway_light)
            results["details"]["gateway_light"] = {
                "entity_id": self.gateway_light,
                "available": available,
                "state": self.get_entity_state(self.gateway_light),
            }
            if not available:
                results["success"] = False
                messages.append(f"Gateway light {self.gateway_light} unavailable")

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
                messages.append("Siren sound test failed")

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

        if messages:
            results["message"] = "; ".join(messages)

        return results

    async def async_shutdown(self) -> None:
        """Cleanup on shutdown."""
        self._cancel_duration_tasks()
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
