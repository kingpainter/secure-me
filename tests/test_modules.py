"""Tests for Secure Me module system."""
# VERSION = "1.2.0"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
        total = 0
        score = 100 if total == 0 else round((0 / total) * 100)
        assert score == 100


class TestLockModuleFunctional:
    """Tests for the REAL LockModule.async_test() (custom_components.secure_me.modules.lock).

    Previously this class tested a hand-written FakeLockModule that reimplemented
    the logic independently -- it could pass even if the real module diverged
    (and it had, silently: the real module used to leave the lock unlocked after
    testing an unlocked lock, and never functionally tested a lock that started
    locked). These tests now import and exercise the real class directly.
    """

    @pytest.fixture(autouse=True)
    def _no_real_sleep(self):
        """async_test() uses real asyncio.sleep(2) between lock/unlock steps.

        Patched here so the test suite doesn't take 4s+ per lock -- this does not
        change production behaviour, only how fast the test observes it.
        """
        with patch("custom_components.secure_me.modules.lock.asyncio.sleep", new=AsyncMock()):
            yield

    def _wire_service_calls(self, hass):
        """Make hass.services.async_call flip lock state, mimicking a real lock."""
        async def _handle(domain, service, service_data=None, target=None, blocking=True):
            eid = (target or {}).get("entity_id", "")
            if domain == "lock" and service == "unlock":
                hass.set_state(eid, "unlocked")
            elif domain == "lock" and service == "lock":
                hass.set_state(eid, "locked")
        hass.services.async_call = AsyncMock(side_effect=_handle)

    def _make_lock_module(self, hass, locks=None, door_sensors=None, battery_sensors=None):
        from custom_components.secure_me.modules.lock import LockModule
        config = {
            "locks": locks or [],
            "door_sensors": door_sensors or {},
            "battery_sensors": battery_sensors or {},
        }
        return LockModule(hass, config)

    @pytest.mark.asyncio
    async def test_lock_functional_test_passes(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("person.flemming", "home")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front"])
        result = await mod.async_test()
        assert result["success"] is True
        lock_info = result["details"]["locks"][0]
        assert lock_info["unlock_ok"] is True
        assert lock_info["relock_ok"] is True
        assert lock_info["test_passed"] is True
        assert lock_info["final_state"] == "locked"

    @pytest.mark.asyncio
    async def test_lock_always_ends_locked_when_starting_unlocked(self, mock_hass):
        """Regression test for the bug this class used to hide: starting unlocked
        must still end locked, not be relocked-then-unlocked-again."""
        mock_hass.set_state("lock.front", "unlocked")
        mock_hass.set_state("person.flemming", "home")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front"])
        result = await mod.async_test()
        assert mock_hass.states.get("lock.front").state == "locked"
        lock_info = result["details"]["locks"][0]
        assert lock_info["relock_ok"] is True
        assert lock_info["unlock_ok"] is None  # never attempted -- was already unlocked

    @pytest.mark.asyncio
    async def test_lock_starting_locked_is_actually_exercised(self, mock_hass):
        """Regression test: a lock that starts locked must be functionally tested
        (unlock -> verify -> relock -> verify), not rubber-stamped as passed."""
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("person.flemming", "home")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front"])
        result = await mod.async_test()
        assert mock_hass.services.async_call.call_count == 2  # unlock + relock
        lock_info = result["details"]["locks"][0]
        assert lock_info["unlock_ok"] is True
        assert lock_info["relock_ok"] is True

    @pytest.mark.asyncio
    async def test_lock_functional_test_skipped_when_nobody_home(self, mock_hass):
        """Safety feature: the destructive unlock/relock cycle briefly leaves a
        real door unlocked for ~4s. If no tracked person currently reports
        'home', the functional test is skipped entirely rather than doing that
        unattended -- see LockModule.async_test()'s own docstring/comment for
        the full rationale. Availability/current-state reporting still happens;
        only the destructive cycle is skipped.
        """
        mock_hass.set_state("lock.front", "locked")
        # No person.* entity set to "home" at all.
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front"])
        result = await mod.async_test()
        assert result["success"] is True
        lock_info = result["details"]["locks"][0]
        assert lock_info["skip_reason"] == "nobody_home"
        assert lock_info["test_passed"] is True
        assert lock_info["unlock_ok"] is None
        assert lock_info["relock_ok"] is None
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_lock_skipped_when_door_open(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("binary_sensor.door", "on")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(
            mock_hass,
            locks=["lock.front"],
            door_sensors={"lock.front": "binary_sensor.door"},
        )
        result = await mod.async_test()
        assert result["success"] is True
        lock_info = result["details"]["locks"][0]
        assert lock_info["skip_reason"] == "door_open"
        assert lock_info["test_passed"] is True
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_lock_unavailable_fails(self, mock_hass):
        mock_hass.set_state("lock.front", "unavailable")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front"])
        result = await mod.async_test()
        assert result["success"] is False
        lock_info = result["details"]["locks"][0]
        assert lock_info["test_passed"] is False
        assert lock_info["unlock_ok"] is None

    @pytest.mark.asyncio
    async def test_lock_battery_low_warning(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("sensor.front_battery", "15")
        mock_hass.set_state("person.flemming", "home")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(
            mock_hass,
            locks=["lock.front"],
            battery_sensors={"lock.front": "sensor.front_battery"},
        )
        result = await mod.async_test()
        assert result["details"]["locks"][0]["battery"] == 15
        # Low-battery is a non-fatal warning -- it lives in results["warnings"],
        # not results["message"] (that field is reserved for real failures; see
        # ws_modules.py's _run_test_internal(), which surfaces per-module
        # warnings at the top level of a Standard/Full test run instead).
        assert any("battery low" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_lock_reports_unlock_and_relock_separately(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("person.flemming", "home")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front"])
        result = await mod.async_test()
        lock_info = result["details"]["locks"][0]
        assert "unlock_ok" in lock_info
        assert "relock_ok" in lock_info
        assert "initial_state" in lock_info
        assert "final_state" in lock_info

    @pytest.mark.asyncio
    async def test_multiple_locks_all_pass(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("lock.back", "locked")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front", "lock.back"])
        result = await mod.async_test()
        assert result["success"] is True
        assert len(result["details"]["locks"]) == 2
        assert all(l["test_passed"] for l in result["details"]["locks"])

    @pytest.mark.asyncio
    async def test_multiple_locks_one_unavailable(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("lock.back", "unavailable")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front", "lock.back"])
        result = await mod.async_test()
        assert result["success"] is False
        front = next(l for l in result["details"]["locks"] if l["entity_id"] == "lock.front")
        back = next(l for l in result["details"]["locks"] if l["entity_id"] == "lock.back")
        assert front["test_passed"] is True
        assert back["test_passed"] is False

    @pytest.mark.asyncio
    async def test_multiple_unavailable_locks_all_appear_in_summary_message(self, mock_hass):
        """Regression: with 2+ problems, only the LAST one used to survive in
        results['message'] -- the first was silently dropped from the summary
        (though always present in the per-lock details)."""
        mock_hass.set_state("lock.front", "unavailable")
        mock_hass.set_state("lock.back", "unavailable")
        self._wire_service_calls(mock_hass)
        mod = self._make_lock_module(mock_hass, locks=["lock.front", "lock.back"])
        result = await mod.async_test()
        assert "lock.front" in result["message"]
        assert "lock.back" in result["message"]


class TestSirenModuleDomainHandling:
    """Regression tests for the REAL SirenModule (custom_components.secure_me.modules.siren).

    Previously an unsupported-domain siren entity (e.g. a renamed/misconfigured
    entity, or a media_player-based siren) failed completely silently: no
    exception, no notification, just a debug-level log line nobody sees. During
    a real trigger this meant a siren could simply never sound. During the Test
    tab it meant `test_fired: true` was reported even though nothing happened --
    a false-positive safety test. No test file previously covered this module
    at all.
    """

    @pytest.fixture(autouse=True)
    def _no_real_sleep(self):
        with patch("custom_components.secure_me.modules.siren.asyncio.sleep", new=AsyncMock()):
            yield

    def _make_hass(self):
        hass = MockHass()
        hass.components = MagicMock()
        hass.components.persistent_notification = MagicMock()
        hass.components.persistent_notification.async_create = MagicMock()
        hass.services.async_call = AsyncMock()
        return hass

    def _make_siren(self, hass, sirens=None):
        from custom_components.secure_me.modules.siren import SirenModule
        return SirenModule(hass, {"sirens": sirens or []})

    @pytest.mark.asyncio
    async def test_turn_on_supported_siren_domain_returns_true(self):
        hass = self._make_hass()
        mod = self._make_siren(hass)
        assert await mod._turn_on_entity("siren.front", 50) is True

    @pytest.mark.asyncio
    async def test_turn_on_supported_switch_domain_returns_true(self):
        hass = self._make_hass()
        mod = self._make_siren(hass)
        assert await mod._turn_on_entity("switch.siren_relay", 50) is True

    @pytest.mark.asyncio
    async def test_turn_on_unsupported_domain_returns_false(self):
        """Regression: this used to return None and look like success."""
        hass = self._make_hass()
        mod = self._make_siren(hass)
        assert await mod._turn_on_entity("media_player.kitchen", 50) is False

    @pytest.mark.asyncio
    async def test_turn_on_unsupported_domain_sets_degraded(self):
        """Regression: a misconfigured siren must now surface as degraded."""
        hass = self._make_hass()
        mod = self._make_siren(hass)
        await mod._turn_on_entity("media_player.kitchen", 50)
        assert mod.degraded is True

    @pytest.mark.asyncio
    async def test_turn_on_unsupported_domain_fires_notification(self):
        """Regression: this used to fail completely silently.

        base.py's _on_failure calls the real
        homeassistant.components.persistent_notification.async_create function
        directly (a local import inside the method), not hass.components.* --
        that convention only exists in test_base_module.py's hand-written
        mirror class, which doesn't reflect the real module.
        """
        hass = self._make_hass()
        mod = self._make_siren(hass)
        with patch("homeassistant.components.persistent_notification.async_create") as mock_create:
            await mod._turn_on_entity("media_player.kitchen", 50)
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_turn_off_unsupported_domain_returns_false(self):
        hass = self._make_hass()
        mod = self._make_siren(hass)
        assert await mod._turn_off_entity("media_player.kitchen") is False

    @pytest.mark.asyncio
    async def test_async_test_fails_for_unsupported_domain_entity(self):
        """Regression: async_test() used to report test_fired=True (false positive)
        for an entity that never actually did anything."""
        hass = self._make_hass()
        hass.set_state("media_player.kitchen", "idle")
        mod = self._make_siren(hass, sirens=[{"entity_id": "media_player.kitchen"}])
        result = await mod.async_test()
        entity_result = result["details"]["entities_tested"][0]
        assert entity_result["test_fired"] is False
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_async_test_passes_for_supported_switch_domain(self):
        hass = self._make_hass()
        hass.set_state("switch.siren_relay", "off")
        mod = self._make_siren(hass, sirens=[{"entity_id": "switch.siren_relay"}])
        result = await mod.async_test()
        entity_result = result["details"]["entities_tested"][0]
        assert entity_result["test_fired"] is True
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_async_test_passes_for_native_siren_domain(self):
        hass = self._make_hass()
        hass.set_state("siren.front", "off")
        mod = self._make_siren(hass, sirens=[{"entity_id": "siren.front"}])
        result = await mod.async_test()
        entity_result = result["details"]["entities_tested"][0]
        assert entity_result["test_fired"] is True
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_multiple_unavailable_entities_all_appear_in_summary_message(self):
        """Regression: only the LAST problem used to survive in results['message']."""
        hass = self._make_hass()
        # both entities missing from hass -> both unavailable
        mod = self._make_siren(hass, sirens=[
            {"entity_id": "siren.front"}, {"entity_id": "siren.back"},
        ])
        result = await mod.async_test()
        assert "siren.front" in result["message"]
        assert "siren.back" in result["message"]


class TestAlarmCycleTest:
    """Tests for Alarm Cycle Test in ws_run_test (Standard + Full)."""

    def _make_state_machine(self, initial_state="disarmed"):
        import asyncio

        class FakeStateMachine:
            def __init__(self):
                self.current_state = initial_state
                self.arm_calls = []
                self.disarm_calls = 0

            async def arm_away(self, skip_delay=False):
                self.arm_calls.append({"mode": "away", "skip_delay": skip_delay})
                self.current_state = "armed_away"
                return True

            async def disarm(self):
                self.disarm_calls += 1
                self.current_state = "disarmed"
                return True

        return FakeStateMachine()

    @pytest.mark.asyncio
    async def test_alarm_cycle_passes_when_disarmed(self):
        sm = self._make_state_machine("disarmed")
        alarm_cycle = {"status": "pass", "arm_ok": False, "disarm_ok": False}

        if sm.current_state != "disarmed":
            alarm_cycle["status"] = "skipped"
        else:
            arm_ok = await sm.arm_away(skip_delay=True)
            actual_armed = sm.current_state == "armed_away"
            alarm_cycle["arm_ok"] = arm_ok and actual_armed
            disarm_ok = await sm.disarm()
            actual_disarmed = sm.current_state == "disarmed"
            alarm_cycle["disarm_ok"] = disarm_ok and actual_disarmed
            if alarm_cycle["arm_ok"] and actual_disarmed:
                alarm_cycle["status"] = "pass"

        assert alarm_cycle["status"] == "pass"
        assert alarm_cycle["arm_ok"] is True
        assert alarm_cycle["disarm_ok"] is True

    @pytest.mark.asyncio
    async def test_alarm_cycle_skipped_when_already_armed(self):
        sm = self._make_state_machine("armed_away")
        alarm_cycle = {"status": "pass", "arm_ok": False, "disarm_ok": False}

        if sm.current_state != "disarmed":
            alarm_cycle["status"] = "skipped"
            alarm_cycle["message"] = f"Alarm is {sm.current_state} -- cycle test skipped"

        assert alarm_cycle["status"] == "skipped"
        assert sm.arm_calls == []
        assert sm.disarm_calls == 0

    @pytest.mark.asyncio
    async def test_alarm_cycle_uses_skip_delay(self):
        sm = self._make_state_machine("disarmed")
        await sm.arm_away(skip_delay=True)
        assert sm.arm_calls[0]["skip_delay"] is True

    @pytest.mark.asyncio
    async def test_alarm_cycle_always_disarms(self):
        sm = self._make_state_machine("disarmed")
        await sm.arm_away(skip_delay=True)
        assert sm.current_state == "armed_away"
        await sm.disarm()
        assert sm.current_state == "disarmed"
        assert sm.disarm_calls == 1

    @pytest.mark.asyncio
    async def test_alarm_cycle_final_state_is_disarmed(self):
        sm = self._make_state_machine("disarmed")
        await sm.arm_away(skip_delay=True)
        await sm.disarm()
        assert sm.current_state == "disarmed"


class TestSeveritySystem:
    """Tests for severity-aware overall result calculation."""

    def _run_overall(self, module_results, sensor_results=None, alarm_cycle_status="pass"):
        MODULE_SEVERITY = {
            "siren":   "critical",
            "lock":    "critical",
            "camera":  "high",
            "lights":  "medium",
            "climate": "low",
            "tts":     "low",
        }
        SENSOR_SEVERITY = {
            "environmental": "critical",
            "contact":       "high",
            "motion":        "high",
            "presence":      "medium",
        }

        critical_fails = []
        high_fails = []
        low_fails = []

        for mod_id, m in module_results.items():
            if m.get("status") not in ("fail", "error"):
                continue
            sev = MODULE_SEVERITY.get(mod_id, "medium")
            if sev == "critical":
                critical_fails.append(mod_id)
            elif sev == "high":
                high_fails.append(mod_id)
            else:
                low_fails.append(mod_id)

        critical_sensor_fails = []
        high_sensor_fails = []
        low_sensor_fails = []
        for eid, s in (sensor_results or {}).items():
            if s.get("status") != "fail":
                continue
            sev = SENSOR_SEVERITY.get(s.get("type", "contact"), "high")
            if sev == "critical":
                critical_sensor_fails.append(eid)
            elif sev == "high":
                high_sensor_fails.append(eid)
            else:
                low_sensor_fails.append(eid)

        if alarm_cycle_status in ("fail", "error"):
            critical_fails.append("alarm_cycle")

        if critical_fails or critical_sensor_fails:
            overall = "critical"
        elif high_fails or high_sensor_fails:
            overall = "fail"
        elif low_fails or low_sensor_fails or any(m.get("status") == "warning" for m in module_results.values()):
            overall = "warning"
        else:
            overall = "pass"

        return overall, critical_fails + critical_sensor_fails, high_fails + high_sensor_fails, low_fails

    def test_all_pass_gives_pass(self):
        mods = {"siren": {"status": "pass"}, "lock": {"status": "pass"}, "camera": {"status": "pass"}}
        overall, cf, hf, lf = self._run_overall(mods)
        assert overall == "pass"
        assert cf == [] and hf == [] and lf == []

    def test_siren_fail_is_critical(self):
        mods = {"siren": {"status": "fail"}, "lock": {"status": "pass"}}
        overall, cf, _, _ = self._run_overall(mods)
        assert overall == "critical"
        assert "siren" in cf

    def test_lock_fail_is_critical(self):
        mods = {"lock": {"status": "fail"}, "camera": {"status": "pass"}}
        overall, cf, _, _ = self._run_overall(mods)
        assert overall == "critical"
        assert "lock" in cf

    def test_camera_fail_is_high(self):
        mods = {"camera": {"status": "fail"}, "siren": {"status": "pass"}}
        overall, cf, hf, _ = self._run_overall(mods)
        assert overall == "fail"
        assert cf == []
        assert "camera" in hf

    def test_climate_fail_is_warning(self):
        mods = {"climate": {"status": "fail"}, "siren": {"status": "pass"}}
        overall, cf, hf, lf = self._run_overall(mods)
        assert overall == "warning"
        assert cf == [] and hf == []
        assert "climate" in lf

    def test_tts_fail_is_warning(self):
        mods = {"tts": {"status": "fail"}}
        overall, _, _, lf = self._run_overall(mods)
        assert overall == "warning"
        assert "tts" in lf

    def test_environmental_sensor_fail_is_critical(self):
        sensors = {"binary_sensor.smoke": {"status": "fail", "type": "environmental"}}
        overall, cf, _, _ = self._run_overall({}, sensors)
        assert overall == "critical"
        assert "binary_sensor.smoke" in cf

    def test_contact_sensor_fail_is_high(self):
        sensors = {"binary_sensor.door": {"status": "fail", "type": "contact"}}
        overall, cf, hf, _ = self._run_overall({}, sensors)
        assert overall == "fail"
        assert cf == []
        assert "binary_sensor.door" in hf

    def test_presence_sensor_fail_is_warning(self):
        sensors = {"device_tracker.person": {"status": "fail", "type": "presence"}}
        overall, cf, hf, lf = self._run_overall({}, sensors)
        assert overall == "warning"

    def test_alarm_cycle_fail_is_critical(self):
        mods = {"camera": {"status": "pass"}}
        overall, cf, _, _ = self._run_overall(mods, alarm_cycle_status="fail")
        assert overall == "critical"
        assert "alarm_cycle" in cf

    def test_critical_overrides_high(self):
        mods = {
            "siren":  {"status": "fail"},
            "camera": {"status": "fail"},
            "tts":    {"status": "fail"},
        }
        overall, cf, hf, lf = self._run_overall(mods)
        assert overall == "critical"
        assert "siren" in cf
        assert "camera" in hf
        assert "tts" in lf

    def test_skipped_and_warned_dont_affect_overall(self):
        mods = {
            "siren":   {"status": "skipped"},
            "climate": {"status": "warning"},
            "lock":    {"status": "pass"},
        }
        overall, cf, hf, _ = self._run_overall(mods)
        assert overall == "warning"
        assert cf == [] and hf == []

    def test_module_severity_map_completeness(self):
        MODULE_SEVERITY = {
            "siren": "critical", "lock": "critical",
            "camera": "high",
            "lights": "medium", "climate": "low", "tts": "low",
        }
        expected = {"siren", "lock", "camera", "lights", "climate", "tts"}
        assert set(MODULE_SEVERITY.keys()) == expected

    def test_sensor_severity_map_completeness(self):
        SENSOR_SEVERITY = {
            "environmental": "critical",
            "contact": "high",
            "motion": "high",
            "presence": "medium",
        }
        expected = {"environmental", "contact", "motion", "presence"}
        assert set(SENSOR_SEVERITY.keys()) == expected


class TestTTSSpeakerTargeting:
    """Regression tests for the REAL TTSModule._play_message speaker targeting.

    Previously, a message targeted at specific speakers (msg['speakers']) that
    no longer matched any configured profile (e.g. a renamed/removed speaker)
    silently fell back to announcing on ALL speakers instead of being skipped.
    A message meant for one room could unexpectedly announce house-wide.
    """

    def _make_hass(self):
        hass = MockHass()
        hass.services.async_call = AsyncMock()
        return hass

    def _profile(self, entity_id, name):
        return {
            "entity_id": entity_id, "name": name, "volume": 0.5,
            "tts_service": "tts.cloud_say", "tts_entity": "tts.home_assistant_cloud",
        }

    def _make_tts(self, hass, speaker_profiles=None):
        from custom_components.secure_me.modules.tts import TTSModule
        return TTSModule(hass, {"speaker_profiles": speaker_profiles or []})

    @pytest.mark.asyncio
    async def test_targeted_message_no_match_skips_instead_of_broadcasting(self):
        """Regression: this used to fall back to announcing on ALL speakers."""
        hass = self._make_hass()
        mod = self._make_tts(hass, [self._profile("media_player.kitchen", "Kitchen")])
        mod._play_on_speakers = AsyncMock()
        msg = {"type": "tts", "message": "Hello", "speakers": ["media_player.removed"]}
        await mod._play_message(msg)
        mod._play_on_speakers.assert_not_called()

    @pytest.mark.asyncio
    async def test_targeted_message_plays_only_on_matching_speaker(self):
        hass = self._make_hass()
        mod = self._make_tts(hass, [
            self._profile("media_player.kitchen", "Kitchen"),
            self._profile("media_player.living", "Living"),
        ])
        mod._play_on_speakers = AsyncMock()
        msg = {"type": "tts", "message": "Hello", "speakers": ["media_player.kitchen"]}
        await mod._play_message(msg)
        mod._play_on_speakers.assert_called_once()
        called_speakers = mod._play_on_speakers.call_args.args[1]
        assert {s["entity_id"] for s in called_speakers} == {"media_player.kitchen"}

    @pytest.mark.asyncio
    async def test_untargeted_message_plays_on_all_speakers(self):
        hass = self._make_hass()
        mod = self._make_tts(hass, [
            self._profile("media_player.kitchen", "Kitchen"),
            self._profile("media_player.living", "Living"),
        ])
        mod._play_on_speakers = AsyncMock()
        msg = {"type": "tts", "message": "Hello"}  # no 'speakers' key -> all
        await mod._play_message(msg)
        called_speakers = mod._play_on_speakers.call_args.args[1]
        assert {s["entity_id"] for s in called_speakers} == {"media_player.kitchen", "media_player.living"}


class TestLightsModuleSteadyLightsCoverage:
    """Regression: async_test() previously never checked steady_lights at all --
    a Full test could report success=True even if every steady light was broken."""

    def _make_lights(self, hass, lights=None, steady_lights=None):
        from custom_components.secure_me.modules.lights import LightsModule
        return LightsModule(hass, {"lights": lights or [], "steady_lights": steady_lights or []})

    @pytest.mark.asyncio
    async def test_steady_lights_included_in_test_details(self, mock_hass):
        mock_hass.set_state("light.steady1", "on", {"brightness": 255})
        mod = self._make_lights(mock_hass, steady_lights=["light.steady1"])
        result = await mod.async_test()
        assert len(result["details"]["steady_lights"]) == 1
        assert result["details"]["steady_lights"][0]["entity_id"] == "light.steady1"

    @pytest.mark.asyncio
    async def test_unavailable_steady_light_fails_test(self, mock_hass):
        """Regression: this used to report success=True regardless."""
        mock_hass.set_state("light.steady1", "unavailable")
        mod = self._make_lights(mock_hass, steady_lights=["light.steady1"])
        result = await mod.async_test()
        assert result["success"] is False
        assert "Steady light" in result["message"]

    @pytest.mark.asyncio
    async def test_available_steady_light_does_not_fail_test(self, mock_hass):
        mock_hass.set_state("light.steady1", "on")
        mod = self._make_lights(mock_hass, steady_lights=["light.steady1"])
        result = await mod.async_test()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_multiple_unavailable_lights_all_appear_in_summary_message(self, mock_hass):
        """Regression: only the LAST problem used to survive in results['message']."""
        mock_hass.set_state("light.a", "unavailable")
        mock_hass.set_state("light.b", "unavailable")
        mod = self._make_lights(mock_hass, lights=["light.a", "light.b"])
        result = await mod.async_test()
        assert "light.a" in result["message"]
        assert "light.b" in result["message"]


class TestCameraModulePoeRestoreRetry:
    """Regression: async_test() previously restored POE to OFF with a single,
    non-retried service call and silently ignored failure -- cameras could be
    left powered on indefinitely with zero notification to the user."""

    @pytest.fixture(autouse=True)
    def _no_real_sleep(self):
        with patch("custom_components.secure_me.modules.camera.asyncio.sleep", new=AsyncMock()), \
             patch("custom_components.secure_me.modules.base.asyncio.sleep", new=AsyncMock()):
            yield

    def _make_hass(self):
        hass = MockHass()
        hass.components = MagicMock()
        hass.components.persistent_notification = MagicMock()
        hass.components.persistent_notification.async_create = MagicMock()
        return hass

    def _make_camera(self, hass, poe_switches=None, cameras=None):
        from custom_components.secure_me.modules.camera import CameraModule
        return CameraModule(hass, {
            "poe_switches": poe_switches or [], "cameras": cameras or [], "poe_delay": 30,
        })

    @pytest.mark.asyncio
    async def test_poe_restored_off_successfully(self):
        hass = self._make_hass()
        hass.set_state("switch.poe1", "off")

        async def _handle(domain, service, service_data=None, target=None, blocking=True):
            eid = (target or {}).get("entity_id", "")
            if domain == "switch" and service == "turn_off":
                hass.set_state(eid, "off")
            elif domain == "switch" and service == "turn_on":
                hass.set_state(eid, "on")
        hass.services.async_call = AsyncMock(side_effect=_handle)

        mod = self._make_camera(hass, poe_switches=["switch.poe1"])
        result = await mod.async_test()
        assert result["details"]["poe_status"]["restored_to_off"] is True
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_poe_restore_failure_is_surfaced(self):
        """Regression: this used to be silently swallowed."""
        hass = self._make_hass()
        hass.set_state("switch.poe1", "off")
        hass.services.async_call = AsyncMock(side_effect=Exception("network error"))

        mod = self._make_camera(hass, poe_switches=["switch.poe1"])
        result = await mod.async_test()
        assert result["details"]["poe_status"]["restored_to_off"] is False
        assert result["success"] is False
        assert "restore POE" in result["message"]

    @pytest.mark.asyncio
    async def test_multiple_unavailable_poe_switches_all_checked_and_reported(self):
        """Regression: previously this returned on the FIRST unavailable POE
        switch and never even looked at the rest -- both details and the
        summary message were incomplete."""
        hass = self._make_hass()
        hass.set_state("switch.poe1", "unavailable")
        hass.set_state("switch.poe2", "unavailable")
        hass.services.async_call = AsyncMock()

        mod = self._make_camera(hass, poe_switches=["switch.poe1", "switch.poe2"])
        result = await mod.async_test()
        assert len(result["details"]["poe_switches"]) == 2
        assert "switch.poe1" in result["message"]
        assert "switch.poe2" in result["message"]


class TestTTSModuleMessageAggregation:
    """Regression: only the LAST unavailable speaker used to survive in
    results['message'] -- details per-speaker were always correct."""

    def _make_hass(self):
        hass = MockHass()
        hass.services.async_call = AsyncMock()
        return hass

    def _profile(self, entity_id, name):
        return {
            "entity_id": entity_id, "name": name, "volume": 0.5,
            "tts_service": "tts.cloud_say", "tts_entity": "tts.home_assistant_cloud",
        }

    def _make_tts(self, hass, speaker_profiles=None):
        from custom_components.secure_me.modules.tts import TTSModule
        return TTSModule(hass, {"speaker_profiles": speaker_profiles or []})

    @pytest.mark.asyncio
    async def test_multiple_unavailable_speakers_all_appear_in_summary_message(self):
        hass = self._make_hass()
        hass.set_state("media_player.kitchen", "unavailable")
        hass.set_state("media_player.living", "unavailable")
        mod = self._make_tts(hass, [
            self._profile("media_player.kitchen", "Kitchen"),
            self._profile("media_player.living", "Living"),
        ])
        result = await mod.async_test()
        assert "media_player.kitchen" in result["message"]
        assert "media_player.living" in result["message"]


class TestClimateModule:
    """Tests for the REAL ClimateModule (custom_components.secure_me.modules.climate).

    This module had no dedicated test coverage at all before this session.
    """

    def _make_climate(self, hass, climates=None, away_temperature=None):
        from custom_components.secure_me.modules.climate import ClimateModule
        return ClimateModule(hass, {
            "climates": climates or [], "away_temperature": away_temperature,
        })

    @pytest.mark.asyncio
    async def test_available_climate_with_away_preset_passes(self, mock_hass):
        mock_hass.set_state("climate.living", "heat", {
            "preset_modes": ["home", "away"], "preset_mode": "home",
            "current_temperature": 21, "temperature": 21,
        })
        mod = self._make_climate(mock_hass, climates=["climate.living"])
        result = await mod.async_test()
        assert result["success"] is True
        info = result["details"]["climates"][0]
        assert info["available"] is True
        assert info["preset_modes"] == ["home", "away"]

    @pytest.mark.asyncio
    async def test_unavailable_climate_fails_test(self, mock_hass):
        mock_hass.set_state("climate.living", "unavailable")
        mod = self._make_climate(mock_hass, climates=["climate.living"])
        result = await mod.async_test()
        assert result["success"] is False
        assert "Climate" in result["message"]

    @pytest.mark.asyncio
    async def test_climate_without_away_support_or_temperature_is_informational_only(self, mock_hass):
        """No 'away' preset and no away_temperature configured -- this is a
        non-fatal note, surfaced via results["warnings"] (like lock.py's
        battery-low warning), not a test failure and not part of
        results["message"] (which is reserved for real failures).
        """
        mock_hass.set_state("climate.living", "heat", {"preset_modes": ["home"]})
        mod = self._make_climate(mock_hass, climates=["climate.living"])
        result = await mod.async_test()
        assert result["success"] is True
        assert any("does not support away mode" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_climate_with_away_temperature_configured_no_warning(self, mock_hass):
        mock_hass.set_state("climate.living", "heat", {"preset_modes": ["home"]})
        mod = self._make_climate(mock_hass, climates=["climate.living"], away_temperature=16)
        result = await mod.async_test()
        assert result["message"] == "Climate module test passed"

    @pytest.mark.asyncio
    async def test_multiple_unavailable_climates_all_appear_in_summary_message(self, mock_hass):
        """Regression: only the LAST issue used to survive in results['message']."""
        mock_hass.set_state("climate.living", "unavailable")
        mock_hass.set_state("climate.bedroom", "unavailable")
        mod = self._make_climate(mock_hass, climates=["climate.living", "climate.bedroom"])
        result = await mod.async_test()
        assert "climate.living" in result["message"]
        assert "climate.bedroom" in result["message"]

    @pytest.mark.asyncio
    async def test_missing_climate_state_handled_gracefully(self, mock_hass):
        """Entity not in HA states at all -- must not raise, must report unavailable."""
        mod = self._make_climate(mock_hass, climates=["climate.missing"])
        result = await mod.async_test()
        assert result["success"] is False
        info = result["details"]["climates"][0]
        assert info["available"] is False
        assert info["current_temperature"] is None
        assert info["preset_modes"] == []
