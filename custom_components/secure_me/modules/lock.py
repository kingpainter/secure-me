"""Lock module for Secure Me alarm system."""
# VERSION = "1.5.1"

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
        """Test lock module functionality.

        Always leaves the lock in the "locked" state when the test completes,
        regardless of which state it started in:
        - Starts locked: unlock -> verify -> relock -> verify (both directions tested).
        - Starts unlocked: lock -> verify (ends locked, matching a real arm cycle).
        - Door sensor reports open: functional test is skipped entirely (locking an
          open door proves nothing and risks spurious retry/degraded notifications).
        """
        results = {
            "success": True,
            "message": "Lock module test passed",
            "details": {
                "locks": [],
                "total_locks": len(self.locks),
                "all_locked": True,
            },
        }
        # Collected instead of overwriting results["message"] each time -- with
        # more than one lock, only the LAST problem used to survive in the
        # summary, silently hiding earlier ones (details per-lock were always
        # correct, but the one-line summary was misleading).
        messages: list[str] = []

        for lock in self.locks:
            initial_state = self.get_entity_state(lock)
            lock_info: dict[str, Any] = {
                "entity_id": lock,
                "available": self.is_entity_available(lock),
                "initial_state": initial_state,
                "battery": None,
                "door_sensor": None,
                "unlock_ok": None,
                "relock_ok": None,
                "test_passed": False,
                "skip_reason": None,
            }

            if not lock_info["available"]:
                results["success"] = False
                messages.append(f"Lock {lock} unavailable")
                results["details"]["all_locked"] = False
                results["details"]["locks"].append(lock_info)
                continue

            # Battery (informational only -- does not affect pass/fail)
            battery_sensor = self.battery_sensors.get(lock)
            if battery_sensor:
                try:
                    level = int(float(self.get_entity_state(battery_sensor) or ""))
                    lock_info["battery"] = level
                    if level < 20:
                        messages.append(f"Lock {lock} battery low ({level}%)")
                except (ValueError, TypeError):
                    pass

            # Door sensor: skip the functional test if the door is open
            door_sensor = self.door_sensors.get(lock)
            if door_sensor:
                door_state = self.get_entity_state(door_sensor)
                lock_info["door_sensor"] = {"entity_id": door_sensor, "state": door_state}
                if door_state == "on":
                    lock_info["skip_reason"] = "door_open"
                    lock_info["test_passed"] = True
                    results["details"]["locks"].append(lock_info)
                    continue

            try:
                if initial_state == "locked":
                    # Test both directions, always end locked.
                    await self.async_call_service("lock", "unlock", target={"entity_id": lock})
                    await asyncio.sleep(2)
                    lock_info["unlock_ok"] = self.get_entity_state(lock) == "unlocked"

                    await self.async_call_service("lock", "lock", target={"entity_id": lock})
                    await asyncio.sleep(2)
                    lock_info["relock_ok"] = self.get_entity_state(lock) == "locked"

                    lock_info["test_passed"] = lock_info["unlock_ok"] and lock_info["relock_ok"]
                    if not lock_info["test_passed"]:
                        results["success"] = False
                        messages.append(f"Lock {lock} failed unlock/relock cycle")
                else:
                    # Unlocked (or any other non-locked state): lock and verify.
                    await self.async_call_service("lock", "lock", target={"entity_id": lock})
                    await asyncio.sleep(2)
                    lock_info["relock_ok"] = self.get_entity_state(lock) == "locked"
                    lock_info["test_passed"] = lock_info["relock_ok"]
                    if not lock_info["test_passed"]:
                        results["success"] = False
                        messages.append(f"Lock {lock} failed to lock")
            except Exception as err:
                lock_info["test_passed"] = False
                lock_info["error"] = str(err)
                results["success"] = False
                messages.append(f"Lock {lock} test error: {err}")

            lock_info["final_state"] = self.get_entity_state(lock)
            if lock_info["final_state"] != "locked":
                results["details"]["all_locked"] = False

            results["details"]["locks"].append(lock_info)

        if messages:
            results["message"] = "; ".join(messages)

        return results
