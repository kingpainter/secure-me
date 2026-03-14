"""Tests for Secure Me diagnostics."""
# VERSION = "1.0.0"

import pytest

from custom_components.secure_me.const import CONF_CODE, VERSION


class TestDiagnosticsRedaction:
    """Test that sensitive data is properly identified for redaction."""

    def test_code_in_redact_list(self):
        from custom_components.secure_me.diagnostics import TO_REDACT
        assert CONF_CODE in TO_REDACT
        assert "code" in TO_REDACT

    def test_password_in_redact_list(self):
        from custom_components.secure_me.diagnostics import TO_REDACT
        assert "password" in TO_REDACT

    def test_pin_in_redact_list(self):
        from custom_components.secure_me.diagnostics import TO_REDACT
        assert "pin" in TO_REDACT

    def test_nfc_tag_in_redact_list(self):
        from custom_components.secure_me.diagnostics import TO_REDACT
        assert "nfc_tag_id" in TO_REDACT


class TestDiagnosticsVersion:
    """Test diagnostics includes version info."""

    def test_version_matches_const(self):
        assert VERSION == "1.0.0"
