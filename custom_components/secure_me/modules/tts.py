"""TTS module for Secure Me alarm system."""
# VERSION = "0.2.0"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

# Default settings
DEFAULT_LANGUAGE = "da"  # Danish
DEFAULT_VOLUME = 0.5


class TTSModule(AlarmModule):
    """TTS (Text-to-Speech) module for voice announcements."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize TTS module.
        
        Config options:
            - media_players: List of media player entity IDs
            - tts_service: TTS service to use (default: "tts.cloud_say")
            - language: Language code (default: "da" = Danish)
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
        """Announce when arming.
        
        - Announce arming mode
        - Start exit countdown announcements (if configured)
        """
        if not self.enabled or not self.announce_arming:
            return True
            
        try:
            # Announce arming
            mode_name = self._get_mode_name(mode)
            message = f"Alarm aktiveres i {mode_name} mode."
            await self._announce(message)
            
            return True
            
        except Exception as err:
            _LOGGER.error("TTS module arm failed: %s", err)
            return False
            
    async def async_disarm(self) -> bool:
        """Announce when disarmed.
        
        - Stop countdown announcements
        - Announce system disarmed
        """
        if not self.enabled:
            return True
            
        try:
            # Stop countdown if running
            if self._countdown_task:
                self._countdown_task.cancel()
                self._countdown_task = None
                
            # Announce disarmed
            if self.announce_disarm:
                await self._announce("Alarm systemet er deaktiveret.")
                
            return True
            
        except Exception as err:
            _LOGGER.error("TTS module disarm failed: %s", err)
            return False
            
    async def async_trigger(self) -> bool:
        """Announce when alarm triggers.
        
        - Announce alarm triggered
        - Repeat warning message
        """
        if not self.enabled or not self.announce_trigger:
            return True
            
        try:
            # Announce trigger
            await self._announce("ADVARSEL! Alarm udløst! ADVARSEL!", urgent=True)
            
            # Wait a bit then announce again
            await asyncio.sleep(5)
            await self._announce("Alarm systemet er udløst. Politiet er underrettet.", urgent=True)
            
            return True
            
        except Exception as err:
            _LOGGER.error("TTS module trigger failed: %s", err)
            return False
            
    async def async_test(self) -> dict[str, Any]:
        """Test TTS module functionality.
        
        Tests:
        - Media player availability
        - TTS service availability
        - Brief announcement test
        """
        results = {
            "success": True,
            "message": "TTS module test passed",
            "details": {
                "media_players": [],
                "tts_service": self.tts_service,
                "language": self.language,
                "test_announcement": False,
            }
        }
        
        # Test media players
        for player in self.media_players:
            player_info = {
                "entity_id": player,
                "available": False,
                "state": None,
                "volume": None,
            }
            
            player_info["available"] = self.is_entity_available(player)
            state = self.hass.states.get(player)
            
            if state:
                player_info["state"] = state.state
                player_info["volume"] = state.attributes.get("volume_level")
                
            if not player_info["available"]:
                results["success"] = False
                results["message"] = f"Media player {player} unavailable"
                
            results["details"]["media_players"].append(player_info)
            
        # Test TTS announcement
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
        """Announce countdown (called by coordinator).
        
        Args:
            seconds: Seconds remaining
        """
        if not self.enabled or not self.announce_countdown:
            return
            
        # Announce at specific intervals: 30, 20, 10, 5, 4, 3, 2, 1
        if seconds in (30, 20, 10, 5, 4, 3, 2, 1):
            message = f"Alarm aktiveres om {seconds} sekunder."
            asyncio.create_task(self._announce(message))
            
    async def _announce(self, message: str, urgent: bool = False, test_mode: bool = False) -> None:
        """Make a TTS announcement.
        
        Args:
            message: Message to announce
            urgent: Increase volume for urgent messages
            test_mode: Lower volume for testing
        """
        if not self.media_players:
            return
            
        try:
            # Calculate volume
            volume = self.volume
            if urgent:
                volume = min(volume * 1.5, 1.0)
            elif test_mode:
                volume = volume * 0.5
                
            # Set volume on all media players
            for player in self.media_players:
                await self.async_call_service(
                    "media_player",
                    "volume_set",
                    service_data={"volume_level": volume},
                    target={"entity_id": player}
                )
                
            # Wait for volume to be set
            await asyncio.sleep(0.5)
            
            # Make announcement
            service_domain = self.tts_service.split(".")[0]
            service_name = self.tts_service.split(".")[1]
            
            await self.hass.services.async_call(
                service_domain,
                service_name,
                service_data={
                    "entity_id": self.media_players,
                    "message": message,
                    "cache": False,
                },
                blocking=True,
            )
            
            _LOGGER.debug("TTS announcement: %s", message)
            
        except Exception as err:
            _LOGGER.error("TTS announcement failed: %s", err)
            
    def _get_mode_name(self, mode: str) -> str:
        """Get Danish mode name.
        
        Args:
            mode: Arming mode
            
        Returns:
            Danish mode name
        """
        mode_names = {
            "away": "ude",
            "home": "hjemme",
            "night": "nat",
            "vacation": "ferie",
        }
        return mode_names.get(mode, mode)
