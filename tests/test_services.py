"""Tests for services.py -- the secure_me.* Home Assistant service registrations.

Covers a gap that had existed since v1.5.0: services.yaml documented
arm_away / arm_home / arm_night / arm_vacation / arm_home_alone / disarm /
trigger / run_test / enable_module / disable_module, and services.py backed
them with real hass.services.async_register() handlers, but no test ever
verified the registration actually happens, that each handler calls the
right coordinator method with the right arguments, that schema validation
enforces what services.yaml documents (e.g. disarm requires a code, run_test
requires a valid test_type), or that a not-yet-ready coordinator/store is
handled gracefully instead of raising.

These tests exercise the real async_register_services()/async_unregister_services()
functions against a real hass.services registry (via hass.services.async_call()),
per the project's testing rule: no mirror re-implementation of the
registration logic under test. The coordinator and store are lightweight
fakes -- not mirrors of services.py's own logic, just data-layer stand-ins.
"""
# VERSION = "1.5.5"

from unittest.mock import AsyncMock

import pytest

from custom_components.secure_me.services import (
    async_register_services,
    async_unregister_services,
)
from custom_components.secure_me.const import DOMAIN


class FakeServicesCoordinator:
    """Records every arm/disarm/trigger/module-config call made through it."""

    def __init__(self):
        self.calls: list[tuple] = []
        self.module_configs: dict[str, dict] = {}

    async def async_arm_away(self, code=None, skip_delay=False, force=False):
        self.calls.append(("arm_away", code, skip_delay, force))
        return True

    async def async_arm_home(self, code=None, skip_delay=False, force=False):
        self.calls.append(("arm_home", code, skip_delay, force))
        return True

    async def async_arm_night(self, code=None, skip_delay=False, force=False):
        self.calls.append(("arm_night", code, skip_delay, force))
        return True

    async def async_arm_vacation(self, code=None, skip_delay=False, force=False):
        self.calls.append(("arm_vacation", code, skip_delay, force))
        return True

    async def async_arm_home_alone(self, code=None, skip_delay=False, force=False):
        self.calls.append(("arm_home_alone", code, skip_delay, force))
        return True

    async def async_disarm(self, code=None):
        self.calls.append(("disarm", code))
        return True

    async def async_trigger(self, source=None):
        self.calls.append(("trigger", source))
        return True

    def update_module_config(self, module_id, config):
        self.module_configs[module_id] = config
        return True


class FakeServicesStore:
    """Minimal store stand-in exposing only what services.py reads/writes."""

    def __init__(self, modules=None):
        self._modules = modules or {}
        self.saved: list[tuple] = []

    def get_modules(self):
        return self._modules

    async def async_save_module(self, module_id, config):
        self.saved.append((module_id, dict(config)))
        self._modules[module_id] = config


def _wire(hass, coordinator=None, store=None):
    """Populate hass.data[DOMAIN] the way ws_helpers._get_coordinator/_get_store expect."""
    hass.data[DOMAIN] = {}
    if store is not None:
        hass.data[DOMAIN]["store"] = store
    if coordinator is not None:
        hass.data[DOMAIN]["some_entry_id"] = {"coordinator": coordinator}


# -----------------------------------------------------------------------------
# Registration / unregistration
# -----------------------------------------------------------------------------

class TestRegistration:
    @pytest.mark.asyncio
    async def test_all_ten_services_registered(self, hass):
        async_register_services(hass)

        expected = [
            "arm_away", "arm_home", "arm_night", "arm_vacation", "arm_home_alone",
            "disarm", "trigger", "run_test", "enable_module", "disable_module",
        ]
        for service in expected:
            assert hass.services.has_service(DOMAIN, service), f"{service} not registered"

    @pytest.mark.asyncio
    async def test_unregister_removes_all_services(self, hass):
        async_register_services(hass)
        async_unregister_services(hass)

        for service in (
            "arm_away", "arm_home", "arm_night", "arm_vacation", "arm_home_alone",
            "disarm", "trigger", "run_test", "enable_module", "disable_module",
        ):
            assert not hass.services.has_service(DOMAIN, service)

    @pytest.mark.asyncio
    async def test_unregister_is_safe_when_never_registered(self, hass):
        """Must not raise even if called before registration (e.g. failed setup)."""
        async_unregister_services(hass)  # should not raise


