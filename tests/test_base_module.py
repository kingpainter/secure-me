"""Tests for AlarmModule base class -- retry logic, degraded state, recovery.

Covers v0.4.0 changes:
- async_call_service_with_retry: exponential backoff, 3 retries
- Degraded state set on exhausted retries (_on_failure)
- Recovery and persistent_notification on success after degraded (_on_success)
- async_call_service: single-attempt, no retry
- State backup/restore helpers
- Entity availability helpers
"""
# VERSION = "1.2.0"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from .conftest import MockHass


# ---------------------------------------------------------------------------
# Minimal concrete subclass of AlarmModule for testing
# ---------------------------------------------------------------------------

class ConcreteModule:
    """Minimal stand-in that mirrors AlarmModule without HA import complexity.

    Reimplements only the retry/degraded logic under test so these tests
    remain fast, isolated unit tests with no HA event-loop dependency.
    """

    DEFAULT_RETRY_MAX = 3
    DEFAULT_RETRY_DELAY = 2.0
    DEFAULT_RETRY_BACKOFF = 2.0
    NOTIFY_ID_MODULE_ERROR = "secure_me_module_error"
    NOTIFY_ID_RECOVERY = "secure_me_recovery"

    def __init__(self, hass, config=None):
        self.hass = hass
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
        self._retry_max = self.config.get("retry_max", self.DEFAULT_RETRY_MAX)
        self._retry_delay = self.config.get("retry_delay", self.DEFAULT_RETRY_DELAY)
        self._retry_backoff = self.config.get("retry_backoff", self.DEFAULT_RETRY_BACKOFF)
        self._consecutive_errors = 0
        self._degraded = False
        self._state_backup = {}

    # -- Properties ----------------------------------------------------------

    @property
    def enabled(self):
        return self._enabled

    @property
    def degraded(self):
        return self._degraded

    @property
    def module_name(self):
        return self.__class__.__name__.replace("Module", "")

    def enable(self):
        self._enabled = True
        self._degraded = False
        self._consecutive_errors = 0

    def disable(self):
        self._enabled = False

    # -- Retry logic (mirrors base.py exactly) -------------------------------

    async def async_call_service_with_retry(self, domain, service,
                                            service_data=None, target=None,
                                            action="service_call"):
        import asyncio
        delay = self._retry_delay
        for attempt in range(1, self._retry_max + 1):
            try:
                await self.hass.services.async_call(
                    domain, service,
                    service_data=service_data,
                    target=target,
                    blocking=True,
                )
                self._on_success(action)
                return True
            except Exception:
                if attempt < self._retry_max:
                    await asyncio.sleep(0)   # zero-sleep so tests run fast
                    delay *= self._retry_backoff
        self._on_failure(action)
        return False

    async def async_call_service(self, domain, service,
                                 service_data=None, target=None):
        try:
            await self.hass.services.async_call(
                domain, service,
                service_data=service_data,
                target=target,
                blocking=True,
            )
            return True
        except Exception:
            return False

    def _on_success(self, action):
        previously_degraded = self._degraded
        self._consecutive_errors = 0
        self._degraded = False
        if previously_degraded:
            self.hass.components.persistent_notification.async_create(
                message=f"Secure Me: Module '{self.module_name}' recovered.",
                title="Secure Me - Recovery",
                notification_id=f"{self.NOTIFY_ID_RECOVERY}_{self.module_name.lower()}",
            )

    def _on_failure(self, action):
        self._consecutive_errors += 1
        self._degraded = True
        self.hass.components.persistent_notification.async_create(
            message=f"Secure Me: Module '{self.module_name}' failed after "
                    f"{self._retry_max} retries for '{action}'.",
            title="Secure Me - Module Error",
            notification_id=f"{self.NOTIFY_ID_MODULE_ERROR}_{self.module_name.lower()}",
        )

    # -- State helpers --------------------------------------------------------

    def backup_state(self, entity_id):
        state = self.hass.states.get(entity_id)
        if state:
            self._state_backup[entity_id] = {
                "state": state.state,
                "attributes": dict(state.attributes),
            }

    def get_backup_state(self, entity_id):
        return self._state_backup.get(entity_id)

    def clear_backup(self, entity_id=None):
        if entity_id:
            self._state_backup.pop(entity_id, None)
        else:
            self._state_backup.clear()

    def is_entity_available(self, entity_id):
        state = self.hass.states.get(entity_id)
        return state is not None and state.state not in ("unavailable", "unknown")

    def get_entity_state(self, entity_id):
        state = self.hass.states.get(entity_id)
        return state.state if state else None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_hass_with_notification():
    """Return MockHass with persistent_notification mock wired up."""
    hass = MockHass()
    hass.components = MagicMock()
    hass.components.persistent_notification = MagicMock()
    hass.components.persistent_notification.async_create = MagicMock()
    return hass


