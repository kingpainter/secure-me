"""Lock module for Secure Me alarm system."""
# VERSION = "0.9.0"

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .base import AlarmModule

_LOGGER = logging.getLogger(__name__)


class LockModule(AlarmModule):
    """Smart lock control module.

    Uses base class retry logic (async_call_service_with_retry) for all
    lock/unlock operations instead of custom retry code.
    """

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize lock module.

        Config options:
            - locks: List of lock entity IDs
            - door_sensors: Dict mapping lock -> door sensor entity ID
            - battery_sensors: Dict mapping lock -> battery sensor entity ID
            - lock_on_arm: Lock doors when arming (default: True)
            - unlock_on_disarm: Unlock doors when disarming (default: False)
            - retry_max / retry_delay / retry_backoff: Override base defaults
        """
        super().__init__(hass, config)

        self.locks = config.get("locks", [])
        self.door_sensors = config.get("door_sensors", {})
        self.battery_sensors = config.get("battery_sensors", {})
        self.lock_on_arm = config.get("lock_on_arm", True)
        self.unlock_on_disarm = config.get("unlock_on_disarm", False)

    async def async_arm(self, mode: str) -> bool:
        """Lock doors when arming."""
        if not self.enabled or not self.lock_on_arm:
            return True

        success = True
        for lock in self.locks:
            # Skip if door is open
            door_sensor = self.door_sensors.get(lock)
            if door_sensor and self.get_entity_state(door_sensor) == "on":
                _LOGGER.warning("Lock module: Cannot lock %s - door is open", lock)
                continue

            if not await self.async_call_service_with_retry(
                "lock", "lock",
                target={"entity_id": lock},
                action=f"lock:{lock}",
            ):
                success = False

        return success

    async def async_disarm(self) -> bool:
        """Unlock doors when disarming."""
        if not self.enabled or not self.unlock_on_disarm:
            return True

        success = True
        for lock in self.locks:
            if not await self.async_call_service_with_retry(
                "lock", "unlock",
                target={"entity_id": lock},
                action=f"unlock:{lock}",
            ):
                success = False

        return success

    async def async_trigger(self) -> bool:
        """No action on trigger (doors stay locked)."""
        return True

    async def async_test(self) -> dict[str, Any]:
        """Test lock module functionality."""
        results = {
            "success": True,
            "message": "Lock module test passed",
            "details": {
                "locks": [],
                "total_locks": len(self.locks),
                "all_locked": True,
            },
        }

        for lock in self.locks:
            lock_info: dict[str, Any] = {
                "entity_id": lock,
                "available": self.is_entity_available(lock),
                "state": self.get_entity_state(lock),
                "battery": None,
                "door_sensor": None,
                "test_passed": False,
            }

            if not lock_info["available"]:
                results["success"] = False
                results["message"] = f"Lock {lock} unavailable"

            # Battery
            battery_sensor = self.battery_sensors.get(lock)
            if battery_sensor:
                try:
                    level = int(float(self.get_entity_state(battery_sensor) or ""))
                    lock_info["battery"] = level
                    if level < 20:
                        results["message"] = f"Lock {lock} battery low ({level}%)"
                except (ValueError, TypeError):
                    pass

            # Door sensor
            door_sensor = self.door_sensors.get(lock)
            if door_sensor:
                lock_info["door_sensor"] = {
                    "entity_id": door_sensor,
                    "state": self.get_entity_state(door_sensor),
                }

            # Quick lock/unlock test if currently unlocked
            if lock_info["state"] == "unlocked":
                ok = await self.async_call_service("lock", "lock", target={"entity_id": lock})
                await asyncio.sleep(2)
                if ok and self.get_entity_state(lock) == "locked":
                    lock_info["test_passed"] = True
                    await self.async_call_service("lock", "unlock", target={"entity_id": lock})
                else:
                    results["success"] = False
                    results["message"] = f"Lock {lock} failed to lock"
            elif lock_info["state"] == "locked":
                lock_info["test_passed"] = True

            results["details"]["locks"].append(lock_info)

        return results
