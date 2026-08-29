"""Tests for module_dispatch.py -- ModuleDispatcher, get_module_entity_ids,
and normalize_module_config.

Extracted from coordinator.py in v1.5.5 (see module_dispatch.py's own
docstring), this file previously had NO dedicated test coverage at all --
it was only exercised indirectly through coordinator-level tests such as
test_coordinator_trigger.py. That left several of its own responsibilities
untested in isolation:

  - get_module_entity_ids(): the exact siren-visibility bug fixed in
    v1.5.5 (siren's `sirens` list of dicts was previously invisible to
    passive health scoring) has no regression test locking it in place.
  - ModuleDispatcher.get_health_score() / get_module_health(): the health
    percentage math and per-module status categorisation (ok/degraded/
    error/disabled) are untested.
  - ModuleDispatcher's arm/disarm/trigger dispatch: fault isolation (one
    module raising must not stop the others) and EVENT_MODULE_ERROR firing
    are untested.
  - Battery cache TTL/invalidation: untested.
  - normalize_module_config(): the per-module-id normalization rules
    (camera poe_switches extraction, lights entities-vs-lights fallback,
    siren pass-through, etc.) are untested.

Per the project's own testing rule (see test_coordinator_trigger.py), these
tests use the REAL ModuleDispatcher and REAL module classes (SirenModule,
CameraModule, etc.) against the real `hass` fixture -- no mirror
re-implementations that could silently drift from production behaviour.
"""
# VERSION = "1.0.0"

import time

import pytest
from unittest.mock import AsyncMock, patch

from custom_components.secure_me.module_dispatch import (
    ModuleDispatcher,
    get_module_entity_ids,
    normalize_module_config,
)
from custom_components.secure_me.const import EVENT_MODULE_ERROR

from .conftest import MockConfigEntry, MockModule


# ---------------------------------------------------------------------------
# get_module_entity_ids() -- the v1.5.5 siren-visibility regression
# ---------------------------------------------------------------------------

class TestGetModuleEntityIds:
    """Locks in the v1.5.5 fix: siren's `sirens` list (list of dicts with an
    entity_id key) must be visible to health/availability scanning, the same
    way it always was for ws_modules.py's Test-tab copy.
    """

    def test_siren_entities_extracted_from_dict_list(self):
        module = MockModule()
        module.sirens = [
            {"entity_id": "siren.front_door", "pattern": "continuous"},
            {"entity_id": "switch.siren_relay", "pattern": "intermittent"},
        ]
        entities = get_module_entity_ids(module)
        assert "siren.front_door" in entities
        assert "switch.siren_relay" in entities

    def test_siren_plain_string_list_also_supported(self):
        """Defensive: a siren list of plain entity_id strings (not dicts)
        must also be picked up, not just the dict-with-entity_id form."""
        module = MockModule()
        module.sirens = ["siren.front_door", "siren.garage"]
        entities = get_module_entity_ids(module)
        assert "siren.front_door" in entities
        assert "siren.garage" in entities

    def test_siren_entries_without_entity_id_are_skipped(self):
        module = MockModule()
        module.sirens = [{"pattern": "continuous"}]  # no entity_id key
        entities = get_module_entity_ids(module)
        assert entities == []

    def test_flat_list_attributes_extracted(self):
        module = MockModule()
        module.cameras = ["camera.front", "camera.back"]
        module.locks = ["lock.front_door"]
        entities = get_module_entity_ids(module)
        assert "camera.front" in entities
        assert "camera.back" in entities
        assert "lock.front_door" in entities

    def test_dict_attributes_extracted_by_value(self):
        module = MockModule()
        module.door_sensors = {"front": "binary_sensor.front_door"}
        module.battery_sensors = {"lock": "sensor.lock_battery"}
        entities = get_module_entity_ids(module)
        assert "binary_sensor.front_door" in entities
        assert "sensor.lock_battery" in entities

    def test_gateway_light_extracted(self):
        module = MockModule()
        module.gateway_light = "light.gateway"
        entities = get_module_entity_ids(module)
        assert "light.gateway" in entities

    def test_duplicates_are_deduplicated(self):
        module = MockModule()
        module.cameras = ["camera.front", "camera.front"]
        entities = get_module_entity_ids(module)
        assert entities.count("camera.front") == 1

    def test_entries_without_a_dot_are_excluded(self):
        """Guards against garbage/placeholder values (e.g. empty string or
        a bare name with no domain) leaking into health scoring."""
        module = MockModule()
        module.cameras = ["not_a_valid_entity_id", ""]
        entities = get_module_entity_ids(module)
        assert entities == []

    def test_falls_back_to_config_dict_when_no_attributes_set(self):
        """A module with no matching flat-list attributes at all (e.g. a
        stripped-down stand-in) still exposes entities via its config dict.
        """
        module = MockModule()
        # Clear every attribute the primary extraction path looks at.
        module.cameras = []
        module.locks = []
        module.lights = []
        module.climates = []
        module.media_players = []
        module.recording_entities = []
        module.poe_switches = []
        module.config = {"locks": ["lock.fallback"]}
        entities = get_module_entity_ids(module)
        assert "lock.fallback" in entities

    def test_empty_module_returns_empty_list(self):
        module = MockModule()
        assert get_module_entity_ids(module) == []


