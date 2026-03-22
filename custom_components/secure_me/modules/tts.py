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

MSG_TYPE_TTS = "tts"
MSG_TYPE_MEDIA = "media"

VALID_TRIGGERS = {
    "armed_away", "armed_home", "armed_night", "armed_vacation",
    "disarmed", "triggered", "arming", "pending",
}


class TTSModule(AlarmModule):
    """TTS module for custom voice and media announcements."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)
        self.media_players: list[str] = config.get("media_players", [])
        self.tts_service: str = config.get("tts_service", "tts.cloud_say")
        self.tts_entity: str = config.get("tts_entity", "tts.home_assistant_cloud")
        self.language: str = config.get("language", DEFAULT_LANGUAGE)
        self.volume: float = float(config.get("volume", DEFAULT_VOLUME))
        self.custom_messages: list[dict[str, Any]] = config.get("custom_messages", [])
        self._warned_incompatible_service: bool = False

    async def async_arm(self, mode: str) -> bool:
        if not self.enabled:
            return True
        trigger = f"armed_{mode}" if mode in ("away", "home", "night", "vacation") else mode
        await self._fire_custom_messages(trigger)
        return True

    async def async_disarm(self) -> bool:
        if not self.enabled:
            return True
        await self._fire_custom_messages("disarmed")
        return True

    async def async_trigger(self) -> bool:
        if not self.enabled:
            return True
        await self._fire_custom_messages("triggered")
        return True

    async def async_test(self) -> dict[str, Any]:
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

        test_msg = next((m for m in self.custom_messages if m.get("enabled", True)), None)
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

    async def announce_system(self, message: str, urgent: bool = False) -> None:
        """Play a system status message via TTS (called by notification_dispatcher)."""
        if not self.enabled or not self.media_players:
            return
        await self._announce_tts(message, urgent=urgent)

    async def _fire_custom_messages(self, trigger: str) -> None:
        for msg in self.custom_messages:
            if not msg.get("enabled", True):
                continue
            if msg.get("trigger") != trigger:
                continue
            try:
                await self._play_message(msg)
            except Exception as err:
                _LOGGER.error("TTS custom message '%s' failed: %s", msg.get("name", "?"), err)

    async def _play_message(self, msg: dict[str, Any], test_mode: bool = False) -> None:
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
        if not self.media_players:
            _LOGGER.debug("TTS: no media_players configured, skipping")
            return

        try:
            service_domain, service_name = self.tts_service.split(".", 1)
        except ValueError:
            _LOGGER.error("Invalid TTS service '%s'", self.tts_service)
            return

        if service_domain == "tts":
            # Standard HA TTS — set volume first, then speak
            volume = self.volume
            if urgent:
                volume = min(volume * 1.5, 1.0)
            elif test_mode:
                volume = volume * 0.5

            for player in self.media_players:
                await self.async_call_service_with_retry(
                    "media_player", "volume_set",
                    service_data={"volume_level": volume},
                    target={"entity_id": player},
                    action=f"tts_volume:{player}",
                )
            await asyncio.sleep(0.5)

            # Normalise short language codes to BCP-47 for cloud_say
            _LANG_MAP = {
                "da": "da-DK", "en": "en-US", "de": "de-DE",
                "sv": "sv-SE", "nb": "nb-NO", "nl": "nl-NL",
                "fr": "fr-FR", "es": "es-ES", "it": "it-IT",
                "fi": "fi-FI", "pl": "pl-PL",
            }
            language = self.language or "da-DK"
            if service_name in ("cloud_say",) and language in _LANG_MAP:
                language = _LANG_MAP[language]

            await self.async_call_service_with_retry(
                service_domain, service_name,
                service_data={
                    "message": message,
                    "language": language,
                    "cache": False,
                },
                target={"entity_id": self.media_players},
                action="tts_announce",
            )

        elif service_domain == "notify":
            # notify.* — message + title, no volume control
            await self.async_call_service_with_retry(
                service_domain, service_name,
                service_data={"message": message, "title": "Secure Me"},
                action="tts_announce",
            )

        elif service_domain == "script":
            # script.ultra_tts dukker volumen ned internt (original * 0.25).
            # For at sikre at TTS tales ved den konfigurerede volumen,
            # bypasser vi ducking ved at kalde tts.speak direkte med
            # volumen sat til det oenskede niveau foer og restore bagefter.
            tts_volume = min(self.volume * 1.5, 1.0) if urgent else self.volume
            if test_mode:
                tts_volume = tts_volume * 0.5

            # Gem original volumen og saet til oenset TTS-niveau
            original_volumes: dict[str, float] = {}
            for player in self.media_players:
                state = self.hass.states.get(player)
                if state:
                    original_volumes[player] = float(
                        state.attributes.get("volume_level", tts_volume)
                    )
                await self.async_call_service(
                    "media_player", "volume_set",
                    service_data={"volume_level": tts_volume},
                    target={"entity_id": player},
                )

            await asyncio.sleep(0.4)

            # Kald tts.speak direkte — single attempt, NO retry.
            # Retry ville afspille beskeden to gange hvis Alexa er optaget.
            await self.async_call_service(
                "tts", "speak",
                service_data={
                    "message": message,
                    "cache": False,
                    "media_player_entity_id": self.media_players,
                },
                target={"entity_id": self.tts_entity},
            )

            # Vent pa at beskeden er faerdig (dynamisk baseret paa laengde)
            wait_seconds = max(3, len(message) // 12)
            await asyncio.sleep(wait_seconds)

            # Restore original volumen
            for player, vol in original_volumes.items():
                await self.async_call_service(
                    "media_player", "volume_set",
                    service_data={"volume_level": vol},
                    target={"entity_id": player},
                )

        else:
            # Unknown service type — warn once, skip silently.
            if not self._warned_incompatible_service:
                self._warned_incompatible_service = True
                _LOGGER.warning(
                    "TTS: '%s' is not a supported service (tts.*, notify.*, script.*). "
                    "Skipping announcements. Use tts.cloud_say or script.ultra_tts.",
                    self.tts_service,
                )
            return

        _LOGGER.debug("TTS announcement sent: %s", message)

    async def _play_media(self, msg: dict[str, Any], test_mode: bool = False) -> None:
        media_url = msg.get("media_url", "")
        if not media_url:
            _LOGGER.warning("TTS media message '%s' has no media_url", msg.get("name", "?"))
            return
        if not self.media_players:
            _LOGGER.debug("TTS: no media_players configured for media playback")
            return

        content_type = msg.get("media_content_type", "music")
        volume = self.volume * 0.5 if test_mode else self.volume

        for player in self.media_players:
            await self.async_call_service_with_retry(
                "media_player", "volume_set",
                service_data={"volume_level": volume},
                target={"entity_id": player},
                action=f"media_volume:{player}",
            )
        await asyncio.sleep(0.3)

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
        return {
            "away": "ude", "home": "hjemme",
            "night": "nat", "vacation": "ferie",
        }.get(mode, mode)
