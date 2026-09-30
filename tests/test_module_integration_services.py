"""Phase C.3: Module Service Routing Integration Tests

Tests for service call handling, dispatch, and service result validation
across all 6 module types.

Test count: 8 tests across 2 classes
Focus: Service invocation, error handling, response tracking
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, call
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


class TestModuleServiceCalls:
    """Test that modules properly invoke HA services."""

    @pytest.mark.asyncio
    async def test_camera_calls_switch_service(self, mock_hass):
        """Camera module calls switch.turn_on for POE switches."""
        config = {"poe_switches": ["switch.poe"]}
        module = CameraModule(mock_hass, config)
        result = await module.async_call_service(
            "switch", "turn_on",
            target={"entity_id": "switch.poe"}
        )
        assert result is True
        mock_hass.services.async_call.assert_called()

    @pytest.mark.asyncio
    async def test_lock_calls_lock_service(self, mock_hass):
        """Lock module calls lock.lock service."""
        config = {"locks": ["lock.front"]}
        module = LockModule(mock_hass, config)
        result = await module.async_call_service(
            "lock", "lock",
            target={"entity_id": "lock.front"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_lights_calls_light_service(self, mock_hass):
        """Lights module calls light.turn_on service."""
        config = {"lights": ["light.living_room"]}
        module = LightsModule(mock_hass, config)
        result = await module.async_call_service(
            "light", "turn_on",
            service_data={"brightness": 200},
            target={"entity_id": "light.living_room"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_climate_calls_climate_service(self, mock_hass):
        """Climate module calls climate.set_temperature service."""
        config = {"climate_entities": ["climate.thermostat"]}
        module = ClimateModule(mock_hass, config)
        result = await module.async_call_service(
            "climate", "set_temperature",
            service_data={"temperature": 16},
            target={"entity_id": "climate.thermostat"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_siren_calls_siren_service(self, mock_hass):
        """Siren module calls siren.turn_on service."""
        config = {"sirens": []}
        module = SirenModule(mock_hass, config)
        result = await module.async_call_service(
            "siren", "turn_on",
            target={"entity_id": "siren.front"}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_service_call_with_exception(self, mock_hass):
        """Module handles service call exceptions gracefully."""
        mock_hass.services.async_call.side_effect = Exception("Service failed")
        config = {}
        module = CameraModule(mock_hass, config)
        result = await module.async_call_service("switch", "turn_on")
        assert result is False


class TestModuleServiceRetry:
    """Test retry mechanism for failed service calls."""

    @pytest.mark.asyncio
    async def test_retry_on_service_failure(self, mock_hass):
        """Module retries on transient service failure."""
        mock_hass.services.async_call.side_effect = [
            Exception("Temporary failure"),
            None,  # Success on retry
        ]
        config = {
            "retry_max": 2,
            "retry_delay": 0.01,
            "retry_backoff": 2.0,
        }
        module = CameraModule(mock_hass, config)
        result = await module.async_call_service_with_retry(
            "switch", "turn_on",
            target={"entity_id": "switch.poe"}
        )
        assert result is True
        assert mock_hass.services.async_call.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhaustion_sets_degraded(self, mock_hass):
        """Module enters degraded state after max retries."""
        mock_hass.services.async_call.side_effect = Exception("Persistent failure")
        config = {
            "retry_max": 2,
            "retry_delay": 0.01,
            "retry_backoff": 1.0,
        }
        module = CameraModule(mock_hass, config)
        result = await module.async_call_service_with_retry(
            "switch", "turn_on",
            target={"entity_id": "switch.poe"}
        )
        assert result is False
        assert module.degraded is True

    @pytest.mark.asyncio
    async def test_successful_retry_clears_degraded(self, mock_hass):
        """Module clears degraded state on successful recovery."""
        call_count = 0
        async def service_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return None

        mock_hass.services.async_call.side_effect = service_side_effect
        config = {
            "retry_max": 2,
            "retry_delay": 0.01,
            "retry_backoff": 1.0,
        }
        module = CameraModule(mock_hass, config)
        module._degraded = True

        result = await module.async_call_service_with_retry(
            "switch", "turn_on",
            target={"entity_id": "switch.poe"}
        )
        assert result is True
        assert module.degraded is False