# ---------------------------------------------------------------------------
# normalize_module_config()
# ---------------------------------------------------------------------------

class TestNormalizeModuleConfig:
    """Panel-saved config (rich objects) -> module class format (flat
    string lists). Each module_id has its own extraction rule.
    """

    def test_camera_extracts_entity_ids_and_poe_switches(self):
        config = {
            "cameras": [
                {"entity_id": "camera.front", "poe_port": "switch.poe_1"},
                {"entity_id": "camera.back"},
            ]
        }
        result = normalize_module_config("camera", config)
        assert result["cameras"] == ["camera.front", "camera.back"]
        assert result["poe_switches"] == ["switch.poe_1"]

    def test_camera_without_poe_ports_omits_poe_switches_key(self):
        config = {"cameras": [{"entity_id": "camera.front"}]}
        result = normalize_module_config("camera", config)
        assert "poe_switches" not in result or result.get("poe_switches") == []

    def test_lock_extracts_entity_ids_from_locks_key(self):
        config = {"locks": [{"entity_id": "lock.front"}, "lock.back"]}
        result = normalize_module_config("lock", config)
        assert result["locks"] == ["lock.front", "lock.back"]

    def test_climate_extracts_from_thermostats_key(self):
        config = {"thermostats": [{"entity_id": "climate.living_room"}]}
        result = normalize_module_config("climate", config)
        assert result["climates"] == ["climate.living_room"]

    def test_lights_prefers_entities_key_over_lights_key(self):
        config = {"entities": ["light.hall"], "lights": ["light.old_stale"]}
        result = normalize_module_config("lights", config)
        assert result["lights"] == ["light.hall"]

    def test_lights_falls_back_to_lights_key_when_entities_absent(self):
        config = {"lights": [{"entity_id": "light.hall"}]}
        result = normalize_module_config("lights", config)
        assert result["lights"] == ["light.hall"]

    def test_tts_normalizes_all_fields_with_defaults(self):
        config = {"entities": [{"entity_id": "media_player.kitchen"}]}
        result = normalize_module_config("tts", config)
        assert result["media_players"] == ["media_player.kitchen"]
        assert result["tts_service"] == "tts.cloud_say"
        assert result["language"] == "da"
        assert result["volume"] == 0.5

    def test_tts_respects_explicit_overrides(self):
        config = {
            "entities": [],
            "tts_service": "tts.custom_say",
            "language": "en",
            "volume": 0.8,
        }
        result = normalize_module_config("tts", config)
        assert result["tts_service"] == "tts.custom_say"
        assert result["language"] == "en"
        assert result["volume"] == 0.8

    def test_siren_passes_sirens_list_through_unchanged(self):
        sirens = [{"entity_id": "siren.front", "pattern": "continuous", "duration": 300, "volume": 80}]
        config = {"sirens": sirens}
        result = normalize_module_config("siren", config)
        assert result["sirens"] == sirens

    def test_siren_legacy_gateway_fields_passed_through(self):
        config = {"sirens": [], "gateway_mac": "AA:BB:CC", "gateway_light": "light.gw"}
        result = normalize_module_config("siren", config)
        assert result["gateway_mac"] == "AA:BB:CC"
        assert result["gateway_light"] == "light.gw"

    def test_unknown_module_id_returns_config_unchanged(self):
        config = {"foo": "bar"}
        result = normalize_module_config("unknown_module", config)
        assert result == {"foo": "bar"}


