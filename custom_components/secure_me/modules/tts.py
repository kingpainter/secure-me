"""TTS module for Secure Me alarm system."""
# VERSION = "0.9.0"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "da"
DEFAULT_VOLUME = 0.5

# Service modes
SERVICE_MODE_TTS = "tts"        # Standard HA TTS (tts.cloud_say etc.)
SERVICE_MODE_CUSTOM = "custom"  # Custom service (house_voice.say etc.)


class TTSModule(AlarmModule):
    """TTS (Text-to-Speech) module for voice announcements.

    Supports two service modes:
      - tts mode:    Uses standard HA TTS services (tts.cloud_say, tts.google_say etc.)
                     Requires media_players. Sets volume before announcing.
      - custom mode: Uses any HA service (house_voice.say, script.announce etc.)
                     Does NOT require media_players or volume control.
                     Message is passed via the field defined by message_field (default: "message").
                     Extra static fields can be added via custom_service_data.

    Config examples:

      # Standard TTS (default)
      tts_service: "tts.cloud_say"
      media_players:
        - media_player.living_room
      volume: 0.7
      language: "da"

      # Custom service — house_voice.say
      service_mode: "custom"
      tts_service: "house_voice.say"
      message_field: "message"        # field name for the spoken text (default: "message")
      custom_service_data:            # optional extra fields sent with every call
        language: "da"
        volume: 80

      # Custom service — HA script
      service_mode: "custom"
      tts_service: "script.alarm_announce"
      message_field: "message"
    """

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize TTS module.

        Config options:
            - service_mode: "tts" (default) or "custom"
            - media_players: List of media player entity IDs (tts mode only)
            - tts_service: Service to call (default: "tts.cloud_say")
            - language: Language code (default: "da") — tts mode only
            - volume: Volume level 0.0-1.0 (default: 0.5) — tts mode only
            - message_field: Field name for message in custom mode (default: "message")
            - custom_service_data: Extra static fields for custom service calls
            - announce_arming: Announce when arming (default: True)
            - announce_countdown: Announce countdown (default: True)
            - announce_disarm: Announce when disarmed (default: True)
            - announce_trigger: Announce when triggered (default: True)
        """
        super().__init__(hass, config)

        self.service_mode = config.get("service_mode", SERVICE_MODE_TTS)
        self.media_players = config.get("media_players", [])
        self.tts_service = config.get("tts_service", "tts.cloud_say")
        self.language = config.get("language", DEFAULT_LANGUAGE)
        self.volume = config.get("volume", DEFAULT_VOLUME)
        self.message_field = config.get("message_field", "message")
        self.custom_service_data = config.get("custom_service_data", {})
        self.announce_arming = config.get("announce_arming", True)
        self.announce_countdown_enabled = config.get("announce_countdown", True)
        self.announce_disarm = config.get("announce_disarm", True)
        self.announce_trigger = config.get("announce_trigger", True)
        self._countdown_task = None

        _LOGGER.debug(
            "TTS module initialized: mode=%s service=%s",
            self.service_mode,
            self.tts_service,
        )

    @property
    def is_custom_mode(self) -> bool:
        """Return True if using custom service mode."""
        return self.service_mode == SERVICE_MODE_CUSTOM

    async def async_arm(self, mode: str) -> bool:
        """Announce when arming."""
        if not self.enabled or not self.announce_arming:
            return True
        mode_name = self._get_mode_name(mode)
        await self._announce(f"Alarm aktiveres i {mode_name} mode.")
        return True

    async def async_disarm(self) -> bool:
        """Stop countdown and announce disarm."""
        if not self.enabled:
            return True
        if self._countdown_task:
            self._countdown_task.cancel()
            self._countdown_task = None
        if self.announce_disarm:
            await self._announce("Alarm systemet er deaktiveret.")
        return True

    async def async_trigger(self) -> bool:
        """Announce alarm trigger."""
        if not self.enabled or not self.announce_trigger:
            return True
        await self._announce("ADVARSEL! Alarm udlost! ADVARSEL!", urgent=True)
        await asyncio.sleep(5)
        await self._announce("Alarm systemet er udlost. Politiet er underrettet.", urgent=True)
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test TTS module — verify service and play brief announcement."""
        results: dict[str, Any] = {
            "success": True,
            "message": "TTS module test passed",
            "details": {
                "service_mode": self.service_mode,
                "tts_service": self.tts_service,
                "language": self.language,
                "media_players": [],
                "test_announcement": False,
            },
        }

        if not self.is_custom_mode:
            # TTS mode: verify media players are available
            for player in self.media_players:
                state = self.hass.states.get(player)
                player_info = {
                    "entity_id": player,
                    "available": self.is_entity_available(player),
                    "state": state.state if state else None,
                    "volume": state.attributes.get("volume_level") if state else None,
                }
                if not player_info["available"]:
                    results["success"] = False
                    results["message"] = f"Media player {player} unavailable"
                results["details"]["media_players"].append(player_info)
        else:
            results["details"]["message_field"] = self.message_field
            results["details"]["custom_service_data"] = self.custom_service_data

        # Play test announcement regardless of mode
        try:
            await self._announce("Test besked fra alarm systemet.", test_mode=True)
            results["details"]["test_announcement"] = True
        except Exception as err:
            _LOGGER.error("TTS test announcement failed: %s", err)
            results["success"] = False
            results["message"] = "TTS announcement test failed"

        return results

    async def async_shutdown(self) -> None:
        """Cleanup on shutdown."""
        if self._countdown_task:
            self._countdown_task.cancel()
            self._countdown_task = None
        await super().async_shutdown()

    async def announce_countdown(self, seconds: int) -> None:
        """Announce countdown at key intervals (called by coordinator)."""
        if not self.enabled or not self.announce_countdown_enabled:
            return
        if seconds in (30, 20, 10, 5, 4, 3, 2, 1):
            asyncio.create_task(self._announce(f"Alarm aktiveres om {seconds} sekunder."))

    async def _announce(
        self,
        message: str,
        urgent: bool = False,
        test_mode: bool = False,
    ) -> None:
        """Make a TTS announcement.

        In TTS mode:    sets volume on media players, then calls tts service with entity_id.
        In custom mode: calls service directly with message field + custom_service_data.
                        No volume control — the custom service handles that itself.
        """
        service_domain, service_name = self.tts_service.split(".", 1)

        if self.is_custom_mode:
            await self._announce_custom(service_domain, service_name, message)
        else:
            await self._announce_tts(service_domain, service_name, message, urgent, test_mode)

        _LOGGER.debug("TTS announcement [%s]: %s", self.service_mode, message)

    async def _announce_tts(
        self,
        service_domain: str,
        service_name: str,
        message: str,
        urgent: bool,
        test_mode: bool,
    ) -> None:
        """Standard TTS mode — set volume then call TTS service."""
        if not self.media_players:
            _LOGGER.warning("TTS module: no media_players configured")
            return

        volume = self.volume
        if urgent:
            volume = min(volume * 1.5, 1.0)
        elif test_mode:
            volume = volume * 0.5

        # Set volume on all players (with retry)
        for player in self.media_players:
            await self.async_call_service_with_retry(
                "media_player", "volume_set",
                service_data={"volume_level": volume},
                target={"entity_id": player},
                action=f"tts_volume:{player}",
            )

        await asyncio.sleep(0.5)

        # Call TTS service with retry
        await self.async_call_service_with_retry(
            service_domain, service_name,
            service_data={
                "entity_id": self.media_players,
                "message": message,
                "cache": False,
            },
            action="tts_announce",
        )

    async def _announce_custom(
        self,
        service_domain: str,
        service_name: str,
        message: str,
    ) -> None:
        """Custom service mode — call service with message field + any extra data."""
        service_data = dict(self.custom_service_data)
        service_data[self.message_field] = message

        await self.async_call_service_with_retry(
            service_domain, service_name,
            service_data=service_data,
            action="tts_custom_announce",
        )

    def _get_mode_name(self, mode: str) -> str:
        """Return Danish mode name."""
        return {"away": "ude", "home": "hjemme", "night": "nat", "vacation": "ferie"}.get(mode, mode)
