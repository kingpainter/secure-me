"""Tests for Secure Me ws_modules.py -- module health status classification."""
# VERSION = "1.5.0"

from unittest.mock import MagicMock

from custom_components.secure_me.ws_modules import _classify_module_status


class FakeModule:
    """Minimal stand-in with just the attributes _classify_module_status reads."""

    def __init__(self, enabled=True, degraded=False):
        self.enabled = enabled
        self.degraded = degraded


class TestClassifyModuleStatus:
    """Regression tests for the health-summary status classification.

    Previously the health summary sent 'problem' for a module with
    unavailable entities -- a value the frontend's label map does not
    recognize, so it silently fell back to a grey 'unknown' badge showing the
    raw string 'problem' instead of a red error badge. The `degraded`
    property (base.py's retry/failure tracking, fully implemented and
    unit-tested in test_base_module.py) was also never read here at all,
    despite the frontend already having CSS and a label ready for it.
    """

    def test_disabled_module_status(self):
        mod = FakeModule(enabled=False)
        assert _classify_module_status(mod, unavail=[]) == "disabled"

    def test_disabled_takes_precedence_over_degraded(self):
        mod = FakeModule(enabled=False, degraded=True)
        assert _classify_module_status(mod, unavail=["lock.front"]) == "disabled"

    def test_degraded_module_status(self):
        """Regression: base.py's degraded property used to be read nowhere."""
        mod = FakeModule(enabled=True, degraded=True)
        assert _classify_module_status(mod, unavail=[]) == "degraded"

    def test_degraded_takes_precedence_over_unavailable_entities(self):
        mod = FakeModule(enabled=True, degraded=True)
        assert _classify_module_status(mod, unavail=["lock.front"]) == "degraded"

    def test_unavailable_entities_status_is_error_not_problem(self):
        """Regression: this used to return 'problem', which the frontend's
        label map doesn't recognize (falls back to a grey 'unknown' badge)."""
        mod = FakeModule(enabled=True, degraded=False)
        assert _classify_module_status(mod, unavail=["lock.front"]) == "error"

    def test_healthy_module_status(self):
        mod = FakeModule(enabled=True, degraded=False)
        assert _classify_module_status(mod, unavail=[]) == "ok"

    def test_module_without_degraded_attribute_does_not_crash(self):
        """Defensive getattr default must handle modules without a real
        degraded attribute (e.g. loosely-specced mocks in other tests)."""
        mod = MagicMock(spec=["enabled"])
        mod.enabled = True
        assert _classify_module_status(mod, unavail=[]) == "ok"