# ---------------------------------------------------------------------------
# ModuleDispatcher -- initialization
# ---------------------------------------------------------------------------

@pytest.fixture
def dispatcher(hass):
    """Real ModuleDispatcher with all six modules enabled by default."""
    entry = MockConfigEntry(options={"modules": {}})
    return ModuleDispatcher(hass, entry)


class TestModuleDispatcherInit:
    def test_all_six_modules_initialized(self, dispatcher):
        assert set(dispatcher.modules.keys()) == {
            "camera", "lock", "lights", "climate", "siren", "tts",
        }

    def test_modules_enabled_by_default(self, dispatcher):
        assert all(m.enabled for m in dispatcher.modules.values())

    def test_module_disabled_via_options(self, hass):
        entry = MockConfigEntry(options={"modules": {"camera": {"enabled": False}}})
        dispatcher = ModuleDispatcher(hass, entry)
        assert dispatcher.modules["camera"].enabled is False
        assert dispatcher.modules["lock"].enabled is True

    def test_update_module_config_reinitializes_module(self, dispatcher):
        old_module = dispatcher.modules["lock"]
        result = dispatcher.update_module_config("lock", {"locks": ["lock.new"]})
        assert result is True
        assert dispatcher.modules["lock"] is not old_module
        assert dispatcher.modules["lock"].locks == ["lock.new"]

    def test_update_module_config_unknown_module_returns_false(self, dispatcher):
        result = dispatcher.update_module_config("not_a_real_module", {})
        assert result is False

    def test_update_module_config_failure_keeps_old_module_and_returns_false(self, dispatcher, monkeypatch):
        """If re-initialization raises, the dispatcher must not crash and
        must leave the previously-working module instance in place."""
        old_module = dispatcher.modules["lock"]

        def _boom(hass, config):
            raise ValueError("bad config")

        monkeypatch.setitem(
            __import__("custom_components.secure_me.module_dispatch", fromlist=["_MODULE_CLASSES"])._MODULE_CLASSES,
            "lock",
            _boom,
        )
        result = dispatcher.update_module_config("lock", {})
        assert result is False
        assert dispatcher.modules["lock"] is old_module


# ---------------------------------------------------------------------------
# ModuleDispatcher -- arm/disarm/trigger dispatch
# ---------------------------------------------------------------------------

