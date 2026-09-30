"""Phase C.5: Module Error Handling & Recovery Tests

Tests for error scenarios, recovery mechanisms, graceful degradation,
and notification/logging behavior.

Test count: 6 tests across 2 classes
Focus: Error handling, state recovery, notification dispatch, logging
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.core import HomeAssistant

from custom_components.secure_me.modules.camera import CameraModule
from custom_components.secure_me.modules.lock import LockModule
from custom_components.secure_me.modules.lights import LightsModule


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.services = AsyncMock()
    hass.services.async_call = AsyncMock()
    hass.states = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    return hass


class TestModuleErrorRecovery:
    """Test module error handling and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_module_recovers_from_transient_error(self, mock_hass):
        """Module recovers after transient service failure."""
        config = {
            "retry_max": 3,
            "retry_delay": 0.01,
            "retry_backoff": 1.5,
        }
        module = CameraModule(mock_hass, config)
        module._degraded = True
        module._consecutive_errors = 2

        mock_hass.services.async_call.return_value = None

        result = await module.async_call_service_with_retry(
            "switch", "turn_on",
            target={"entity_id": "switch.poe"}
        )

        assert result is True
        assert module.degraded is False
        assert module._consecutive_errors == 0

    @pytest.mark.asyncio
    async def test_module_persistent_error_state(self, mock_hass):
        """Module stays degraded after persistent errors."""
        config = {
            "retry_max": 2,
            "retry_delay": 0.01,
            "retry_backoff": 1.0,
        }
        module = LockModule(mock_hass, config)
        mock_hass.services.async_call.side_effect = Exception("Service unavailable")

        result = await module.async_call_service_with_retry(
            "lock", "lock",
            target={"entity_id": "lock.front"}
        )

        assert result is False
        assert module.degraded is True

    @pytest.mark.asyncio
    async def test_disabled_module_skips_execution(self, mock_hass):
        """Disabled module returns True without executing."""
        config = {"enabled": False}
        module = CameraModule(mock_hass, config)
        mock_hass.services.async_call.return_value = None

        result = await module.async_arm("away")

        assert result is True
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_module_consecutive_errors_tracked(self, mock_hass):
        """Module tracks consecutive error count."""
        config = {
            "retry_max": 1,
            "retry_delay": 0.01,
        }
        module = LightsModule(mock_hass, config)
        mock_hass.services.async_call.side_effect = Exception("Error")

        for _ in range(3):
            await module.async_call_service_with_retry(
                "light", "turn_on",
                target={"entity_id": "light.test"}
            )

        assert module._consecutive_errors == 3


class TestModuleGracefulDegradation:
    """Test graceful degradation when modules fail."""

    @pytest.mark.asyncio
    async def test_module_enters_degraded_after_retries(self, mock_hass):
        """Module enters degraded state after retry exhaustion."""
        config = {
            "retry_max": 2,
            "retry_delay": 0.01,
            "retry_backoff": 1.0,
        }
        module = CameraModule(mock_hass, config)
        assert module.degraded is False

        mock_hass.services.async_call.side_effect = Exception("Network error")
        result = await module.async_call_service_with_retry(
            "switch", "turn_on",
            target={"entity_id": "switch.poe"}
        )

        assert result is False
        assert module.degraded is True

    @pytest.mark.asyncio
    async def test_module_test_catches_exceptions(self, mock_hass):
        """Module test method handles exceptions gracefully."""
        config = {}
        module = CameraModule(mock_hass, config)
        mock_hass.services.async_call.side_effect = Exception("Test failed")

        result = await module.async_test()

        # Should return a dict even on error
        assert isinstance(result, dict)
