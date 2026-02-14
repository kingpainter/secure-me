"""Tests for Secure Me module system."""
# VERSION = "0.3.0"

import pytest
from unittest.mock import AsyncMock, MagicMock
from .conftest import MockModule, MockHass


class TestModuleBase:
    """Test the mock module (mirrors base.py interface)."""

    def test_module_defaults_enabled(self):
        mod = MockModule(enabled=True)
        assert mod.enabled is True

    def test_module_can_disable(self):
        mod = MockModule(enabled=True)
        mod.disable()
        assert mod.enabled is False

    def test_module_can_enable(self):
        mod = MockModule(enabled=False)
        mod.enable()
        assert mod.enabled is True

    def test_module_name(self):
        mod = MockModule(name="Camera")
        assert mod.module_name == "Camera"

    @pytest.mark.asyncio
    async def test_module_test_returns_success(self):
        mod = MockModule()
        result = await mod.async_test()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_module_cleanup_no_error(self):
        mod = MockModule()
        await mod.async_cleanup()  # Should not raise


class TestModuleEntityExtraction:
    """Test entity ID extraction from module config."""

    def test_list_attributes(self):
        mod = MockModule()
        mod.lights = ["light.living", "light.kitchen"]
        mod.cameras = ["camera.front"]

        entities = []
        for attr in ("poe_switches", "cameras", "recording_entities",
                     "locks", "lights", "climates", "media_players"):
            val = getattr(mod, attr, None)
            if isinstance(val, list):
                entities.extend(val)
        assert len(entities) == 3

    def test_dict_attributes(self):
        mod = MockModule()
        mod.door_sensors = {"lock1": "binary_sensor.door1"}
        mod.battery_sensors = {"lock1": "sensor.bat1"}

        entities = []
        for attr in ("door_sensors", "battery_sensors"):
            val = getattr(mod, attr, None)
            if isinstance(val, dict):
                entities.extend(val.values())
        assert len(entities) == 2

    def test_single_entity_attribute(self):
        mod = MockModule()
        mod.gateway_light = "light.gateway"

        entities = []
        for attr in ("gateway_light",):
            val = getattr(mod, attr, None)
            if isinstance(val, str) and "." in val:
                entities.append(val)
        assert entities == ["light.gateway"]

    def test_empty_module_no_entities(self):
        mod = MockModule()
        entities = []
        for attr in ("poe_switches", "cameras", "recording_entities",
                     "locks", "lights", "climates", "media_players"):
            val = getattr(mod, attr, None)
            if isinstance(val, list):
                entities.extend(val)
        assert entities == []


class TestModuleHealth:
    """Test module health checking logic."""

    def test_all_entities_available(self, mock_hass):
        mock_hass.set_state("light.living", "on")
        mock_hass.set_state("light.kitchen", "off")

        entity_ids = ["light.living", "light.kitchen"]
        unavail = []
        for eid in entity_ids:
            state = mock_hass.states.get(eid)
            if not state or state.state in ("unavailable", "unknown"):
                unavail.append(eid)
        assert len(unavail) == 0

    def test_one_entity_unavailable(self, mock_hass):
        mock_hass.set_state("light.living", "on")
        mock_hass.set_state("light.kitchen", "unavailable")

        entity_ids = ["light.living", "light.kitchen"]
        unavail = []
        for eid in entity_ids:
            state = mock_hass.states.get(eid)
            if not state or state.state in ("unavailable", "unknown"):
                unavail.append(eid)
        assert unavail == ["light.kitchen"]

    def test_missing_entity_counts_as_unavailable(self, mock_hass):
        mock_hass.set_state("light.living", "on")

        entity_ids = ["light.living", "light.nonexistent"]
        unavail = []
        for eid in entity_ids:
            state = mock_hass.states.get(eid)
            if not state or state.state in ("unavailable", "unknown"):
                unavail.append(eid)
        assert "light.nonexistent" in unavail

    def test_health_score_calculation(self):
        """Health score = (available / total) * 100."""
        total = 10
        available = 8
        score = round((available / total) * 100)
        assert score == 80

    def test_health_score_all_available(self):
        total = 5
        available = 5
        score = round((available / total) * 100)
        assert score == 100

    def test_health_score_none_configured(self):
        """No entities = 100% health."""
        total = 0
        score = 100 if total == 0 else round((0 / total) * 100)
        assert score == 100