class TestModuleDispatcherDispatch:
    @pytest.mark.asyncio
    async def test_execute_arm_away_calls_every_enabled_module(self, dispatcher):
        for module in dispatcher.modules.values():
            module.async_arm = AsyncMock(return_value=True)

        await dispatcher.execute_arm_away()

        for module in dispatcher.modules.values():
            module.async_arm.assert_awaited_once_with("away")

    @pytest.mark.asyncio
    async def test_disabled_module_is_skipped(self, dispatcher):
        dispatcher.modules["camera"].disable()
        dispatcher.modules["camera"].async_arm = AsyncMock(return_value=True)
        dispatcher.modules["lock"].async_arm = AsyncMock(return_value=True)

        await dispatcher.execute_arm_away()

        dispatcher.modules["camera"].async_arm.assert_not_awaited()
        dispatcher.modules["lock"].async_arm.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_one_module_raising_does_not_block_the_others(self, dispatcher):
        """Fault isolation: a failing module must not prevent the remaining
        enabled modules from still being dispatched."""
        dispatcher.modules["camera"].async_arm = AsyncMock(side_effect=Exception("camera offline"))
        dispatcher.modules["lock"].async_arm = AsyncMock(return_value=True)

        await dispatcher.execute_arm_away()

        dispatcher.modules["lock"].async_arm.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_module_error_fires_event_with_module_and_action(self, dispatcher):
        dispatcher.modules["camera"].async_arm = AsyncMock(side_effect=Exception("camera offline"))

        await dispatcher.execute_arm_away()

        fired = [
            call for call in dispatcher.hass.bus.async_fire.call_args_list
            if call.args[0] == EVENT_MODULE_ERROR
        ]
        assert len(fired) == 1
        payload = fired[0].args[1]
        assert payload["module"] == "camera"
        assert payload["action"] == "arm_away"

    @pytest.mark.asyncio
    async def test_execute_disarm_calls_async_disarm(self, dispatcher):
        for module in dispatcher.modules.values():
            module.async_disarm = AsyncMock(return_value=True)
        await dispatcher.execute_disarm()
        for module in dispatcher.modules.values():
            module.async_disarm.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_trigger_calls_async_trigger(self, dispatcher):
        for module in dispatcher.modules.values():
            module.async_trigger = AsyncMock(return_value=True)
        await dispatcher.execute_trigger()
        for module in dispatcher.modules.values():
            module.async_trigger.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_arm_home_and_arm_night_pass_correct_mode(self, dispatcher):
        for module in dispatcher.modules.values():
            module.async_arm = AsyncMock(return_value=True)

        await dispatcher.execute_arm_home()
        for module in dispatcher.modules.values():
            module.async_arm.assert_awaited_with("home")

        for module in dispatcher.modules.values():
            module.async_arm = AsyncMock(return_value=True)
        await dispatcher.execute_arm_night()
        for module in dispatcher.modules.values():
            module.async_arm.assert_awaited_with("night")


# ---------------------------------------------------------------------------
# ModuleDispatcher -- health scoring
# ---------------------------------------------------------------------------

class TestModuleDispatcherHealth:
    def test_health_score_100_when_no_entities_configured(self, dispatcher):
        assert dispatcher.get_health_score() == 100

    def test_health_score_reflects_available_vs_unavailable(self, dispatcher, hass):
        dispatcher.modules["lock"].locks = ["lock.front", "lock.back"]
        hass.states.async_set("lock.front", "locked")
        hass.states.async_set("lock.back", "unavailable")

        score = dispatcher.get_health_score()
        assert score == 50

    def test_health_score_100_when_all_configured_entities_available(self, dispatcher, hass):
        dispatcher.modules["lock"].locks = ["lock.front"]
        hass.states.async_set("lock.front", "locked")
        assert dispatcher.get_health_score() == 100

    def test_disabled_module_excluded_from_health_score(self, dispatcher, hass):
        dispatcher.modules["camera"].cameras = ["camera.front"]
        # camera.front is never set -> would be unavailable if counted
        dispatcher.modules["camera"].disable()
        assert dispatcher.get_health_score() == 100

    def test_siren_unavailable_lowers_health_score(self, dispatcher, hass):
        """Regression guard for the v1.5.5 fix: an unavailable siren must
        actually affect the passive health score, not be invisible to it."""
        dispatcher.modules["siren"].sirens = [{"entity_id": "siren.front"}]
        hass.states.async_set("siren.front", "unavailable")
        assert dispatcher.get_health_score() < 100

    def test_get_module_health_reports_disabled_module(self, dispatcher):
        dispatcher.modules["camera"].disable()
        health = dispatcher.get_module_health()
        assert health["camera"]["enabled"] is False
        assert health["camera"]["status"] == "disabled"

    def test_get_module_health_reports_ok_status(self, dispatcher, hass):
        dispatcher.modules["lock"].locks = ["lock.front"]
        hass.states.async_set("lock.front", "locked")
        health = dispatcher.get_module_health()
        assert health["lock"]["status"] == "ok"
        assert health["lock"]["available"] == 1
        assert health["lock"]["unavailable"] == []

    def test_get_module_health_reports_error_status_with_unavailable_list(self, dispatcher, hass):
        dispatcher.modules["lock"].locks = ["lock.front"]
        hass.states.async_set("lock.front", "unavailable")
        health = dispatcher.get_module_health()
        assert health["lock"]["status"] == "error"
        assert "lock.front" in health["lock"]["unavailable"]

    def test_get_module_health_reports_degraded_status(self, dispatcher, hass):
        dispatcher.modules["lock"].locks = ["lock.front"]
        hass.states.async_set("lock.front", "locked")
        dispatcher.modules["lock"]._degraded = True
        health = dispatcher.get_module_health()
        assert health["lock"]["status"] == "degraded"

    def test_get_enabled_module_count(self, dispatcher):
        assert dispatcher.get_enabled_module_count() == 6
        dispatcher.modules["camera"].disable()
        dispatcher.modules["tts"].disable()
        assert dispatcher.get_enabled_module_count() == 4


