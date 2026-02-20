"""Lock module for Secure Me alarm system."""
# VERSION = "0.3.6"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)

# Default settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5


class LockModule(AlarmModule):
    """Smart lock control module with retry logic."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize lock module.
        
        Config options:
            - locks: List of lock entity IDs
            - door_sensors: Dict mapping lock -> door sensor entity ID
            - battery_sensors: Dict mapping lock -> battery sensor entity ID
            - max_retries: Maximum lock attempts (default: 3)
            - retry_delay: Seconds between retries (default: 5)
            - lock_on_arm: Lock doors when arming (default: True)
            - unlock_on_disarm: Unlock doors when disarming (default: False)
        """
        super().__init__(hass, config)
        
        self.locks = config.get("locks", [])
        self.door_sensors = config.get("door_sensors", {})
        self.battery_sensors = config.get("battery_sensors", {})
        self.max_retries = config.get("max_retries", DEFAULT_MAX_RETRIES)
        self.retry_delay = config.get("retry_delay", DEFAULT_RETRY_DELAY)
        self.lock_on_arm = config.get("lock_on_arm", True)
        self.unlock_on_disarm = config.get("unlock_on_disarm", False)
        
    async def async_arm(self, mode: str) -> bool:
        """Lock doors when arming (with retry)."""
        if not self.enabled or not self.lock_on_arm:
            return True
            
        success = True
        for lock in self.locks:
            # Check if door is open first
            door_sensor = self.door_sensors.get(lock)
            if door_sensor:
                door_state = self.get_entity_state(door_sensor)
                if door_state == "on":  # Door open
                    _LOGGER.warning(
                        "Lock module: Cannot lock %s - door is open",
                        lock
                    )
                    continue
                    
            # Try to lock with retry
            if not await self._lock_with_retry(lock):
                success = False
                
        return success
        
    async def async_disarm(self) -> bool:
        """Unlock doors when disarming (with retry)."""
        if not self.enabled or not self.unlock_on_disarm:
            return True
            
        success = True
        for lock in self.locks:
            if not await self._unlock_with_retry(lock):
                success = False
                
        return success
        
    async def async_trigger(self) -> bool:
        """No action on trigger (doors already locked)."""
        return True
        
    async def async_test(self) -> dict[str, Any]:
        """Test lock module functionality.
        
        Tests:
        - Lock availability
        - Lock state
        - Battery levels
        - Door sensor states
        - Lock/unlock operation
        """
        results = {
            "success": True,
            "message": "Lock module test passed",
            "details": {
                "locks": [],
                "total_locks": len(self.locks),
                "all_locked": True,
            }
        }
        
        for lock in self.locks:
            lock_info = {
                "entity_id": lock,
                "available": False,
                "state": None,
                "battery": None,
                "door_sensor": None,
                "test_passed": False,
            }
            
            # Check availability
            lock_info["available"] = self.is_entity_available(lock)
            lock_info["state"] = self.get_entity_state(lock)
            
            if not lock_info["available"]:
                results["success"] = False
                results["message"] = f"Lock {lock} unavailable"
                
            # Check battery
            battery_sensor = self.battery_sensors.get(lock)
            if battery_sensor:
                battery_state = self.get_entity_state(battery_sensor)
                if battery_state:
                    try:
                        lock_info["battery"] = int(float(battery_state))
                        if lock_info["battery"] < 20:
                            results["message"] = f"Lock {lock} battery low ({lock_info['battery']}%)"
                    except (ValueError, TypeError):
                        pass
                        
            # Check door sensor
            door_sensor = self.door_sensors.get(lock)
            if door_sensor:
                lock_info["door_sensor"] = {
                    "entity_id": door_sensor,
                    "state": self.get_entity_state(door_sensor),
                }
                
            # Test lock operation (if currently unlocked)
            if lock_info["state"] == "unlocked":
                # Lock it
                success = await self._lock_with_retry(lock)
                await asyncio.sleep(2)
                
                # Check if locked
                new_state = self.get_entity_state(lock)
                if new_state == "locked":
                    lock_info["test_passed"] = True
                    # Unlock back
                    await self._unlock_with_retry(lock)
                else:
                    lock_info["test_passed"] = False
                    results["success"] = False
                    results["message"] = f"Lock {lock} failed to lock"
            elif lock_info["state"] == "locked":
                # Already locked - just note it
                lock_info["test_passed"] = True
                results["details"]["all_locked"] = True
            else:
                results["details"]["all_locked"] = False
                
            results["details"]["locks"].append(lock_info)
            
        return results
        
    async def _lock_with_retry(self, lock: str) -> bool:
        """Lock a door with retry logic.
        
        Args:
            lock: Lock entity ID
            
        Returns:
            True if locked successfully, False otherwise
        """
        for attempt in range(1, self.max_retries + 1):
            _LOGGER.debug("Locking %s (attempt %d/%d)", lock, attempt, self.max_retries)
            
            # Send lock command
            success = await self.async_call_service(
                "lock",
                "lock",
                target={"entity_id": lock}
            )
            
            if not success:
                await asyncio.sleep(self.retry_delay)
                continue
                
            # Wait for lock to complete
            await asyncio.sleep(self.retry_delay)
            
            # Check if locked
            state = self.get_entity_state(lock)
            if state == "locked":
                _LOGGER.info("Lock module: %s locked successfully", lock)
                return True
                
            # Not locked yet, try again
            await asyncio.sleep(self.retry_delay)
            
        _LOGGER.error("Lock module: Failed to lock %s after %d attempts", lock, self.max_retries)
        return False
        
    async def _unlock_with_retry(self, lock: str) -> bool:
        """Unlock a door with retry logic.
        
        Args:
            lock: Lock entity ID
            
        Returns:
            True if unlocked successfully, False otherwise
        """
        for attempt in range(1, self.max_retries + 1):
            _LOGGER.debug("Unlocking %s (attempt %d/%d)", lock, attempt, self.max_retries)
            
            # Send unlock command
            success = await self.async_call_service(
                "lock",
                "unlock",
                target={"entity_id": lock}
            )
            
            if not success:
                await asyncio.sleep(self.retry_delay)
                continue
                
            # Wait for unlock to complete
            await asyncio.sleep(self.retry_delay)
            
            # Check if unlocked
            state = self.get_entity_state(lock)
            if state == "unlocked":
                _LOGGER.info("Lock module: %s unlocked successfully", lock)
                return True
                
            # Not unlocked yet, try again
            await asyncio.sleep(self.retry_delay)
            
        _LOGGER.error("Lock module: Failed to unlock %s after %d attempts", lock, self.max_retries)
        return False
