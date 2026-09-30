"""Phase C.1: Module Lifecycle Integration Tests

Tests for module initialization, shutdown, cleanup, and state management
across all 6 module types (Camera, Lock, Lights, Climate, Siren, TTS).

Test count: 12 tests across 3 classes
Architecture: Each module inherits from AlarmModule base class
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant

from custom_components.secure_me.modules.base import AlarmModule
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


@pytest.fixture
def base_module_config() -> dict:
    """Base module configuration."""
    return {
        "enabled": True,
        "retry_max": 3,
        "retry_delay": 0.1,
        "retry_backoff": 2.0,
    }


@pytest.fixture
def camera_config(base_module_config) -> dict:
    """Camera module configuration."""
    return {
        **base_module_config,
        "poe_switches": ["switch.camera_poe"],
        "cameras": ["camera.front"],
        "recording_entities": ["select.recording_mode"],
        "poe_delay": 2,
        "auto_record": True,
    }


@pytest.fixture
def lock_config(base_module_config) -> dict:
    """Lock module configuration."""
    return {
        **base_module_config,
        "locks": ["lock.front_door", "lock.back_door"],
        "pre_arm_lock_delay": 1,
    }


class TestModuleInitialization:
    """Test module initialization and property access."""

    @pytest.mark.asyncio
    async def test_camera_module_initializes_with_config(
        self, mock_hass, camera_config
    ):
        """Camera module stores config and exposes it."""
        module = CameraModule(mock_hass, camera_config)
        assert module.enabled is True
        assert module.module_name == "Camera"
        assert module.degraded is False
        assert len(module.poe_switches) == 1
        assert module.poe_delay == 2

    @pytest.mark.asyncio
    async def test_lock_module_initializes_with_config(
        self, mock_hass, lock_config
    ):
        """Lock module stores config and exposes it."""
        module = LockModule(mock_hass, lock_config)
        assert module.enabled is True
        assert module.module_name == "Lock"
        assert len(module.locks) == 2

    @pytest.mark.asyncio
    async def test_module_disabled_on_init(self, mock_hass, base_module_config):
        """Module can be disabled at initialization."""
        config = {**base_module_config, "enabled": False}
        module = CameraModule(mock_hass, config)
        assert module.enabled is False

    @pytest.mark.asyncio
    async def test_all_modules_initialize(self, mock_hass):
        """All 6 module types initialize successfully."""
        modules = [
            CameraModule(mock_hass, {"enabled": True}),
            LockModule(mock_hass, {"enabled": True, "locks": []}),
            LightsModule(mock_hass, {"enabled": True, "lights": []}),
            ClimateModule(mock_hass, {"enabled": True, "climate_entities": []}),
            SirenModule(mock_hass, {"enabled": True, "sirens": []}),
            TTSModule(mock_hass, {"enabled": True, "tts_entity": "", "speaker_entity": ""}),
        ]
        assert len(modules) == 6
        for module in modules:
            assert module.enabled is True
            assert module.degraded is False


class TestModuleLifecycle:
    """Test module async_initialize, async_shutdown, async_cleanup."""

    @pytest.mark.asyncio
    async def test_module_initialize_succeeds(self, mock_hass, camera_config):
        """Module.async_initialize returns True."""
        module = CameraModule(mock_hass, camera_config)
        result = await module.async_initialize()
        assert result is True

    @pytest.mark.asyncio
    async def test_module_shutdown_completes(self, mock_hass, camera_config):
        """Module.async_shutdown completes without error."""
        module = CameraModule(mock_hass, camera_config)
        await module.async_shutdown()

    @pytest.mark.asyncio
    async def test_module_cleanup_calls_shutdown(self, mock_hass, camera_config):
        """Module.async_cleanup calls async_shutdown."""
        module = CameraModule(mock_hass, camera_config)
        with patch.object(module, 'async_shutdown', new_callable=AsyncMock) as mock_shutdown:
            await module.async_cleanup()
            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_module_enable_clears_degraded_state(self, mock_hass, camera_config):
        """Module.enable() clears degraded flag and error count."""
        module = CameraModule(mock_hass, camera_config)
        module._degraded = True
        module._consecutive_errors = 5
        module.enable()
        assert module.enabled is True
        assert module._degraded is False
        assert module._consecutive_errors == 0

    @pytest.mark.asyncio
    async def test_module_disable_sets_disabled_flag(self, mock_hass, camera_config):
        """Module.disable() disables the module."""
        module = CameraModule(mock_hass, camera_config)
        module.disable()
        assert module.enabled is False


class TestModuleStateManagement:
    """Test state backup/restore and entity state tracking."""

    @pytest.mark.asyncio
    async def test_backup_entity_state(self, mock_hass, camera_config):
        """Module backs up entity state."""
        module = CameraModule(mock_hass, camera_config)
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {"brightness": 100}
        mock_hass.states.get.return_value = mock_state

        module.backup_state("light.test")
        backup = module.get_backup_state("light.test")

        assert backup is not None
        assert backup["state"] == "on"
        assert backup["attributes"]["brightness"] == 100

    @pytest.mark.asyncio
    async def test_clear_specific_backup(self, mock_hass, camera_config):
        """Module clears specific entity backup."""
        module = CameraModule(mock_hass, camera_config)
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {}
        mock_hass.states.get.return_value = mock_state

        module.backup_state("light.test1")
        module.backup_state("light.test2")
        module.clear_backup("light.test1")

        assert module.get_backup_state("light.test1") is None
        assert module.get_backup_state("light.test2") is not None

    @pytest.mark.asyncio
    async def test_is_entity_available(self, mock_hass, camera_config):
        """Module checks entity availability."""
        module = CameraModule(mock_hass, camera_config)
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_hass.states.get.return_value = mock_state

        assert module.is_entity_available("light.test") is True

    @pytest.mark.asyncio
    async def test_get_entity_state(self, mock_hass, camera_config):
        """Module retrieves entity state."""
        module = CameraModule(mock_hass, camera_config)
        mock_state = MagicMock()
        mock_state.state = "bright"
        mock_hass.states.get.return_value = mock_state

        state = module.get_entity_state("light.test")
        assert state == "bright"