# -----------------------------------------------------------------------------
# Arm services -- all five share the same schema and argument shape
# -----------------------------------------------------------------------------

class TestArmServices:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("service,method_name", [
        ("arm_away", "arm_away"),
        ("arm_home", "arm_home"),
        ("arm_night", "arm_night"),
        ("arm_vacation", "arm_vacation"),
        ("arm_home_alone", "arm_home_alone"),
    ])
    async def test_arm_service_calls_matching_coordinator_method(self, hass, service, method_name):
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator)
        async_register_services(hass)

        await hass.services.async_call(
            DOMAIN, service,
            {"code": "1234", "skip_delay": True, "force": True},
            blocking=True,
        )

        assert coordinator.calls == [(method_name, "1234", True, True)]

    @pytest.mark.asyncio
    async def test_arm_away_defaults_without_code(self, hass):
        """code is optional on arm services; skip_delay/force default to False."""
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator)
        async_register_services(hass)

        await hass.services.async_call(DOMAIN, "arm_away", {}, blocking=True)

        assert coordinator.calls == [("arm_away", None, False, False)]

    @pytest.mark.asyncio
    async def test_arm_service_no_coordinator_does_not_raise(self, hass):
        """Coordinator not ready yet (e.g. mid-startup) -- handler must log and
        return quietly, not crash the service call."""
        _wire(hass)  # no coordinator, no store
        async_register_services(hass)

        await hass.services.async_call(DOMAIN, "arm_away", {}, blocking=True)  # must not raise


# -----------------------------------------------------------------------------
# Disarm -- code is Required, not Optional
# -----------------------------------------------------------------------------

class TestDisarmService:
    @pytest.mark.asyncio
    async def test_disarm_calls_coordinator_with_code(self, hass):
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator)
        async_register_services(hass)

        await hass.services.async_call(DOMAIN, "disarm", {"code": "1234"}, blocking=True)

        assert coordinator.calls == [("disarm", "1234")]

    @pytest.mark.asyncio
    async def test_disarm_without_code_is_rejected_by_schema(self, hass):
        """services.yaml documents code as required for disarm -- unlike the
        arm services, which don't require one. Enforced by _DISARM_SCHEMA's
        vol.Required(ATTR_CODE)."""
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator)
        async_register_services(hass)

        with pytest.raises(Exception):
            await hass.services.async_call(DOMAIN, "disarm", {}, blocking=True)

        assert coordinator.calls == []  # handler must never have been reached


# -----------------------------------------------------------------------------
# Trigger
# -----------------------------------------------------------------------------

class TestTriggerService:
    @pytest.mark.asyncio
    async def test_trigger_with_explicit_source(self, hass):
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator)
        async_register_services(hass)

        await hass.services.async_call(
            DOMAIN, "trigger", {"source": "test_harness"}, blocking=True
        )

        assert coordinator.calls == [("trigger", "test_harness")]

    @pytest.mark.asyncio
    async def test_trigger_defaults_source_to_manual(self, hass):
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator)
        async_register_services(hass)

        await hass.services.async_call(DOMAIN, "trigger", {}, blocking=True)

        assert coordinator.calls == [("trigger", "manual")]


# -----------------------------------------------------------------------------
# Run test -- test_type must be one of quick/standard/full
# -----------------------------------------------------------------------------

