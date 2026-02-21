"""Tests for Secure Me file integrity – manifest, services, strings."""
# VERSION = "0.9.0"

import json
import os
import pytest


# Path to the integration root
INTEGRATION_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "custom_components",
    "secure_me"
)

# Path to repo root
REPO_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
)


class TestManifest:
    """Test manifest.json validity."""

    def test_manifest_exists(self):
        path = os.path.join(INTEGRATION_DIR, "manifest.json")
        assert os.path.isfile(path), "manifest.json not found"

    def test_manifest_is_valid_json(self):
        path = os.path.join(INTEGRATION_DIR, "manifest.json")
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_manifest_required_keys(self):
        path = os.path.join(INTEGRATION_DIR, "manifest.json")
        with open(path) as f:
            data = json.load(f)
        required = {"domain", "name", "version", "documentation", "codeowners"}
        assert required.issubset(set(data.keys()))

    def test_manifest_domain(self):
        path = os.path.join(INTEGRATION_DIR, "manifest.json")
        with open(path) as f:
            data = json.load(f)
        assert data["domain"] == "secure_me"

    def test_manifest_version_matches_const(self):
        path = os.path.join(INTEGRATION_DIR, "manifest.json")
        with open(path) as f:
            data = json.load(f)
        from custom_components.secure_me.const import VERSION
        assert data["version"] == VERSION


class TestServicesYaml:
    """Test services.yaml exists and has expected services."""

    def test_services_file_exists(self):
        path = os.path.join(INTEGRATION_DIR, "services.yaml")
        assert os.path.isfile(path), "services.yaml not found"

    def test_services_file_not_empty(self):
        path = os.path.join(INTEGRATION_DIR, "services.yaml")
        assert os.path.getsize(path) > 100


class TestStringsJson:
    """Test strings.json validity."""

    def test_strings_exists(self):
        path = os.path.join(INTEGRATION_DIR, "strings.json")
        assert os.path.isfile(path), "strings.json not found"

    def test_strings_is_valid_json(self):
        path = os.path.join(INTEGRATION_DIR, "strings.json")
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_strings_has_config_section(self):
        path = os.path.join(INTEGRATION_DIR, "strings.json")
        with open(path) as f:
            data = json.load(f)
        assert "config" in data

    def test_strings_has_entity_section(self):
        path = os.path.join(INTEGRATION_DIR, "strings.json")
        with open(path) as f:
            data = json.load(f)
        assert "entity" in data


class TestHacsJson:
    """Test hacs.json validity."""

    def test_hacs_exists(self):
        # hacs.json is in repo root, not in custom_components
        path = os.path.join(REPO_ROOT, "hacs.json")
        assert os.path.isfile(path), "hacs.json not found"

    def test_hacs_is_valid_json(self):
        path = os.path.join(REPO_ROOT, "hacs.json")
        with open(path) as f:
            data = json.load(f)
        assert "name" in data
        assert data["name"] == "Secure Me"
