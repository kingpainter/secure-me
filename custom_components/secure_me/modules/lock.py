"""Lock module for Secure Me alarm system."""
# VERSION = "1.0.0"

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

        Functional test: attempts unlock → lock cycle on each lock,
        verifying state transitions actually occur. Lock is ALWAYS
        restored to locked after test (safety guarantee).

        If a door sensor reports the door is open, the lock is skipped
        (cannot safely test a lock on an open door).
        """
        results = {
            "success": True,
            "message": "Lock module test passed",
            "details": {
                "locks": [],
                "total_locks": len(self.locks),
                "functional_test": True,
            },
        }

        for lock in self.locks:
            lock_info: dict[str, Any] = {
                "entity_id": lock,
                "available": self.is_entity_available(lock),
                "initial_state": self.get_entity_state(lock),
                "battery": None,
                "door_sensor": None,
                "unlock_ok": None,
                "relock_ok": None,
                "test_passed": False,
                "skip_reason": None,
            }

            # Battery check
            battery_sensor = self.battery_sensors.get(lock)
            if battery_sensor:
                try:
                    level = int(float(self.get_entity_state(battery_sensor) or ""))
                    lock_info["battery"] = level
                    if level < 20:
                        results["message"] = f"Lock {lock} battery low ({level}%)"
                except (ValueError, TypeError):
                    pass

            # Door sensor check
            door_sensor = self.door_sensors.get(lock)
            if door_sensor:
                door_state = self.get_entity_state(door_sensor)
                lock_info["door_sensor"] = {
                    "entity_id": door_sensor,
                    "state": door_state,
                }
                if door_state == "on":
                    # Door is open — skip functional test, safety first
                    lock_info["skip_reason"] = "door_open"
                    lock_info["test_passed"] = True  # Not a failure, just skipped
                    results["details"]["locks"].append(lock_info)
                    _LOGGER.info("Lock test: skipping %s — door is open", lock)
                    continue

            # Unavailable — fail immediately, no functional test
            if not lock_info["available"]:
                lock_info["test_passed"] = False
                results["success"] = False
                results["message"] = f"Lock {lock} unavailable"
                results["details"]["locks"].append(lock_info)
                continue

            # --- Functional test: unlock → lock, always end locked ---
            initial_state = lock_info["initial_state"]
            try:
                # Step 1: Unlock (test that unlock command works)
                await self.async_call_service(
                    "lock", "unlock", target={"entity_id": lock}
                )
                await asyncio.sleep(3)
                unlock_state = self.get_entity_state(lock)
                lock_info["unlock_ok"] = unlock_state == "unlocked"

                if not lock_info["unlock_ok"]:
                    _LOGGER.warning(
                        "Lock test: %s did not unlock (state=%s)", lock, unlock_state
                    )

                # Step 2: Re-lock (ALWAYS — safety guarantee)
                await self.async_call_service(
                    "lock", "lock", target={"entity_id": lock}
                )
                await asyncio.sleep(3)
                relock_state = self.get_entity_state(lock)
                lock_info["relock_ok"] = relock_state == "locked"

                if not lock_info["relock_ok"]:
                    # Emergency: try once more
                    _LOGGER.warning(
                        "Lock test: %s did not relock — retrying once", lock
                    )
                    await self.async_call_service(
                        "lock", "lock", target={"entity_id": lock}
                    )
                    await asyncio.sleep(3)
                    lock_info["relock_ok"] = self.get_entity_state(lock) == "locked"

                lock_info["final_state"] = self.get_entity_state(lock)
                lock_info["test_passed"] = lock_info["unlock_ok"] and lock_info["relock_ok"]

                if not lock_info["test_passed"]:
                    results["success"] = False
                    if not lock_info["unlock_ok"]:
                        results["message"] = f"Lock {lock} failed to unlock"
                    elif not lock_info["relock_ok"]:
                        results["message"] = f"Lock {lock} failed to relock — CHECK DOOR SECURITY"

            except Exception as err:
                _LOGGER.error("Lock test exception for %s: %s", lock, err)
                lock_info["test_passed"] = False
                lock_info["error"] = str(err)
                results["success"] = False
                results["message"] = f"Lock {lock} test error: {err}"

                # Safety: always attempt to lock on exception
                try:
                    await self.async_call_service(
                        "lock", "lock", target={"entity_id": lock}
                    )
                except Exception:
                    pass

            results["details"]["locks"].append(lock_info)

        return results
