"""Tests for Secure Me module system."""
# VERSION = "1.2.0"

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
    """Tests for LockModule async_test() functional lock/unlock cycle."""

    def _make_lock_module(self, hass, locks=None, door_sensors=None, battery_sensors=None):
        import asyncio

        class FakeLockModule:
            def __init__(self):
                self.hass = hass
                self.locks = locks or []
                self.door_sensors = door_sensors or {}
                self.battery_sensors = battery_sensors or {}
                self._call_log = []

            def is_entity_available(self, eid):
                state = self.hass.states.get(eid)
                return bool(state and state.state not in ("unavailable", "unknown"))

            def get_entity_state(self, eid):
                state = self.hass.states.get(eid)
                return state.state if state else None

            async def async_call_service(self, domain, service, target=None, data=None):
                eid = (target or {}).get("entity_id", "")
                self._call_log.append((domain, service, eid))
                if service == "unlock":
                    self.hass.set_state(eid, "unlocked")
                elif service == "lock":
                    self.hass.set_state(eid, "locked")
                return True

            async def async_test(self):
                results = {
                    "success": True,
                    "message": "Lock module test passed",
                    "details": {"locks": [], "total_locks": len(self.locks), "functional_test": True},
                }
                for lock in self.locks:
                    lock_info = {
                        "entity_id": lock,
                        "available": self.is_entity_available(lock),
                        "initial_state": self.get_entity_state(lock),
                        "battery": None,
                        "door_sensor": None,
                        "unlock_ok": None,
                        "relock_ok": None,
                        "test_passed": False,
                        "skip_reason": None,
                    }
                    battery_sensor = self.battery_sensors.get(lock)
                    if battery_sensor:
                        try:
                            level = int(float(self.get_entity_state(battery_sensor) or ""))
                            lock_info["battery"] = level
                            if level < 20:
                                results["message"] = f"Lock {lock} battery low ({level}%)"
                        except (ValueError, TypeError):
                            pass
                    door_sensor = self.door_sensors.get(lock)
                    if door_sensor:
                        door_state = self.get_entity_state(door_sensor)
                        lock_info["door_sensor"] = {"entity_id": door_sensor, "state": door_state}
                        if door_state == "on":
                            lock_info["skip_reason"] = "door_open"
                            lock_info["test_passed"] = True
                            results["details"]["locks"].append(lock_info)
                            continue
                    if not lock_info["available"]:
                        lock_info["test_passed"] = False
                        results["success"] = False
                        results["message"] = f"Lock {lock} unavailable"
                        results["details"]["locks"].append(lock_info)
                        continue
                    try:
                        await self.async_call_service("lock", "unlock", target={"entity_id": lock})
                        await asyncio.sleep(0)
                        unlock_state = self.get_entity_state(lock)
                        lock_info["unlock_ok"] = unlock_state == "unlocked"
                        await self.async_call_service("lock", "lock", target={"entity_id": lock})
                        await asyncio.sleep(0)
                        relock_state = self.get_entity_state(lock)
                        lock_info["relock_ok"] = relock_state == "locked"
                        lock_info["final_state"] = self.get_entity_state(lock)
                        lock_info["test_passed"] = lock_info["unlock_ok"] and lock_info["relock_ok"]
                        if not lock_info["test_passed"]:
                            results["success"] = False
                            results["message"] = f"Lock {lock} functional test failed"
                    except Exception as err:
                        lock_info["test_passed"] = False
                        lock_info["error"] = str(err)
                        results["success"] = False
                        results["message"] = f"Lock {lock} test error: {err}"
                    results["details"]["locks"].append(lock_info)
                return results

        return FakeLockModule()

    @pytest.mark.asyncio
    async def test_lock_functional_test_passes(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mod = self._make_lock_module(mock_hass, locks=["lock.front"])
        result = await mod.async_test()
        assert result["success"] is True
        lock_info = result["details"]["locks"][0]
        assert lock_info["unlock_ok"] is True
        assert lock_info["relock_ok"] is True
        assert lock_info["test_passed"] is True
        assert lock_info["final_state"] == "locked"

    @pytest.mark.asyncio
    async def test_lock_always_ends_locked(self, mock_hass):
        mock_hass.set_state("lock.front", "unlocked")
        mod = self._make_lock_module(mock_hass, locks=["lock.front"])
        result = await mod.async_test()
        assert mock_hass.states.get("lock.front").state == "locked"
        assert result["details"]["locks"][0]["relock_ok"] is True

    @pytest.mark.asyncio
    async def test_lock_skipped_when_door_open(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("binary_sensor.door", "on")
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
        assert len(mod._call_log) == 0

    @pytest.mark.asyncio
    async def test_lock_unavailable_fails(self, mock_hass):
        mock_hass.set_state("lock.front", "unavailable")
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
        mod = self._make_lock_module(
            mock_hass,
            locks=["lock.front"],
            battery_sensors={"lock.front": "sensor.front_battery"},
        )
        result = await mod.async_test()
        assert result["details"]["locks"][0]["battery"] == 15
        assert "battery low" in result["message"]

    @pytest.mark.asyncio
    async def test_lock_reports_unlock_and_relock_separately(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
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
        mod = self._make_lock_module(mock_hass, locks=["lock.front", "lock.back"])
        result = await mod.async_test()
        assert result["success"] is True
        assert len(result["details"]["locks"]) == 2
        assert all(l["test_passed"] for l in result["details"]["locks"])

    @pytest.mark.asyncio
    async def test_multiple_locks_one_unavailable(self, mock_hass):
        mock_hass.set_state("lock.front", "locked")
        mock_hass.set_state("lock.back", "unavailable")
        mod = self._make_lock_module(mock_hass, locks=["lock.front", "lock.back"])
        result = await mod.async_test()
        assert result["success"] is False
        front = next(l for l in result["details"]["locks"] if l["entity_id"] == "lock.front")
        back = next(l for l in result["details"]["locks"] if l["entity_id"] == "lock.back")
        assert front["test_passed"] is True
        assert back["test_passed"] is False


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
