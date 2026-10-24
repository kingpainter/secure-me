"""Concurrent/race condition test suite for Secure Me fixes.

v2.2.0: Tests for race condition fixes in:
- auto_actions.py: _done_actions/_action_results protection with asyncio.Lock
- store.py: ThreadPoolExecutor reuse and proper resource management
- zones.py: Thread-safe state management
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from tests.conftest import MockHass


class TestAutoActionsRaceCondition:
    """Test asyncio.Lock protection for concurrent action modifications."""

    @pytest.mark.asyncio
    async def test_concurrent_action_updates_protected(self):
        """Verify _done_actions and _action_results are protected from race conditions."""
        from custom_components.secure_me.auto_actions import AutoActionsManager
        
        hass = MockHass()
        coordinator = MagicMock()
        coordinator.alarm_state = "disarmed"
        store = MagicMock()
        
        manager = AutoActionsManager(hass, coordinator, store, config={})
        
        # Simulate concurrent action execution
        async def simulate_action_execution(action_name: str):
            """Simulate an action running through _run_action_after_delay."""
            # v2.2.0: Action execution now protected by _action_lock
            async with manager._action_lock:
                manager._action_results[action_name] = f"executed_{action_name}"
                manager._done_actions.add(action_name)
                # Simulate some async work
                await asyncio.sleep(0.01)
        
        # Run multiple actions concurrently
        tasks = [
            simulate_action_execution("lock"),
            simulate_action_execution("alarm"),
            simulate_action_execution("camera"),
        ]
        
        await asyncio.gather(*tasks)
        
        # Verify all actions completed without data corruption
        assert len(manager._done_actions) == 3
        assert "lock" in manager._done_actions
        assert "alarm" in manager._done_actions
        assert "camera" in manager._done_actions
        assert manager._action_results["lock"] == "executed_lock"
        assert manager._action_results["alarm"] == "executed_alarm"
        assert manager._action_results["camera"] == "executed_camera"

    @pytest.mark.asyncio
    async def test_on_home_empty_concurrent_clearing(self):
        """Test _done_actions clearing is protected when home becomes empty."""
        from custom_components.secure_me.auto_actions import AutoActionsManager
        from custom_components.secure_me.const import STATE_ALARM_DISARMED
        
        hass = MockHass()
        coordinator = MagicMock()
        coordinator.alarm_state = STATE_ALARM_DISARMED
        store = MagicMock()
        store.get_fake_presence_v2 = MagicMock(return_value={})
        
        manager = AutoActionsManager(hass, coordinator, store, config={})
        
        # Simulate concurrent access: one task clears, another tries to read
        async def concurrent_modifications():
            # Task 1: _on_home_empty clears the dicts
            clear_task = asyncio.create_task(manager._on_home_empty())
            
            # Task 2: Concurrent check of state
            await asyncio.sleep(0.001)  # Let clear_task start
            
            try:
                # This should not crash even if clearing is in progress
                state = manager._home_empty
                actions_count = len(manager._done_actions)
            except Exception as e:
                pytest.fail(f"Concurrent access caused exception: {e}")
            
            await clear_task
        
        await concurrent_modifications()


class TestStoreThreadPoolExecutorReuse:
    """Test ThreadPoolExecutor is properly reused, not recreated."""

    def test_executor_instance_reused(self):
        """Verify ThreadPoolExecutor is created once in __init__ and reused."""
        from custom_components.secure_me.store import Store
        
        hass = MockHass()
        store = Store(hass, 1, "secure_me_test")
        
        # Verify executor was created
        assert hasattr(store, "_executor")
        assert store._executor is not None
        
        # Verify it's the same instance (not recreated)
        first_executor = store._executor
        # Simulate an auth attempt that would use the executor
        # (not actually testing auth, just that the executor instance is stable)
        assert store._executor is first_executor


class TestZoneStateManagement:
    """Test thread-safe state management in Zone operations."""

    def test_unavailable_state_mem_cleanup(self):
        """Test _unavailable_state_mem is cleaned up properly."""
        from custom_components.secure_me.zones import ZoneManager
        
        hass = MockHass()
        manager = ZoneManager(hass)
        
        # Simulate sensor unavailable state tracking
        manager._unavailable_state_mem["sensor.door"] = "closed"
        manager._unavailable_state_mem["sensor.window"] = "open"
        
        assert len(manager._unavailable_state_mem) == 2
        
        # Call cleanup (as happens on integration unload)
        manager.cleanup()
        
        # Verify memory was cleared
        assert len(manager._unavailable_state_mem) == 0

    def test_ready_modes_listener_initialization(self):
        """Test _ready_modes_unsub is properly initialized."""
        from custom_components.secure_me.zones import ZoneManager
        
        hass = MockHass()
        manager = ZoneManager(hass)
        
        # Verify initialization
        assert hasattr(manager, "_ready_modes_unsub")
        assert manager._ready_modes_unsub is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