# ---------------------------------------------------------------------------
# ModuleDispatcher -- battery cache
# ---------------------------------------------------------------------------

class TestModuleDispatcherBatteryCache:
    def test_battery_cache_calls_discovery_once_within_ttl(self, dispatcher):
        with patch(
            "custom_components.secure_me.ws_helpers._discover_batteries",
            return_value=[{"entity_id": "sensor.lock_battery", "level": 80}],
        ) as mock_discover:
            first = dispatcher.get_batteries_cached({"lock.front"})
            second = dispatcher.get_batteries_cached({"lock.front"})

            assert first == second
            mock_discover.assert_called_once()

    def test_invalidate_battery_cache_forces_rebuild(self, dispatcher):
        with patch(
            "custom_components.secure_me.ws_helpers._discover_batteries",
            return_value=[{"entity_id": "sensor.lock_battery", "level": 80}],
        ) as mock_discover:
            dispatcher.get_batteries_cached({"lock.front"})
            dispatcher.invalidate_battery_cache()
            dispatcher.get_batteries_cached({"lock.front"})

            assert mock_discover.call_count == 2

    def test_battery_cache_rebuilds_after_ttl_expires(self, dispatcher):
        with patch(
            "custom_components.secure_me.ws_helpers._discover_batteries",
            return_value=[],
        ) as mock_discover:
            dispatcher.get_batteries_cached({"lock.front"})
            # Simulate TTL expiry without sleeping the test for 5 real minutes.
            dispatcher._battery_cache_time = time.monotonic() - 301
            dispatcher.get_batteries_cached({"lock.front"})

            assert mock_discover.call_count == 2


# ---------------------------------------------------------------------------
# ModuleDispatcher -- cleanup
# ---------------------------------------------------------------------------

class TestModuleDispatcherCleanup:
    @pytest.mark.asyncio
    async def test_async_cleanup_calls_every_module(self, dispatcher):
        for module in dispatcher.modules.values():
            module.async_cleanup = AsyncMock()

        await dispatcher.async_cleanup()

        for module in dispatcher.modules.values():
            module.async_cleanup.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_one_module_cleanup_failure_does_not_block_others(self, dispatcher):
        dispatcher.modules["camera"].async_cleanup = AsyncMock(side_effect=Exception("boom"))
        dispatcher.modules["lock"].async_cleanup = AsyncMock()

        await dispatcher.async_cleanup()

        dispatcher.modules["lock"].async_cleanup.assert_awaited_once()
