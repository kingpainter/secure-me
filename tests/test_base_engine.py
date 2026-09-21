"""Unit tests for BaseEngine lifecycle management."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.secure_me.engine.base_engine import BaseEngine


class TestBaseEngine:
    """Test BaseEngine initialization and lifecycle."""

    @pytest.fixture
    def mock_hass(self):
        """Create mock Home Assistant instance."""
        return MagicMock()

    @pytest.fixture
    def engine(self, mock_hass):
        """Create BaseEngine instance for testing."""
        return BaseEngine(mock_hass, {})

    def test_init_sets_hass_and_logger(self, mock_hass):
        """Test __init__ sets hass and creates logger."""
        engine = BaseEngine(mock_hass, {})
        assert engine.hass == mock_hass
        assert engine.logger is not None

    def test_is_running_initially_false(self, engine):
        """Test is_running returns False before async_start."""
        assert engine.is_running() is False

    @pytest.mark.asyncio
    async def test_async_start_sets_running(self, engine):
        """Test async_start sets running state."""
        await engine.async_start()
        assert engine.is_running() is True

    @pytest.mark.asyncio
    async def test_async_stop_clears_running(self, engine):
        """Test async_stop clears running state."""
        await engine.async_start()
        assert engine.is_running() is True
        await engine.async_stop()
        assert engine.is_running() is False

    @pytest.mark.asyncio
    async def test_cleanup_cancels_pending_tasks(self, engine):
        """Test cleanup cancels registered async tasks."""
        # Create a task and register it
        async def dummy_coro():
            await asyncio.sleep(10)
        
        task = asyncio.create_task(dummy_coro())
        engine.register_cleanup(task)
        
        # Task should be running
        assert not task.done()
        
        # Cleanup should cancel it
        await engine._cleanup_tasks()
        await asyncio.sleep(0.01)  # Give cancellation time to propagate
        
        assert task.cancelled() or task.done()

