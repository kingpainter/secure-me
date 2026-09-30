"""Phase C.6: Module Cross-Module Coordination Tests

Tests for module-to-module coordination, event handling, race conditions,
and coordinator integration patterns.

Test count: 5 tests across 2 classes
Focus: Async coordination, multi-module scenarios, state coherence
"""

from __future__ import annotations

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from homeassistant.core import HomeAssistant

from custom_components.secure_me.modules.camera import CameraModule
from custom_components.secure_me.modules.lock import LockModule
from custom_components.secure_me.modules.lights import LightsModule
from custom_components.secure_me.modules.siren import SirenModule


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


class TestModuleCoordination:
    """Test coordination between multiple modules."""

    @pytest.mark.asyncio
    async def test_multiple_modules_arm_independently(self, mock_hass):
        """Multiple modules can arm independently."""
        modules = [
            CameraModule(mock_hass, {"poe_switches": ["switch.poe"]}),
            LockModule(mock_hass, {"locks": ["lock.front"]}),
            LightsModule(mock_hass, {"lights": ["light.living_room"]}),
        ]

        mock_hass.services.async_call.return_value = None

        results = await asyncio.gather(*[m.async_arm("away") for m in modules])

        assert all(results)
        assert mock_hass.services.async_call.call_count >= 3

    @pytest.mark.asyncio
    async def test_multiple_modules_disarm_independently(self, mock_hass):
        """Multiple modules can disarm independently."""
        modules = [
            CameraModule(mock_hass, {}),
            LockModule(mock_hass, {"locks": []}),
            SirenModule(mock_hass, {"sirens": []}),
        ]

        mock_hass.services.async_call.return_value = None

        results = await asyncio.gather(*[m.async_disarm() for m in modules])

        assert all(results)

    @pytest.mark.asyncio
    async def test_concurrent_module_operations_no_race(self, mock_hass):
        """Concurrent module operations don't cause race conditions."""
        camera = CameraModule(mock_hass, {"poe_switches": ["switch.poe"]})
        lock = LockModule(mock_hass, {"locks": ["lock.front"]})
        lights = LightsModule(mock_hass, {"lights": ["light.living_room"]})

        mock_hass.services.async_call.return_value = None

        # Trigger multiple operations concurrently
        tasks = [
            camera.async_arm("away"),
            lock.async_arm("away"),
            lights.async_arm("away"),
            camera.async_disarm(),
            lock.async_disarm(),
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert all(results)
        # Each module should be coherent
        assert camera.enabled is True
        assert lock.enabled is True
        assert lights.enabled is True


class TestModuleInitializationSequence:
    """Test proper initialization and shutdown sequencing."""

    @pytest.mark.asyncio
    async def test_sequential_module_initialization(self, mock_hass):
        """Modules can be initialized in sequence."""
        modules = [
            CameraModule(mock_hass, {}),
            LockModule(mock_hass, {"locks": []}),
            SirenModule(mock_hass, {"sirens": []}),
        ]

        for module in modules:
            result = await module.async_initialize()
            assert result is True

    @pytest.mark.asyncio
    async def test_concurrent_module_shutdown(self, mock_hass):
        """Multiple modules can shut down concurrently."""
        modules = [
            CameraModule(mock_hass, {}),
            LockModule(mock_hass, {"locks": []}),
            LightsModule(mock_hass, {"lights": []}),
            SirenModule(mock_hass, {"sirens": []}),
        ]

        # Initialize all
        for module in modules:
            await module.async_initialize()

        # Shutdown concurrently
        await asyncio.gather(*[m.async_shutdown() for m in modules])

        # All should still be coherent
        for module in modules:
            assert module.enabled is True  # Shutdown doesn't disable
