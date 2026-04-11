"""TTS module for Secure Me alarm system — v1.4.0 multi-speaker engine."""
# VERSION = "1.3.0"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "da"
DEFAULT_VOLUME = 0.5

MSG_TYPE_TTS   = "tts"
MSG_TYPE_MEDIA = "media"

VALID_TRIGGERS = {
    "armed_away", "armed_home", "armed_night", "armed_vacation",
    "armed_home_alone",
    "disarmed", "triggered", "arming", "pending",
}

_LANG_MAP = {
    "da": "da-DK", "en": "en-US", "de": "de-DE",
    "sv": "sv-SE", "nb": "nb-NO", "nl": "nl-NL",
    "fr": "fr-FR", "es": "es-ES", "it": "it-IT",
    "fi": "fi-FI", "pl": "pl-PL",
}


class SpeakerQueue:
    """Per-speaker asyncio queue -- ensures messages play sequentially on same speaker."""

    def __init__(self, hass: HomeAssistant, profile: dict[str, Any]) -> None:
        self.hass = hass
        self.profile = profile
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = self.hass.async_create_task(self._worker())

    async def enqueue(self, coro) -> None:
        """Add a coroutine to the speaker queue."""
        await self._queue.put(coro)
        self.start()

    async def _worker(self) -> None:
        while True:
            try:
                coro = await asyncio.wait_for(self._queue.get(), timeout=30)
                try:
                    await coro
                except Exception as err:
                    _LOGGER.error(
                        "SpeakerQueue error on %s: %s",
                        self.profile.get("entity_id", "?"), err,
                    )
                finally:
                    self._queue.task_done()
            except asyncio.TimeoutError:
                break  # idle -- stop worker, restart on next message

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()


