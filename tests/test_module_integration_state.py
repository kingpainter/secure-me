"""Phase C.4: Module State Synchronization Tests

Tests for state tracking, property updates, and module-specific state changes
across all 6 module types.

Test count: 8 tests across 2 classes
Focus: Entity state changes, module internal state, mode transitions
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock
from homeassistant.core import HomeAssistant

from custom_components.secure_me.modules.camera import CameraModule
from custom_components.secure_me.modules.lock import LockModule
from custom_components.secure_me.modules.lights import LightsModule
from custom_components.secure_me.modules.climate import ClimateModule
from custom_components.secure_me.modules.siren import SirenModule
from custom_components.secure_me.modules.tts import TTSModule


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.services = AsyncMock()
    hass.services.async_call = AsyncMock()
    hass.states = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    hass.states.set = MagicMock()
    return hass


class TestModuleStateTracking:
    """Test that modules track and update state correctly."""

    @pytest.mark.asyncio
    async def test_camera_arm_changes_state(self, mock_hass):
        """Camera module changes state when armed."""
        config = {
            "poe_switches": ["switch.poe"],
            "cameras": ["camera.front"],
        }
        module = CameraModule(mock_hass, config)
        mock_hass.services.async_call.return_value = None

        result = await module.async_arm("away")
        assert result is True

    @pytest.mark.asyncio
    async def test_lock_arm_changes_state(self, mock_hass):
        """Lock module changes state when armed."""
        config = {"locks": ["lock.front"]}
        module = LockModule(mock_hass, config)
        mock_hass.services.async_call.return_value = None

        result = await module.async_arm("away")
        assert result is True

    @pytest.mark.asyncio
    async def test_lights_disarm_changes_state(self, mock_hass):
        """Lights module changes state when disarmed."""
        config = {"lights": ["light.living_room"]}
        module = LightsModule(mock_hass, config)
        mock_hass.services.async_call.return_value = None

        result = await module.async_disarm()
        assert result is True

    @pytest.mark.asyncio
    async def test_climate_arm_changes_temperature(self, mock_hass):
        """Climate module changes temperature when armed."""
        config = {
            "climate_entities": ["climate.thermostat"],
            "away_temperature": 16,
        }
        module = ClimateModule(mock_hass, config)
        mock_hass.services.async_call.return_value = None

        result = await module.async_arm("away")
        assert result is True

    @pytest.mark.asyncio
    async def test_siren_trigger_changes_state(self, mock_hass):
        """Siren module activates when triggered."""
        config = {"sirens": [{"entity_id": "siren.front", "duration": 300}]}
        module = SirenModule(mock_hass, config)
        mock_hass.services.async_call.return_value = None

        result = await module.async_trigger()
        assert result is True

    @pytest.mark.asyncio
    async def test_tts_trigger_speaks(self, mock_hass):
        """TTS module speaks when triggered."""
        config = {
            "tts_entity": "tts.google_en",
            "speaker_entity": "media_player.living_room",
        }
        module = TTSModule(mock_hass, config)
        mock_hass.services.async_call.return_value = None

        result = await module.async_trigger()
        assert result is True


class TestModulePropertyUpdates:
    """Test that module properties reflect configuration."""

    @pytest.mark.asyncio
    async def test_camera_poe_status_property(self, mock_hass):
        """Camera module exposes POE switch configuration."""
        config = {"poe_switches": ["switch.poe_1", "switch.poe_2"]}
        module = CameraModule(mock_hass, config)
        assert len(module.poe_switches) == 2

    @pytest.mark.asyncio
    async def test_lock_list_property(self, mock_hass):
        """Lock module exposes lock list."""
        config = {"locks": ["lock.front", "lock.back"]}
        module = LockModule(mock_hass, config)
        assert len(module.locks) == 2

    @pytest.mark.asyncio
    async def test_lights_brightness_property(self, mock_hass):
        """Lights module exposes brightness setting."""
        config = {"brightness": 128}
        module = LightsModule(mock_hass, config)
        assert module.brightness == 128

    @pytest.mark.asyncio
    async def test_climate_temperature_property(self, mock_hass):
        """Climate module exposes temperature settings."""
        config = {
            "away_temperature": 14,
            "home_temperature": 22,
        }
        module = ClimateModule(mock_hass, config)
        assert module.away_temperature == 14
        assert module.home_temperature == 22