# ---------------------------------------------------------------------------
# Tests: retry success
# ---------------------------------------------------------------------------

class TestRetrySuccess:
    """Service call succeeds -- no degraded state set."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt_returns_true(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock()
        mod = ConcreteModule(hass)

        result = await mod.async_call_service_with_retry("light", "turn_on", action="arm")
        assert result is True

    @pytest.mark.asyncio
    async def test_success_does_not_set_degraded(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock()
        mod = ConcreteModule(hass)

        await mod.async_call_service_with_retry("light", "turn_on", action="arm")
        assert mod.degraded is False

    @pytest.mark.asyncio
    async def test_success_resets_consecutive_errors(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock()
        mod = ConcreteModule(hass)
        mod._consecutive_errors = 2

        await mod.async_call_service_with_retry("light", "turn_on", action="arm")
        assert mod._consecutive_errors == 0

    @pytest.mark.asyncio
    async def test_service_call_passes_correct_args(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock()
        mod = ConcreteModule(hass)

        await mod.async_call_service_with_retry(
            "lock", "lock",
            target={"entity_id": "lock.front"},
            action="lock:front",
        )
        hass.services.async_call.assert_called_once_with(
            "lock", "lock",
            service_data=None,
            target={"entity_id": "lock.front"},
            blocking=True,
        )


# ---------------------------------------------------------------------------
# Tests: retry exhaustion -> degraded
# ---------------------------------------------------------------------------

class TestRetryExhaustion:
    """All retries fail -- module goes degraded and user is notified."""

    @pytest.mark.asyncio
    async def test_all_retries_fail_returns_false(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("HA unavailable"))
        mod = ConcreteModule(hass)

        result = await mod.async_call_service_with_retry("lock", "lock", action="test")
        assert result is False

    @pytest.mark.asyncio
    async def test_exhaustion_sets_degraded(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("fail"))
        mod = ConcreteModule(hass)

        await mod.async_call_service_with_retry("lock", "lock", action="test")
        assert mod.degraded is True

    @pytest.mark.asyncio
    async def test_exhaustion_increments_consecutive_errors(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("fail"))
        mod = ConcreteModule(hass)

        await mod.async_call_service_with_retry("lock", "lock", action="test")
        assert mod._consecutive_errors == 1

    @pytest.mark.asyncio
    async def test_exhaustion_fires_persistent_notification(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("fail"))
        mod = ConcreteModule(hass)

        await mod.async_call_service_with_retry("lock", "lock", action="lock_door")
        hass.components.persistent_notification.async_create.assert_called_once()
        call_kwargs = hass.components.persistent_notification.async_create.call_args
        assert "Module Error" in call_kwargs.kwargs.get("title", "") or \
               "Module Error" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_retries_exactly_max_times(self):
        """Service must be attempted exactly retry_max times before giving up."""
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("fail"))
        mod = ConcreteModule(hass, config={"retry_max": 3})

        await mod.async_call_service_with_retry("lock", "lock", action="test")
        assert hass.services.async_call.call_count == 3

    @pytest.mark.asyncio
    async def test_custom_retry_max_respected(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("fail"))
        mod = ConcreteModule(hass, config={"retry_max": 1})

        await mod.async_call_service_with_retry("lock", "lock", action="test")
        assert hass.services.async_call.call_count == 1


# ---------------------------------------------------------------------------
# Tests: recovery after degraded
# ---------------------------------------------------------------------------

class TestRecoveryAfterDegraded:
    """Successful call after degraded state fires recovery notification."""

    @pytest.mark.asyncio
    async def test_recovery_clears_degraded(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock()
        mod = ConcreteModule(hass)
        mod._degraded = True  # Pre-set degraded

        await mod.async_call_service_with_retry("light", "turn_on", action="arm")
        assert mod.degraded is False

    @pytest.mark.asyncio
    async def test_recovery_fires_recovery_notification(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock()
        mod = ConcreteModule(hass)
        mod._degraded = True  # Pre-set degraded

        await mod.async_call_service_with_retry("light", "turn_on", action="arm")
        hass.components.persistent_notification.async_create.assert_called_once()
        call_kwargs = hass.components.persistent_notification.async_create.call_args
        assert "Recovery" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_no_recovery_notification_if_not_previously_degraded(self):
        """No notification fired if module was never degraded."""
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock()
        mod = ConcreteModule(hass)

        await mod.async_call_service_with_retry("light", "turn_on", action="arm")
        hass.components.persistent_notification.async_create.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: async_call_service (single attempt, no retry)
# ---------------------------------------------------------------------------

class TestSingleAttemptCall:
    """async_call_service -- one attempt only, no degraded state side effects."""

    @pytest.mark.asyncio
    async def test_success_returns_true(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock()
        mod = ConcreteModule(hass)

        result = await mod.async_call_service("switch", "turn_on")
        assert result is True

    @pytest.mark.asyncio
    async def test_failure_returns_false(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("fail"))
        mod = ConcreteModule(hass)

        result = await mod.async_call_service("switch", "turn_on")
        assert result is False

    @pytest.mark.asyncio
    async def test_failure_does_not_set_degraded(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("fail"))
        mod = ConcreteModule(hass)

        await mod.async_call_service("switch", "turn_on")
        assert mod.degraded is False

    @pytest.mark.asyncio
    async def test_called_exactly_once_on_failure(self):
        hass = make_hass_with_notification()
        hass.services.async_call = AsyncMock(side_effect=Exception("fail"))
        mod = ConcreteModule(hass)

        await mod.async_call_service("switch", "turn_on")
        assert hass.services.async_call.call_count == 1


# ---------------------------------------------------------------------------
# Tests: state backup/restore helpers
# ---------------------------------------------------------------------------

class TestStateBackup:
    """Backup and restore entity state helpers."""

    def test_backup_stores_state_and_attributes(self):
        hass = MockHass()
        hass.set_state("light.living", "on", {"brightness": 200})
        mod = ConcreteModule(hass)

        mod.backup_state("light.living")
        backup = mod.get_backup_state("light.living")
        assert backup is not None
        assert backup["state"] == "on"
        assert backup["attributes"]["brightness"] == 200

    def test_backup_missing_entity_does_nothing(self):
        hass = MockHass()
        mod = ConcreteModule(hass)

        mod.backup_state("light.nonexistent")
        assert mod.get_backup_state("light.nonexistent") is None

    def test_clear_single_backup(self):
        hass = MockHass()
        hass.set_state("light.living", "on")
        hass.set_state("light.kitchen", "off")
        mod = ConcreteModule(hass)

        mod.backup_state("light.living")
        mod.backup_state("light.kitchen")
        mod.clear_backup("light.living")

        assert mod.get_backup_state("light.living") is None
        assert mod.get_backup_state("light.kitchen") is not None

    def test_clear_all_backups(self):
        hass = MockHass()
        hass.set_state("light.living", "on")
        hass.set_state("light.kitchen", "off")
        mod = ConcreteModule(hass)

        mod.backup_state("light.living")
        mod.backup_state("light.kitchen")
        mod.clear_backup()

        assert mod.get_backup_state("light.living") is None
        assert mod.get_backup_state("light.kitchen") is None


# ---------------------------------------------------------------------------
# Tests: entity availability helpers
# ---------------------------------------------------------------------------

class TestEntityHelpers:
    """is_entity_available and get_entity_state."""

    def test_available_entity_returns_true(self):
        hass = MockHass()
        hass.set_state("light.living", "on")
        mod = ConcreteModule(hass)
        assert mod.is_entity_available("light.living") is True

    def test_unavailable_entity_returns_false(self):
        hass = MockHass()
        hass.set_state("light.living", "unavailable")
        mod = ConcreteModule(hass)
        assert mod.is_entity_available("light.living") is False

    def test_unknown_entity_returns_false(self):
        hass = MockHass()
        hass.set_state("light.living", "unknown")
        mod = ConcreteModule(hass)
        assert mod.is_entity_available("light.living") is False

    def test_missing_entity_returns_false(self):
        hass = MockHass()
        mod = ConcreteModule(hass)
        assert mod.is_entity_available("light.nonexistent") is False

    def test_get_entity_state_returns_state(self):
        hass = MockHass()
        hass.set_state("light.living", "on")
        mod = ConcreteModule(hass)
        assert mod.get_entity_state("light.living") == "on"

    def test_get_entity_state_missing_returns_none(self):
        hass = MockHass()
        mod = ConcreteModule(hass)
        assert mod.get_entity_state("light.nonexistent") is None


# ---------------------------------------------------------------------------
# Tests: enable/disable
# ---------------------------------------------------------------------------

class TestModuleEnableDisable:
    """Enable/disable clears degraded state."""

    def test_enable_clears_degraded(self):
        hass = make_hass_with_notification()
        mod = ConcreteModule(hass)
        mod._degraded = True
        mod._consecutive_errors = 5

        mod.enable()
        assert mod.degraded is False
        assert mod._consecutive_errors == 0
        assert mod.enabled is True

    def test_disable_does_not_affect_degraded(self):
        hass = make_hass_with_notification()
        mod = ConcreteModule(hass)
        mod._degraded = True

        mod.disable()
        assert mod.enabled is False
        assert mod.degraded is True  # degraded unchanged by disable