class TTSModule(AlarmModule):
    """TTS module -- multi-speaker engine with per-speaker queuing.

    Speaker profiles define entity_id, volume, tts_service, tts_entity.
    Messages are played in parallel across speakers, queued per speaker.
    Custom messages can target specific speaker profiles by entity_id.
    """

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        super().__init__(hass, config)

        # v1.4.0: speaker profiles from store (list of dicts)
        self._speaker_profiles: list[dict[str, Any]] = config.get("speaker_profiles", [])

        # Legacy flat config -- used if no speaker_profiles defined
        self._legacy_players: list[str] = config.get("media_players", [])
        self._legacy_service: str       = config.get("tts_service", "tts.cloud_say")
        self._legacy_entity: str        = config.get("tts_entity", "tts.home_assistant_cloud")
        self._legacy_volume: float      = float(config.get("volume", DEFAULT_VOLUME))

        self.language: str              = config.get("language", DEFAULT_LANGUAGE)
        self.custom_messages: list[dict[str, Any]] = config.get("custom_messages", [])

        # Per-speaker queue map: entity_id -> SpeakerQueue
        self._queues: dict[str, SpeakerQueue] = {}
        self._warned_incompatible: bool = False

    # -- Public API ----------------------------------------------------------

    def get_speakers(self) -> list[dict[str, Any]]:
        """Return resolved speaker list (profiles or legacy fallback)."""
        if self._speaker_profiles:
            return self._speaker_profiles
        # Legacy: build a synthetic profile per player
        return [
            {
                "name": eid,
                "entity_id": eid,
                "volume": self._legacy_volume,
                "tts_service": self._legacy_service,
                "tts_entity": self._legacy_entity,
            }
            for eid in self._legacy_players
        ]

    async def announce_system(
        self,
        message: str,
        urgent: bool = False,
        speaker_ids: list[str] | None = None,
    ) -> None:
        """Play a system message on specified speakers (None = all)."""
        if not self.enabled:
            return
        speakers = self.get_speakers()
        if speaker_ids is not None:
            speakers = [s for s in speakers if s.get("entity_id") in speaker_ids]
        if not speakers:
            _LOGGER.debug("TTS: no speakers available, skipping")
            return
        await self._play_on_speakers(message, speakers, urgent=urgent)

    async def announce_on_profiles(
        self,
        message: str,
        profile_names: list[str],
        urgent: bool = False,
    ) -> None:
        """Play a message on speakers matched by profile name."""
        speakers = [
            s for s in self.get_speakers()
            if s.get("name") in profile_names
        ]
        if not speakers:
            _LOGGER.debug("TTS: no speakers matched profiles %s", profile_names)
            return
        await self._play_on_speakers(message, speakers, urgent=urgent)

    # -- Alarm module hooks --------------------------------------------------

    async def async_arm(self, mode: str) -> bool:
        if not self.enabled:
            return True
        trigger = f"armed_{mode}" if mode in (
            "away", "home", "night", "vacation", "home_alone"
        ) else mode
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

    async def async_cleanup(self) -> None:
        for q in self._queues.values():
            q.stop()
        self._queues.clear()

    async def async_test(self) -> dict[str, Any]:
        speakers = self.get_speakers()
        results: dict[str, Any] = {
            "success": True,
            "message": "TTS module test passed",
            "details": {
                "speakers": [],
                "language": self.language,
                "custom_messages": len(self.custom_messages),
                "test_announcement": False,
            },
        }
        for sp in speakers:
            eid = sp.get("entity_id", "")
            state = self.hass.states.get(eid)
            info = {
                "entity_id": eid,
                "name": sp.get("name", eid),
                "available": self.is_entity_available(eid),
                "state": state.state if state else None,
                "volume": sp.get("volume", DEFAULT_VOLUME),
                "tts_service": sp.get("tts_service", "tts.cloud_say"),
            }
            if not info["available"]:
                results["success"] = False
                results["message"] = f"Speaker {eid} unavailable"
            results["details"]["speakers"].append(info)

        test_msg = next((m for m in self.custom_messages if m.get("enabled", True)), None)
        if test_msg:
            try:
                await self._play_message(test_msg, test_mode=True)
                results["details"]["test_announcement"] = True
            except Exception as err:
                _LOGGER.error("TTS test failed: %s", err)
                results["success"] = False
                results["message"] = "TTS announcement test failed"
        return results

    # -- Internal ------------------------------------------------------------

    def _get_queue(self, entity_id: str, profile: dict) -> SpeakerQueue:
        if entity_id not in self._queues:
            self._queues[entity_id] = SpeakerQueue(self.hass, profile)
        return self._queues[entity_id]

    async def _play_on_speakers(
        self,
        message: str,
        speakers: list[dict[str, Any]],
        urgent: bool = False,
        test_mode: bool = False,
    ) -> None:
        """Parallel across speakers, queued per speaker."""
        async def _speak_on(profile: dict) -> None:
            volume = float(profile.get("volume", DEFAULT_VOLUME))
            if urgent:
                volume = min(volume * 1.3, 1.0)
            elif test_mode:
                volume = volume * 0.5
            await self._speak(message, profile, volume)

        coros = []
        for sp in speakers:
            eid = sp.get("entity_id", "")
            if not eid:
                continue
            q = self._get_queue(eid, sp)
            coros.append(q.enqueue(_speak_on(sp)))

        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    async def _speak(
        self,
        message: str,
        profile: dict[str, Any],
        volume: float,
    ) -> None:
        """Execute a single TTS announcement on one speaker."""
        entity_id   = profile.get("entity_id", "")
        tts_service = profile.get("tts_service", "tts.cloud_say")

        if not entity_id:
            return

        try:
            service_domain, service_name = tts_service.split(".", 1)
        except ValueError:
            _LOGGER.error("Invalid TTS service '%s' on %s", tts_service, entity_id)
            return

        # Set volume
        await self.async_call_service(
            "media_player", "volume_set",
            service_data={"volume_level": volume},
            target={"entity_id": entity_id},
        )
        await asyncio.sleep(0.4)

        if service_domain == "tts":
            language = self.language or "da-DK"
            if service_name in (
                "cloud_say", "google_say", "google_translate_say", "piper"
            ) and language in _LANG_MAP:
                language = _LANG_MAP[language]

            await self.async_call_service(
                service_domain, service_name,
                service_data={
                    "message": message,
                    "language": language,
                    "cache": False,
                },
                target={"entity_id": entity_id},
            )

        elif service_domain == "notify":
            await self.async_call_service(
                service_domain, service_name,
                service_data={"message": message, "title": "Secure Me"},
            )

        else:
            if not self._warned_incompatible:
                self._warned_incompatible = True
                _LOGGER.warning(
                    "TTS: '%s' not supported (use tts.* or notify.*). Speaker: %s",
                    tts_service, entity_id,
                )
            return

        _LOGGER.debug("TTS spoke on %s: %s", entity_id, message)

    async def _fire_custom_messages(self, trigger: str) -> None:
        for msg in self.custom_messages:
            if not msg.get("enabled", True):
                continue
            if msg.get("trigger") != trigger:
                continue
            try:
                await self._play_message(msg)
            except Exception as err:
                _LOGGER.error(
                    "TTS custom message '%s' failed: %s",
                    msg.get("name", "?"), err,
                )

    async def _play_message(self, msg: dict[str, Any], test_mode: bool = False) -> None:
        msg_type = msg.get("type", MSG_TYPE_TTS)
        if msg_type == MSG_TYPE_MEDIA:
            await self._play_media(msg, test_mode=test_mode)
            return

        text = msg.get("message", "")
        if not text:
            return

        # Resolve speakers: msg.speakers = list of entity_ids, None = all
        msg_speaker_ids = msg.get("speakers")
        speakers = self.get_speakers()
        if msg_speaker_ids:
            speakers = [s for s in speakers if s.get("entity_id") in msg_speaker_ids]
        if not speakers:
            speakers = self.get_speakers()

        await self._play_on_speakers(text, speakers, test_mode=test_mode)

    async def _play_media(self, msg: dict[str, Any], test_mode: bool = False) -> None:
        media_url = msg.get("media_url", "")
        if not media_url:
            _LOGGER.warning("Media message '%s' has no media_url", msg.get("name", "?"))
            return

        speakers = self.get_speakers()
        msg_speaker_ids = msg.get("speakers")
        if msg_speaker_ids:
            speakers = [s for s in speakers if s.get("entity_id") in msg_speaker_ids]
        if not speakers:
            return

        content_type = msg.get("media_content_type", "music")

        for sp in speakers:
            eid = sp.get("entity_id", "")
            volume = float(sp.get("volume", DEFAULT_VOLUME))
            if test_mode:
                volume = volume * 0.5
            await self.async_call_service(
                "media_player", "volume_set",
                service_data={"volume_level": volume},
                target={"entity_id": eid},
            )

        await asyncio.sleep(0.3)

        for sp in speakers:
            eid = sp.get("entity_id", "")
            await self.async_call_service(
                "media_player", "play_media",
                service_data={
                    "media_content_id": media_url,
                    "media_content_type": content_type,
                },
                target={"entity_id": eid},
            )
