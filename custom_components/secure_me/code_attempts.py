# VERSION = "2.2.0"
"""Failed-code rate limiter for Secure Me.

Pure Python with no Home Assistant imports, so it can be tested offline.

Only failed checks are counted. A successful check clears the failure
history. Once max_failures failures fall inside a window of `window`
seconds, every check is refused for `lockout` seconds.

The limiter is global, not per user: a keypad or remote code check cannot
be tied to a specific user before it succeeds, so there is no key to count
against. Trusted NFC tags that skip the code check never reach the limiter.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class CodeAttemptLimiter:
    """Refuse code checks for a while after repeated failures."""

    def __init__(
        self,
        max_failures: int = 5,
        window: float = 600.0,
        lockout: float = 600.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create a limiter. `clock` is injectable so tests can control time."""
        self._max_failures = max_failures
        self._window = window
        self._lockout = lockout
        self._clock = clock
        self._failures: list[float] = []
        self._locked_until: float = 0.0

    @property
    def lockout_seconds(self) -> int:
        """Length of a lockout in whole seconds."""
        return int(self._lockout)

    def is_locked(self) -> bool:
        """Return True while a lockout is in effect."""
        return self._clock() < self._locked_until

    def allow_attempt(self) -> bool:
        """Return True if a code check may be performed now."""
        return not self.is_locked()

    def record_result(self, ok: bool) -> bool:
        """Record the outcome of a code check.

        Returns True when this failure started a new lockout, so the caller
        can announce it once.
        """
        if ok:
            self._failures.clear()
            return False
        now = self._clock()
        cutoff = now - self._window
        self._failures = [t for t in self._failures if t > cutoff]
        self._failures.append(now)
        if len(self._failures) >= self._max_failures:
            self._locked_until = now + self._lockout
            self._failures.clear()
            return True
        return False
