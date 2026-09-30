"""Phase C.2: Module Configuration Integration Tests

Tests for configuration propagation, validation, and defaults
across all 6 module types.

Test count: 8 tests across 2 classes
Focus: Config loading, validation, default values, module-specific options
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
    return hass


class TestModuleConfigurationDefaults:
    """Test that modules use sensible defaults when config keys missing."""

    @pytest.mark.asyncio
    async def test_camera_module_defaults(self, mock_hass):
        """Camera module applies defaults for optional fields."""
        config = {}
        module = CameraModule(mock_hass, config)
        assert module.enabled is True
        assert module.poe_switches == []
        assert module.cameras == []

    @pytest.mark.asyncio
    async def test_lock_module_defaults(self, mock_hass):
        """Lock module applies defaults."""
        config = {}
        module = LockModule(mock_hass, config)
        assert module.enabled is True
        assert module.locks == []

    @pytest.mark.asyncio
    async def test_lights_module_defaults(self, mock_hass):
        """Lights module applies defaults."""
        config = {}
        module = LightsModule(mock_hass, config)
        assert module.enabled is True
        assert module.lights == []

    @pytest.mark.asyncio
    async def test_climate_module_defaults(self, mock_hass):
        """Climate module applies defaults."""
        config = {}
        module = ClimateModule(mock_hass, config)
        assert module.enabled is True
        assert module.climate_entities == []

    @pytest.mark.asyncio
    async def test_siren_module_defaults(self, mock_hass):
        """Siren module applies defaults."""
        config = {}
        module = SirenModule(mock_hass, config)
        assert module.enabled is True
        assert module.sirens == []

    @pytest.mark.asyncio
    async def test_tts_module_defaults(self, mock_hass):
        """TTS module applies defaults."""
        config = {}
        module = TTSModule(mock_hass, config)
        assert module.enabled is True
        assert module.tts_entity == ""
        assert module.speaker_entity == ""


class TestModuleConfigurationValidation:
    """Test that modules validate configuration values."""

    @pytest.mark.asyncio
    async def test_camera_poe_delay_validated(self, mock_hass):
        """Camera module validates POE delay bounds."""
        config = {"poe_delay": 500}  # Too high
        module = CameraModule(mock_hass, config)
        # Module should clamp to MAX_POE_DELAY (300)
        assert module.poe_delay <= 300

    @pytest.mark.asyncio
    async def test_retry_config_from_module_config(self, mock_hass):
        """Module uses retry config from its config dict."""
        config = {
            "retry_max": 5,
            "retry_delay": 0.5,
            "retry_backoff": 1.5,
        }
        module = CameraModule(mock_hass, config)
        assert module._retry_max == 5
        assert module._retry_delay == 0.5
        assert module._retry_backoff == 1.5

    @pytest.mark.asyncio
    async def test_module_config_overrides_defaults(self, mock_hass):
        """Module-specific config overrides are applied."""
        config = {
            "locks": ["lock.front", "lock.back", "lock.garage"],
            "pre_arm_lock_delay": 3,
        }
        module = LockModule(mock_hass, config)
        assert len(module.locks) == 3
        assert module.pre_arm_lock_delay == 3

    @pytest.mark.asyncio
    async def test_lights_brightness_from_config(self, mock_hass):
        """Lights module stores brightness preference."""
        config = {
            "brightness": 75,
            "color_temp": 4000,
        }
        module = LightsModule(mock_hass, config)
        assert module.brightness == 75
        assert module.color_temp == 4000
