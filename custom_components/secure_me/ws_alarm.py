"""WebSocket API — Arm, Disarm and Special Feature commands for Secure Me."""
# VERSION = "1.5.3"
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


from .ws_helpers import _get_store, _get_coordinator  # noqa: F401


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_away",
    vol.Optional("code"): str,
    vol.Optional("force", default=False): bool,
})
@websocket_api.async_response
async def ws_arm_away(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in away mode via WebSocket.

    force=True skips the open-sensor check (bypass all open sensors).
    """
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    force = bool(msg.get("force", False))
    success = await coordinator.async_arm_away(code=code, force=force)
    bypassed = coordinator.bypassed_sensors if success and not force else []
    connection.send_result(msg["id"], {
        "success": success,
        "bypassed_sensors": bypassed,
    })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_home",
    vol.Optional("code"): str,
    vol.Optional("force", default=False): bool,
})
@websocket_api.async_response
async def ws_arm_home(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in home mode via WebSocket.

    force=True skips the open-sensor check (bypass all open sensors).
    """
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    force = bool(msg.get("force", False))
    success = await coordinator.async_arm_home(code=code, force=force)
    bypassed = coordinator.bypassed_sensors if success and not force else []
    connection.send_result(msg["id"], {
        "success": success,
        "bypassed_sensors": bypassed,
    })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_night",
    vol.Optional("code"): str,
})
@websocket_api.async_response
async def ws_arm_night(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in night mode via WebSocket."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    success = await coordinator.async_arm_night(code=code)
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_vacation",
    vol.Optional("code"): str,
})
@websocket_api.async_response
async def ws_arm_vacation(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in vacation mode via WebSocket."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    success = await coordinator.async_arm_vacation(code=code)
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/arm_home_alone",
    vol.Optional("code"): str,
})
@websocket_api.async_response
async def ws_arm_home_alone(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Arm in home alone mode via WebSocket."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    if not coordinator.validate_code(code):
        connection.send_error(msg["id"], "invalid_code", "Invalid code")
        return
    success = await coordinator.async_arm_home_alone(code=code)
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/disarm",
    vol.Optional("code"): str,
})
@websocket_api.async_response
async def ws_disarm(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Disarm via WebSocket."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    code = msg.get("code")
    success = await coordinator.async_disarm(code=code)
    connection.send_result(msg["id"], {"success": success})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/skip_delay",
})
@websocket_api.async_response
async def ws_skip_delay(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Skip active exit/entry countdown via WebSocket (v1.4.3).

    Returns success=True if a countdown was skipped, False if there was
    no active countdown to skip.
    """
    coordinator = _get_coordinator(hass)
    if not coordinator:
        connection.send_error(msg["id"], "coordinator_not_ready", "Coordinator not initialized")
        return
    success = await coordinator.async_skip_delay()
    connection.send_result(msg["id"], {"success": success})


#
# SPEAKER PROFILES (v1.4.0)
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_speaker_profiles",
})
@websocket_api.async_response
async def ws_get_speaker_profiles(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get all speaker profiles."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    profiles = store.get_speaker_profiles()
    # Enrich with current media_player state
    enriched = []
    for p in profiles:
        eid = p.get("entity_id", "")
        state = hass.states.get(eid)
        enriched.append({
            **p,
            "available": state is not None and state.state not in ("unavailable", "unknown"),
            "current_volume": state.attributes.get("volume_level") if state else None,
        })
    connection.send_result(msg["id"], {"profiles": enriched})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_speaker_profiles",
    vol.Required("profiles"): list,
})
@websocket_api.async_response
async def ws_save_speaker_profiles(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save speaker profiles and reload TTS module config."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return

    profiles = msg["profiles"]
    # Validate each profile has required fields
    for p in profiles:
        if not p.get("entity_id"):
            connection.send_error(msg["id"], "invalid_profile", "Each profile needs entity_id")
            return
        p.setdefault("name", p["entity_id"])
        p.setdefault("volume", 0.5)
        p.setdefault("tts_service", "tts.cloud_say")
        p.setdefault("tts_entity", "tts.home_assistant_cloud")

    await store.async_save_speaker_profiles(profiles)

    # Reload TTS module config so it picks up new profiles immediately
    coordinator = _get_coordinator(hass)
    if coordinator:
        tts = coordinator.modules.get("tts")
        if tts:
            tts._speaker_profiles = profiles
            _LOGGER.debug("TTS speaker profiles reloaded: %d profiles", len(profiles))

    connection.send_result(msg["id"], {"success": True, "count": len(profiles)})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_home_alone_messages",
})
@websocket_api.async_response
async def ws_get_home_alone_messages(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get Home Alone quick messages for the alarm card.

    Returns notifications with trigger=home_alone_action, formatted for
    the alarm card's quick-message buttons. Each message includes speaker
    preferences so the card can target the right speakers.
    """
    store = _get_store(hass)
    if not store:
        connection.send_result(msg["id"], {"messages": []})
        return

    messages = []
    for notif in store.get_notifications().values():
        if not notif.get("enabled", True):
            continue
        if notif.get("trigger") != "home_alone_action":
            continue
        messages.append({
            "label": notif.get("name", ""),
            "message": notif.get("message", ""),
            "speakers": notif.get("tts_speakers", []),
        })

    connection.send_result(msg["id"], {"messages": messages})


#
# AUTO ACTIONS v2
#

@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_auto_actions",
})
@websocket_api.async_response
async def ws_get_auto_actions(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get Auto Actions v2 configuration."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    connection.send_result(msg["id"], {"config": store.get_auto_actions()})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_auto_actions",
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_auto_actions(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save Auto Actions v2 configuration."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    await store.async_save_auto_actions(msg["config"])
    connection.send_result(msg["id"], {"success": True})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_fake_presence_v2",
})
@websocket_api.async_response
async def ws_get_fake_presence_v2(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Get Fake Presence v2 configuration dict."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    connection.send_result(msg["id"], {"config": store.get_fake_presence_v2()})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_fake_presence_v2",
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def ws_save_fake_presence_v2(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Save Fake Presence v2 configuration dict."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialized")
        return
    await store.async_save_fake_presence_v2(msg["config"])

    # Keep coordinator in sync via the proper async method
    coordinator = _get_coordinator(hass)
    if coordinator:
        await coordinator.async_set_fake_presence(msg["config"].get("active", False))

    connection.send_result(msg["id"], {"success": True, "config": store.get_fake_presence_v2()})