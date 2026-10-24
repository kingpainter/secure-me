"""Tests for code-entry rate limiting (code_attempts.py and coordinator).

The limiter tests use an injected fake clock, so they run without sleeping.
Coordinator tests are built with __new__ to skip HA setup; only the
attributes validate_code() and async_disarm() touch are populated.
"""
# VERSION = "2.2.0"

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from custom_components.secure_me.code_attempts import CodeAttemptLimiter
from custom_components.secure_me.const import EVENT_CODE_LOCKED
from custom_components.secure_me.coordinator import SecureMeCoordinator


class FakeClock:
    """Manually advanced clock for the limiter."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _limiter(clock: FakeClock, max_failures: int = 3) -> CodeAttemptLimiter:
    return CodeAttemptLimiter(
        max_failures=max_failures, window=60.0, lockout=100.0, clock=clock
    )


# ── CodeAttemptLimiter ──────────────────────────────────────────────────────


def test_locks_after_max_failures():
    clock = FakeClock()
    lim = _limiter(clock)
    assert lim.record_result(False) is False
    assert lim.record_result(False) is False
    assert lim.record_result(False) is True  # third failure starts lockout
    assert lim.is_locked()
    assert not lim.allow_attempt()


def test_lock_expires_after_lockout_period():
    clock = FakeClock()
    lim = _limiter(clock)
    for _ in range(3):
        lim.record_result(False)
    clock.now = 99.9
    assert not lim.allow_attempt()
    clock.now = 100.0
    assert lim.allow_attempt()


def test_failures_outside_window_do_not_accumulate():
    clock = FakeClock()
    lim = CodeAttemptLimiter(max_failures=3, window=10.0, lockout=50.0, clock=clock)
    lim.record_result(False)
    lim.record_result(False)
    clock.now = 20.0  # the first two have aged out of the 10 s window
    assert lim.record_result(False) is False
    assert lim.allow_attempt()


def test_success_clears_failure_history():
    clock = FakeClock()
    lim = _limiter(clock)
    lim.record_result(False)
    lim.record_result(False)
    lim.record_result(True)
    assert lim.record_result(False) is False
    assert lim.allow_attempt()


def test_lockout_seconds_is_whole_seconds():
    assert _limiter(FakeClock()).lockout_seconds == 100


# ── SecureMeCoordinator.validate_code ───────────────────────────────────────


def _make_coordinator(code: str = "1234", store_result=None):
    coord = SecureMeCoordinator.__new__(SecureMeCoordinator)
    coord._code = code
    coord.hass = MagicMock()
    coord.store = MagicMock()
    coord.store.authenticate_user.return_value = store_result
    coord.code_limiter = _limiter(FakeClock())
    return coord


def test_wrong_codes_lock_out_even_a_correct_code():
    coord = _make_coordinator(store_result=None)
    for _ in range(3):
        assert coord.validate_code("0000") is False
    # Locked: the store is not consulted at all on further attempts.
    coord.store.authenticate_user.return_value = {"name": "Flemming"}
    calls_before = coord.store.authenticate_user.call_count
    assert coord.validate_code("1234") is False
    assert coord.store.authenticate_user.call_count == calls_before


def test_lockout_announced_once():
    coord = _make_coordinator(store_result=None)
    for _ in range(3):
        coord.validate_code("0000")
    coord.validate_code("0000")  # refused, must not announce again
    fired = [c for c in coord.hass.bus.async_fire.call_args_list]
    assert len(fired) == 1
    assert fired[0][0][0] == EVENT_CODE_LOCKED


def test_success_before_lockout_resets_count():
    coord = _make_coordinator(store_result=None)
    coord.validate_code("0000")
    coord.validate_code("0000")
    coord.store.authenticate_user.return_value = {"name": "Flemming"}
    assert coord.validate_code("1234") is True
    coord.store.authenticate_user.return_value = None
    coord.validate_code("0000")
    coord.validate_code("0000")
    assert coord.code_limiter.allow_attempt()


def test_empty_code_is_not_counted():
    coord = _make_coordinator(store_result=None)
    for _ in range(10):
        assert coord.validate_code(None) is False
    assert coord.code_limiter.allow_attempt()
    coord.store.authenticate_user.assert_not_called()


def test_no_global_code_skips_limiter_entirely():
    coord = _make_coordinator(code="")
    for _ in range(10):
        assert coord.validate_code("anything") is True
    assert coord.code_limiter.allow_attempt()


# ── async_disarm: lockout vs. trusted tags ──────────────────────────────────


def _make_disarm_coordinator(locked: bool):
    coord = _make_coordinator(store_result=None)
    if locked:
        for _ in range(3):
            coord.code_limiter.record_result(False)
    coord.state_machine = MagicMock(is_pending=False)
    coord.state_machine.disarm = AsyncMock(return_value=True)
    coord.zone_manager = MagicMock()
    coord._execute_modules_disarm = AsyncMock()
    coord.async_request_refresh = AsyncMock()
    return coord


async def test_locked_out_code_disarm_is_refused():
    coord = _make_disarm_coordinator(locked=True)

    result = await coord.async_disarm(code="1234")

    assert result is False
    coord.state_machine.disarm.assert_not_called()


async def test_skip_code_disarm_is_not_affected_by_lockout():
    coord = _make_disarm_coordinator(locked=True)

    result = await coord.async_disarm(code=None, skip_code=True)

    assert result is True
    coord.state_machine.disarm.assert_awaited_once()
