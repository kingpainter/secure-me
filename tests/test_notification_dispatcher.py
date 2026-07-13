"""Tests for Secure Me notification_dispatcher.py -- Home Alone quick response."""
# VERSION = "1.5.0"

import time

import pytest
from unittest.mock import AsyncMock, MagicMock

from custom_components.secure_me.notification_dispatcher import (
    handle_home_alone_quick_response,
)
from custom_components.secure_me.const import (
    DOMAIN,
    EVENT_HOME_ALONE_ACTION_1,
    EVENT_HOME_ALONE_ACTION_2,
    CONF_HOME_ALONE_SPEAKER,
    CONF_HOME_ALONE_ACTION_1,
    CONF_HOME_ALONE_ACTION_2,
    HOME_ALONE_DEFAULT_ACTION_1,
    HOME_ALONE_DEFAULT_ACTION_2,
)


class TestHomeAloneQuickResponse:
    """Regression tests for handle_home_alone_quick_response().

    Previously, tapping either quick-response button on a Home Alone door
    notification did nothing at all: the action id wasn't in
    PUSH_EVENT_ACTIONS, so coordinator._handle_push_event silently dropped
    it at the very first filter check. No test file existed for
    notification_dispatcher.py at all before this.
    """

    def _make_hass(self, tts_module=None):
        hass = MagicMock()
        hass.data = {DOMAIN: {}}
        if tts_module is not None:
            coordinator = MagicMock()
            coordinator.modules = {"tts": tts_module}
            hass.data[DOMAIN]["entry1"] = {"coordinator": coordinator}
        return hass

    def _make_tts_module(self, enabled=True):
        tts = MagicMock()
        tts.enabled = enabled
        tts.announce_system = AsyncMock()
        return tts

    @pytest.mark.asyncio
    async def test_no_context_does_not_call_tts(self):
        tts = self._make_tts_module()
        hass = self._make_hass(tts)
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_1)
        tts.announce_system.assert_not_called()

    @pytest.mark.asyncio
    async def test_stale_context_does_not_call_tts(self):
        """Regression: a tap on an old, already-resolved notification must not fire."""
        tts = self._make_tts_module()
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {CONF_HOME_ALONE_SPEAKER: "media_player.hallway"},
            "timestamp": time.monotonic() - 301,  # just over the 5-minute limit
        }
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_1)
        tts.announce_system.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_speaker_configured_does_not_call_tts(self):
        tts = self._make_tts_module()
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {},  # no speaker
            "timestamp": time.monotonic(),
        }
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_1)
        tts.announce_system.assert_not_called()

    @pytest.mark.asyncio
    async def test_action_1_speaks_action_1_message_on_configured_speaker(self):
        tts = self._make_tts_module()
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {
                CONF_HOME_ALONE_SPEAKER: "media_player.hallway",
                CONF_HOME_ALONE_ACTION_1: "Where are you going?",
            },
            "timestamp": time.monotonic(),
        }
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_1)
        tts.announce_system.assert_called_once()
        args, kwargs = tts.announce_system.call_args
        assert args[0] == "Where are you going?"
        assert kwargs["speaker_ids"] == ["media_player.hallway"]

    @pytest.mark.asyncio
    async def test_action_2_speaks_action_2_message(self):
        tts = self._make_tts_module()
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {
                CONF_HOME_ALONE_SPEAKER: "media_player.hallway",
                CONF_HOME_ALONE_ACTION_2: "Please close the door.",
            },
            "timestamp": time.monotonic(),
        }
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_2)
        args, kwargs = tts.announce_system.call_args
        assert args[0] == "Please close the door."

    @pytest.mark.asyncio
    async def test_missing_custom_text_falls_back_to_default(self):
        tts = self._make_tts_module()
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {CONF_HOME_ALONE_SPEAKER: "media_player.hallway"},
            "timestamp": time.monotonic(),
        }
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_1)
        args, _ = tts.announce_system.call_args
        assert args[0] == HOME_ALONE_DEFAULT_ACTION_1

    @pytest.mark.asyncio
    async def test_action_2_missing_custom_text_falls_back_to_default(self):
        tts = self._make_tts_module()
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {CONF_HOME_ALONE_SPEAKER: "media_player.hallway"},
            "timestamp": time.monotonic(),
        }
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_2)
        args, _ = tts.announce_system.call_args
        assert args[0] == HOME_ALONE_DEFAULT_ACTION_2

    @pytest.mark.asyncio
    async def test_unknown_action_does_not_call_tts(self):
        tts = self._make_tts_module()
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {CONF_HOME_ALONE_SPEAKER: "media_player.hallway"},
            "timestamp": time.monotonic(),
        }
        await handle_home_alone_quick_response(hass, "SOME_UNRELATED_ACTION")
        tts.announce_system.assert_not_called()

    @pytest.mark.asyncio
    async def test_tts_module_not_enabled_does_not_crash(self):
        tts = self._make_tts_module(enabled=False)
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {CONF_HOME_ALONE_SPEAKER: "media_player.hallway"},
            "timestamp": time.monotonic(),
        }
        # Should not raise even though the TTS module is disabled
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_1)
        tts.announce_system.assert_not_called()

    @pytest.mark.asyncio
    async def test_tts_failure_does_not_raise(self):
        """A TTS error must not propagate and break the push-event handler."""
        tts = self._make_tts_module()
        tts.announce_system.side_effect = Exception("speaker unreachable")
        hass = self._make_hass(tts)
        hass.data[DOMAIN]["_last_home_alone_trigger"] = {
            "entity_id": "binary_sensor.front_door",
            "sensor_cfg": {CONF_HOME_ALONE_SPEAKER: "media_player.hallway"},
            "timestamp": time.monotonic(),
        }
        # Should not raise
        await handle_home_alone_quick_response(hass, EVENT_HOME_ALONE_ACTION_1)
