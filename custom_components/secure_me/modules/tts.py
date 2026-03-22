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

# Message types supported by custom messages
MSG_TYPE_TTS = "tts"        # Text-to-speech via tts service
MSG_TYPE_MEDIA = "media"    # Play a media file (MP3/URL)

# Alarm states that can trigger a custom message
VALID_TRIGGERS = {
    "armed_away", "armed_home", "armed_night", "armed_vacation",
    "disarmed", "triggered", "arming", "pending",
}


class TTSModule(AlarmModule):
    """TTS module for custom voice and media announcements.

    Responsibility: Play user-defined custom messages on alarm state changes.
    System status messages (armed/disarmed/triggered/countdown) are handled
    by notification_dispatcher.py — not this module.

    Supports two message types:
    - tts: Text-to-speech via a tts.* service + media_player entities
    - media: Play an MP3/URL via media_player.play_media (no TTS service needed)

    media_players is optional when using a custom TTS service that handles
    routing internally (e.g. a script or automation).
    """

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize TTS module.

        Config options:
            - media_players: List of media player entity IDs (optional)
            - tts_service: TTS service to use (default: "tts.cloud_say")
            - language: Language code (default: "da")
            - volume: Volume level 0.0-1.0 (default: 0.5)
            - custom_messages: List of custom message configs (see below)

        Custom message config:
            {
              "id": "msg_001",           # unique id
              "name": "Politiet tilkaldt",
              "type": "tts",             # "tts" or "media"
              "trigger": "triggered",    # alarm state that fires this
              "message": "Politiet er tilkaldt og video er sendt.",  # for tts
              "media_url": "",           # for media type: URL or local path
              "media_content_type": "music",  # for media type
              "enabled": True,
            }
        """
        super().__init__(hass, config)

        self.media_players: list[str] = config.get("media_players", [])
        self.tts_service: str = config.get("tts_service", "tts.cloud_say")
        self.language: str = config.get("language", DEFAULT_LANGUAGE)
        self.volume: float = float(config.get("volume", DEFAULT_VOLUME))
        self.custom_messages: list[dict[str, Any]] = config.get("custom_messages", [])
        self._warned_incompatible_service: bool = False  # warn only once per session

    # ── AlarmModule interface ────────────────────────────────────────────────

    async def async_arm(self, mode: str) -> bool:
        """Fire custom messages for the specific arm mode."""
        if not self.enabled:
            return True
        trigger = f"armed_{mode}" if mode in ("away", "home", "night", "vacation") else mode
        await self._fire_custom_messages(trigger)
        return True

    async def async_disarm(self) -> bool:
        """Fire custom messages for disarmed state."""
        if not self.enabled:
            return True
        await self._fire_custom_messages("disarmed")
        return True

    async def async_trigger(self) -> bool:
        """Fire custom messages for triggered state."""
        if not self.enabled:
            return True
        await self._fire_custom_messages("triggered")
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test TTS module — check players and play first enabled custom message."""
        results: dict[str, Any] = {
            "success": True,
            "message": "TTS module test passed",
            "details": {
                "media_players": [],
                "tts_service": self.tts_service,
                "language": self.language,
                "custom_messages": len(self.custom_messages),
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

        # Play first enabled custom message as test
        test_msg = next(
            (m for m in self.custom_messages if m.get("enabled", True)),
            None,
        )
        if test_msg:
            try:
                await self._play_message(test_msg, test_mode=True)
                results["details"]["test_announcement"] = True
            except Exception as err:
                _LOGGER.error("TTS test announcement failed: %s", err)
                results["success"] = False
                results["message"] = "TTS announcement test failed"
        elif not self.media_players and not self.custom_messages:
            results["message"] = "TTS module enabled but no messages or players configured"

        return results

    # ── Public helpers (called by notification_dispatcher for system TTS) ────

    async def announce_system(self, message: str, urgent: bool = False) -> None:
        """Play a system status message via TTS.

        Called by notification_dispatcher when a notification is configured
        with channel="tts". Uses the module's configured service + players.
        """
        if not self.enabled or not self.media_players:
            return
        await self._announce_tts(message, urgent=urgent)

    # ── Internal ─────────────────────────────────────────────────────────────

    async def _fire_custom_messages(self, trigger: str) -> None:
        """Fire all enabled custom messages matching the given trigger."""
        for msg in self.custom_messages:
            if not msg.get("enabled", True):
                continue
            if msg.get("trigger") != trigger:
                continue
            try:
                await self._play_message(msg)
            except Exception as err:
                _LOGGER.error(
                    "TTS custom message '%s' failed: %s", msg.get("name", "?"), err
                )

    async def _play_message(self, msg: dict[str, Any], test_mode: bool = False) -> None:
        """Play a single custom message (TTS or media file)."""
        msg_type = msg.get("type", MSG_TYPE_TTS)

        if msg_type == MSG_TYPE_MEDIA:
            await self._play_media(msg, test_mode=test_mode)
        else:
            text = msg.get("message", "")
            if text:
                await self._announce_tts(text, test_mode=test_mode)

    async def _announce_tts(
        self,
        message: str,
        urgent: bool = False,
        test_mode: bool = False,
    ) -> None:
        """Make a TTS announcement via tts service + media players."""
        if not self.media_players:
            _LOGGER.debug("TTS: no media_players configured, skipping announcement")
            return

        volume = self.volume
        if urgent:
            volume = min(volume * 1.5, 1.0)
        elif test_mode:
            volume = volume * 0.5

        # Set volume on all players
        for player in self.media_players:
            await self.async_call_service_with_retry(
                "media_player", "volume_set",
                service_data={"volume_level": volume},
                target={"entity_id": player},
                action=f"tts_volume:{player}",
            )

        await asyncio.sleep(0.5)

        # Make TTS announcement
        try:
            service_domain, service_name = self.tts_service.split(".", 1)
        except ValueError:
            _LOGGER.error("Invalid TTS service '%s'", self.tts_service)
            return

        # Standard HA TTS services (tts.*) use target + message/language/cache.
        # Custom services (e.g. house_voice.say, notify.*) have their own schema
        # and should only receive the message field without target or HA-specific keys.
        if service_domain == "tts":
            await self.async_call_service_with_retry(
                service_domain, service_name,
                service_data={
                    "message": message,
                    "language": self.language,
                    "cache": False,
                },
                target={"entity_id": self.media_players},
                action="tts_announce",
            )
        elif service_domain == "notify":
            # notify.* services use message field directly
            await self.async_call_service_with_retry(
                service_domain, service_name,
                service_data={"message": message, "title": "Secure Me"},
                action="tts_announce",
            )
        else:
            # Unknown custom service (e.g. house_voice.say) — these have
            # their own schema and cannot accept free-form text.
            # Warn only once per session to avoid log spam.
            if not self._warned_incompatible_service:
                self._warned_incompatible_service = True
                _LOGGER.warning(
                    "TTS: '%s' is not a standard tts.* or notify.* service and cannot "
                    "receive free-form text. Skipping all TTS announcements. "
                    "Configure tts.cloud_say or similar in the TTS module settings.",
                    self.tts_service,
                )
            return  # Skip — do not attempt call that will always fail

        _LOGGER.debug("TTS announcement: %s", message)

    async def _play_media(
        self,
        msg: dict[str, Any],
        test_mode: bool = False,
    ) -> None:
        """Play a media file (MP3 or URL) on configured media players."""
        media_url = msg.get("media_url", "")
        if not media_url:
            _LOGGER.warning("TTS media message '%s' has no media_url", msg.get("name", "?"))
            return

        if not self.media_players:
            _LOGGER.debug("TTS: no media_players configured for media playback")
            return

        content_type = msg.get("media_content_type", "music")

        volume = self.volume
        if test_mode:
            volume = volume * 0.5

        # Set volume first
        for player in self.media_players:
            await self.async_call_service_with_retry(
                "media_player", "volume_set",
                service_data={"volume_level": volume},
                target={"entity_id": player},
                action=f"media_volume:{player}",
            )

        await asyncio.sleep(0.3)

        # Play media on all players
        for player in self.media_players:
            await self.async_call_service_with_retry(
                "media_player", "play_media",
                service_data={
                    "media_content_id": media_url,
                    "media_content_type": content_type,
                },
                target={"entity_id": player},
                action=f"media_play:{player}",
            )

        _LOGGER.debug("TTS media playback: %s on %s", media_url, self.media_players)

    def _get_mode_name(self, mode: str) -> str:
        """Return Danish mode name."""
        return {
            "away": "ude", "home": "hjemme",
            "night": "nat", "vacation": "ferie",
        }.get(mode, mode)