class TestRunTestService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_type", ["quick", "standard", "full"])
    async def test_run_test_accepts_valid_types(self, hass, monkeypatch, test_type):
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator)
        async_register_services(hass)

        mock_run = AsyncMock(return_value={"overall": "pass"})
        monkeypatch.setattr(
            "custom_components.secure_me.ws_modules._run_test_internal", mock_run
        )

        await hass.services.async_call(
            DOMAIN, "run_test", {"test_type": test_type}, blocking=True
        )

        mock_run.assert_awaited_once_with(hass, test_type)

    @pytest.mark.asyncio
    async def test_run_test_rejects_invalid_type(self, hass, monkeypatch):
        _wire(hass, coordinator=FakeServicesCoordinator())
        async_register_services(hass)

        mock_run = AsyncMock(return_value={"overall": "pass"})
        monkeypatch.setattr(
            "custom_components.secure_me.ws_modules._run_test_internal", mock_run
        )

        with pytest.raises(Exception):
            await hass.services.async_call(
                DOMAIN, "run_test", {"test_type": "extra_thorough"}, blocking=True
            )

        mock_run.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_run_test_requires_test_type(self, hass, monkeypatch):
        _wire(hass, coordinator=FakeServicesCoordinator())
        async_register_services(hass)

        mock_run = AsyncMock(return_value={"overall": "pass"})
        monkeypatch.setattr(
            "custom_components.secure_me.ws_modules._run_test_internal", mock_run
        )

        with pytest.raises(Exception):
            await hass.services.async_call(DOMAIN, "run_test", {}, blocking=True)


# -----------------------------------------------------------------------------
# enable_module / disable_module
# -----------------------------------------------------------------------------

class TestModuleEnableDisable:
    @pytest.mark.asyncio
    async def test_enable_module_saves_and_updates_coordinator(self, hass):
        store = FakeServicesStore(modules={"lock": {"enabled": False, "locks": []}})
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator, store=store)
        async_register_services(hass)

        await hass.services.async_call(
            DOMAIN, "enable_module", {"module_id": "lock"}, blocking=True
        )

        assert store.saved[-1][0] == "lock"
        assert store.saved[-1][1]["enabled"] is True
        assert coordinator.module_configs["lock"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_disable_module_saves_and_updates_coordinator(self, hass):
        store = FakeServicesStore(modules={"siren": {"enabled": True, "sirens": []}})
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator, store=store)
        async_register_services(hass)

        await hass.services.async_call(
            DOMAIN, "disable_module", {"module_id": "siren"}, blocking=True
        )

        assert store.saved[-1][0] == "siren"
        assert store.saved[-1][1]["enabled"] is False
        assert coordinator.module_configs["siren"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_enable_module_fires_event(self, hass):
        store = FakeServicesStore(modules={"camera": {"enabled": False}})
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator, store=store)
        async_register_services(hass)

        events = []
        hass.bus.async_listen("secure_me_module_enabled", lambda e: events.append(e.data))

        await hass.services.async_call(
            DOMAIN, "enable_module", {"module_id": "camera"}, blocking=True
        )
        await hass.async_block_till_done()

        assert events == [{"module": "camera"}]

    @pytest.mark.asyncio
    async def test_module_id_must_be_known(self, hass):
        """services.yaml/const.py only know about the six real module ids --
        an unrecognised module_id must be rejected by the schema, not silently
        create a bogus store entry."""
        store = FakeServicesStore()
        coordinator = FakeServicesCoordinator()
        _wire(hass, coordinator=coordinator, store=store)
        async_register_services(hass)

        with pytest.raises(Exception):
            await hass.services.async_call(
                DOMAIN, "enable_module", {"module_id": "not_a_real_module"}, blocking=True
            )

        assert store.saved == []

    @pytest.mark.asyncio
    async def test_enable_module_no_store_does_not_raise(self, hass):
        """Store not ready yet -- handler must log and return, not crash."""
        _wire(hass, coordinator=FakeServicesCoordinator())  # no store
        async_register_services(hass)

        await hass.services.async_call(
            DOMAIN, "enable_module", {"module_id": "lock"}, blocking=True
        )  # must not raise
