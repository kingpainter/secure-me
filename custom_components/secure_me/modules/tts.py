"""TTS module for Secure Me alarm system."""
# VERSION = "1.2.0"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "da"
DEFAULT_VOLUME = 0.5


class TTSModule(AlarmModule):
    """TTS (Text-to-Speech) module for voice announcements."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize TTS module.

        Config options:
            - media_players: List of media player entity IDs
            - tts_service: TTS service (default: "tts.cloud_say")
            - language: Language code (default: "da")
            - volume: Volume level 0.0-1.0 (default: 0.5)
            - announce_arming: Announce when arming (default: True)
            - announce_countdown: Announce countdown (default: True)
            - announce_disarm: Announce when disarmed (default: True)
            - announce_trigger: Announce when triggered (default: True)
        """
        super().__init__(hass, config)

        self.media_players = config.get("media_players", [])
        self.tts_service = config.get("tts_service", "tts.cloud_say")
        self.language = config.get("language", DEFAULT_LANGUAGE)
        self.volume = config.get("volume", DEFAULT_VOLUME)
        self.announce_arming = config.get("announce_arming", True)
        self.announce_countdown = config.get("announce_countdown", True)
        self.announce_disarm = config.get("announce_disarm", True)
        self.announce_trigger = config.get("announce_trigger", True)
        self._countdown_task = None

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
        """Announce alarm trigger — with retry on volume + TTS calls."""
        if not self.enabled or not self.announce_trigger:
            return True
        await self._announce("ADVARSEL! Alarm udlost! ADVARSEL!", urgent=True)
        await asyncio.sleep(5)
        await self._announce("Alarm systemet er udlost. Politiet er underrettet.", urgent=True)
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test TTS module — check players and play brief announcement."""
        results: dict[str, Any] = {
            "success": True,
            "message": "TTS module test passed",
            "details": {
                "media_players": [],
                "tts_service": self.tts_service,
                "language": self.language,
                "test_announcement": False,
            },
        }

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

        if self.media_players:
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
        if not self.enabled or not self.announce_countdown:
            return
        if seconds in (30, 20, 10, 5, 4, 3, 2, 1):
            asyncio.create_task(self._announce(f"Alarm aktiveres om {seconds} sekunder."))

    async def _announce(
        self,
        message: str,
        urgent: bool = False,
        test_mode: bool = False,
    ) -> None:
        """Make a TTS announcement with retry on volume set + TTS call."""
        if not self.media_players:
            return

        volume = self.volume
        if urgent:
            volume = min(volume * 1.5, 1.0)
        elif test_mode:
            volume = volume * 0.5

        # Set volume on all players (with retry — important for reliability)
        for player in self.media_players:
            await self.async_call_service_with_retry(
                "media_player", "volume_set",
                service_data={"volume_level": volume},
                target={"entity_id": player},
                action=f"tts_volume:{player}",
            )

        await asyncio.sleep(0.5)

        # Make TTS announcement (with retry)
        service_domain, service_name = self.tts_service.split(".", 1)
        await self.async_call_service_with_retry(
            service_domain, service_name,
            service_data={
                "entity_id": self.media_players,
                "message": message,
                "cache": False,
            },
            action="tts_announce",
        )

        _LOGGER.debug("TTS announcement: %s", message)

    def _get_mode_name(self, mode: str) -> str:
        """Return Danish mode name."""
        return {"away": "ude", "home": "hjemme", "night": "nat", "vacation": "ferie"}.get(mode, mode)
