"""Home Assistant services for Secure Me.
# VERSION = "1.5.5"

Registers the secure_me.* services documented in services.yaml, wiring each
one to the same coordinator methods used by the alarm_control_panel entity
and the frontend websocket API.

Why this file exists (v1.5.0 API audit):
services.yaml has documented arm_away / arm_home / arm_night / arm_vacation /
disarm / trigger / run_test / enable_module / disable_module since early
versions, but no hass.services.async_register() call ever backed them --
calling e.g. secure_me.arm_away from Developer Tools or an automation failed
with "service not found". This file closes that gap so the documented
contract is real.

secure_me.arm_home_alone is also registered here (and now documented in
services.yaml) even though HA's alarm_control_panel interface has no
standard command for it, so automations have one documented, versioned way
to trigger the one genuinely non-standard mode -- instead of only the
frontend websocket command `secure_me/arm_home_alone`.
"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_ARM_AWAY,
    SERVICE_ARM_HOME,
    SERVICE_ARM_NIGHT,
    SERVICE_ARM_VACATION,
    SERVICE_ARM_HOME_ALONE,
    SERVICE_DISARM,
    SERVICE_TRIGGER,
    SERVICE_RUN_TEST,
    ATTR_CODE,
    ATTR_TEST_TYPE,
    EVENT_MODULE_ENABLED,
    EVENT_MODULE_DISABLED,
)
from .ws_helpers import _get_coordinator, _get_store

_LOGGER = logging.getLogger(__name__)

SERVICE_ENABLE_MODULE = "enable_module"
SERVICE_DISABLE_MODULE = "disable_module"

ATTR_SKIP_DELAY = "skip_delay"
ATTR_FORCE = "force"
ATTR_SOURCE = "source"
ATTR_MODULE_ID = "module_id"

_MODULE_IDS = ("camera", "lock", "lights", "climate", "siren", "tts")

_ARM_SCHEMA = vol.Schema({
    vol.Optional(ATTR_CODE): cv.string,
    vol.Optional(ATTR_SKIP_DELAY, default=False): cv.boolean,
    vol.Optional(ATTR_FORCE, default=False): cv.boolean,
})

_DISARM_SCHEMA = vol.Schema({
    vol.Required(ATTR_CODE): cv.string,
})

_TRIGGER_SCHEMA = vol.Schema({
    vol.Optional(ATTR_SOURCE, default="manual"): cv.string,
})

_RUN_TEST_SCHEMA = vol.Schema({
    vol.Required(ATTR_TEST_TYPE): vol.In(["quick", "standard", "full"]),
})

_MODULE_SCHEMA = vol.Schema({
    vol.Required(ATTR_MODULE_ID): vol.In(_MODULE_IDS),
})


def async_register_services(hass: HomeAssistant) -> None:
    """Register all secure_me.* services.

    Called once globally from __init__.py (guarded the same way as the
    websocket API registration), not per config entry.
    """

    async def _handle_arm_away(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("secure_me.arm_away: coordinator not ready")
            return
        await coordinator.async_arm_away(
            code=call.data.get(ATTR_CODE),
            skip_delay=call.data.get(ATTR_SKIP_DELAY, False),
            force=call.data.get(ATTR_FORCE, False),
        )

    async def _handle_arm_home(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("secure_me.arm_home: coordinator not ready")
            return
        await coordinator.async_arm_home(
            code=call.data.get(ATTR_CODE),
            skip_delay=call.data.get(ATTR_SKIP_DELAY, False),
            force=call.data.get(ATTR_FORCE, False),
        )

    async def _handle_arm_night(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("secure_me.arm_night: coordinator not ready")
            return
        await coordinator.async_arm_night(
            code=call.data.get(ATTR_CODE),
            skip_delay=call.data.get(ATTR_SKIP_DELAY, False),
            force=call.data.get(ATTR_FORCE, False),
        )

    async def _handle_arm_vacation(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("secure_me.arm_vacation: coordinator not ready")
            return
        await coordinator.async_arm_vacation(
            code=call.data.get(ATTR_CODE),
            skip_delay=call.data.get(ATTR_SKIP_DELAY, False),
            force=call.data.get(ATTR_FORCE, False),
        )

    async def _handle_arm_home_alone(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("secure_me.arm_home_alone: coordinator not ready")
            return
        await coordinator.async_arm_home_alone(
            code=call.data.get(ATTR_CODE),
            skip_delay=call.data.get(ATTR_SKIP_DELAY, False),
            force=call.data.get(ATTR_FORCE, False),
        )

    async def _handle_disarm(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("secure_me.disarm: coordinator not ready")
            return
        await coordinator.async_disarm(code=call.data.get(ATTR_CODE))

    async def _handle_trigger(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("secure_me.trigger: coordinator not ready")
            return
        await coordinator.async_trigger(source=call.data.get(ATTR_SOURCE, "manual"))

    async def _handle_run_test(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass)
        if not coordinator:
            _LOGGER.error("secure_me.run_test: coordinator not ready")
            return
        # Imported inline (mirrors coordinator.py's own scheduled-test call)
        # to avoid a circular import at module load time.
        from .ws_modules import _run_test_internal
        await _run_test_internal(hass, call.data[ATTR_TEST_TYPE])

    async def _set_module_enabled(call: ServiceCall, enabled: bool) -> None:
        # Fix: HA services (unlike websocket commands) have no built-in
        # require_admin concept -- any user/automation with access to call
        # this service could silently disable a module (e.g. the siren)
        # with no admin check at all. Mirror websocket_api.require_admin's
        # behaviour manually via the calling user's HA permissions.
        if call.context.user_id:
            user = await hass.auth.async_get_user(call.context.user_id)
            if user is not None and not user.is_admin:
                _LOGGER.warning(
                    "secure_me.%s rejected -- user '%s' is not a HA admin",
                    SERVICE_ENABLE_MODULE if enabled else SERVICE_DISABLE_MODULE,
                    user.name,
                )
                return
        module_id = call.data[ATTR_MODULE_ID]
        store = _get_store(hass)
        coordinator = _get_coordinator(hass)
        if not store or not coordinator:
            _LOGGER.error("secure_me: store/coordinator not ready")
            return
        config = dict(store.get_modules().get(module_id, {}))
        config["enabled"] = enabled
        await store.async_save_module(module_id, config)
        # Mirror ws_save_module's behaviour exactly: the store holds the
        # panel's object format (e.g. cameras: [{entity_id, poe_port}]), but
        # module classes expect flat entity_id string lists. Skipping this
        # normalization step would silently break the module's entity
        # extraction (cameras/locks/climates/lights/media_players) the next
        # time it's used, since update_module_config() re-instantiates the
        # module class directly from whatever config it's given.
        from .ws_modules import _normalize_module_config
        normalized = _normalize_module_config(module_id, config)
        coordinator.update_module_config(module_id, normalized)
        hass.bus.async_fire(
            EVENT_MODULE_ENABLED if enabled else EVENT_MODULE_DISABLED,
            {"module": module_id},
        )
        _LOGGER.info(
            "Module '%s' %s via secure_me.%s service",
            module_id, "enabled" if enabled else "disabled",
            SERVICE_ENABLE_MODULE if enabled else SERVICE_DISABLE_MODULE,
        )

    async def _handle_enable_module(call: ServiceCall) -> None:
        await _set_module_enabled(call, True)

    async def _handle_disable_module(call: ServiceCall) -> None:
        await _set_module_enabled(call, False)

    hass.services.async_register(DOMAIN, SERVICE_ARM_AWAY, _handle_arm_away, schema=_ARM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ARM_HOME, _handle_arm_home, schema=_ARM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ARM_NIGHT, _handle_arm_night, schema=_ARM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ARM_VACATION, _handle_arm_vacation, schema=_ARM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ARM_HOME_ALONE, _handle_arm_home_alone, schema=_ARM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DISARM, _handle_disarm, schema=_DISARM_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_TRIGGER, _handle_trigger, schema=_TRIGGER_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_RUN_TEST, _handle_run_test, schema=_RUN_TEST_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_MODULE, _handle_enable_module, schema=_MODULE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_MODULE, _handle_disable_module, schema=_MODULE_SCHEMA)

    _LOGGER.info("Secure Me services registered (%d services)", 10)


def async_unregister_services(hass: HomeAssistant) -> None:
    """Remove all secure_me.* services (called when the last config entry unloads)."""
    for service in (
        SERVICE_ARM_AWAY, SERVICE_ARM_HOME, SERVICE_ARM_NIGHT, SERVICE_ARM_VACATION,
        SERVICE_ARM_HOME_ALONE, SERVICE_DISARM, SERVICE_TRIGGER, SERVICE_RUN_TEST,
        SERVICE_ENABLE_MODULE, SERVICE_DISABLE_MODULE,
    ):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
