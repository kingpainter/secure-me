"""Tests for Secure Me diagnostics."""
# VERSION = "1.4.1"

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
        """VERSION constant must match manifest.json (single source of truth)."""
        import json
        from pathlib import Path
        manifest_path = Path(__file__).parent.parent / "custom_components" / "secure_me" / "manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert VERSION == manifest["version"], (
            f"VERSION constant ({VERSION}) does not match manifest.json "
            f"({manifest['version']}). Bump both or run validate_version.py --fix."
        )
