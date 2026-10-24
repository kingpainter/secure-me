"""Tests for NFC tag handling in SecureMeCoordinator.async_listen_nfc_events.

The tag_scanned handler is a closure created inside async_listen_nfc_events,
so these tests capture it from the mocked hass bus and invoke it directly.
The coordinator is built with __new__ to skip the heavy HA setup; only the
attributes the handler touches are populated.
"""
# VERSION = "2.2.0"

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from custom_components.secure_me.const import (
    EVENT_SECURE_ME_TAG_SCANNED,
    NFC_ACTION_ARM_AWAY,
    NFC_ACTION_DISARM,
)
from custom_components.secure_me.coordinator import SecureMeCoordinator


def _make_coordinator(tags: dict, auth_result=None, disarm_result=True):
    coord = SecureMeCoordinator.__new__(SecureMeCoordinator)
    coord._nfc_unsub = None
    coord.hass = MagicMock()
    coord.store = MagicMock()
    coord.store.get_nfc_tags.return_value = tags
    coord.store.authenticate_user_with_id.return_value = auth_result
    coord.state_machine = MagicMock(current_state="disarmed")
    coord.async_disarm = AsyncMock(return_value=disarm_result)
    coord.async_arm_away = AsyncMock(return_value=True)
    return coord


async def _scan(coord, tag_id: str, data: dict | None = None) -> dict:
    """Register the listener, simulate a tag_scan, return the fired payload."""
    await coord.async_listen_nfc_events()
    handler = coord.hass.bus.async_listen.call_args[0][1]
    event = MagicMock()
    event.data = {"tag_id": tag_id, **(data or {})}
    await handler(event)
    event_name, payload = coord.hass.bus.async_fire.call_args[0]
    assert event_name == EVENT_SECURE_ME_TAG_SCANNED
    return payload


async def test_unregistered_tag_is_ignored():
    coord = _make_coordinator(tags={})
    await coord.async_listen_nfc_events()
    handler = coord.hass.bus.async_listen.call_args[0][1]
    event = MagicMock()
    event.data = {"tag_id": "unknown"}
    await handler(event)

    coord.async_disarm.assert_not_called()
    coord.hass.bus.async_fire.assert_not_called()


async def test_pinless_tag_disarms_without_code_check():
    tags = {"t1": {"action": NFC_ACTION_DISARM, "name": "Phone"}}
    coord = _make_coordinator(tags)

    payload = await _scan(coord, "t1")

    coord.async_disarm.assert_awaited_once_with(code=None, skip_code=True)
    assert payload["success"] is True
    assert payload["pin_required"] is False
    assert payload["pin_verified"] is None


async def test_pin_tag_without_code_does_nothing():
    tags = {
        "t1": {
            "action": NFC_ACTION_DISARM,
            "name": "Keychain",
            "requires_pin": True,
        }
    }
    coord = _make_coordinator(tags)

    payload = await _scan(coord, "t1")

    coord.async_disarm.assert_not_called()
    assert payload["success"] is False
    assert payload["pin_required"] is True
    assert payload["pin_verified"] is False
    assert payload["error"] == "PIN required for this tag"


async def test_pin_tag_with_wrong_pin_is_rejected():
    tags = {
        "t1": {
            "action": NFC_ACTION_DISARM,
            "name": "Keychain",
            "requires_pin": True,
        }
    }
    coord = _make_coordinator(tags, auth_result=None)

    payload = await _scan(coord, "t1", {"code": "0000"})

    coord.async_disarm.assert_not_called()
    assert payload["pin_verified"] is False
    assert payload["error"] == "Invalid PIN"
    # The PIN must never leak into the fired event.
    assert "0000" not in str(payload)


async def test_pin_tag_with_correct_pin_disarms():
    tags = {
        "t1": {
            "action": NFC_ACTION_DISARM,
            "name": "Keychain",
            "requires_pin": True,
        }
    }
    coord = _make_coordinator(tags, auth_result=("user-1", {"name": "Flemming"}))

    payload = await _scan(coord, "t1", {"code": "1234"})

    coord.async_disarm.assert_awaited_once_with(code="1234", skip_code=True)
    assert payload["pin_verified"] is True
    assert payload["success"] is True
    assert "1234" not in str(payload)


async def test_arm_away_tag_arms_without_pin():
    tags = {"t2": {"action": NFC_ACTION_ARM_AWAY, "name": "Sticker"}}
    coord = _make_coordinator(tags)

    payload = await _scan(coord, "t2")

    coord.async_arm_away.assert_awaited_once_with(code=None)
    assert payload["success"] is True


async def test_rejected_disarm_reports_failure():
    tags = {"t1": {"action": NFC_ACTION_DISARM, "name": "Phone"}}
    coord = _make_coordinator(tags, disarm_result=False)

    payload = await _scan(coord, "t1")

    assert payload["success"] is False
    assert payload["error"] == "Command rejected by alarm state"
