"""Admin gating for websocket commands that must not be open to non-admin users.

Covers the 23 read-only get_* commands and skip_delay. A non-admin caller must
be rejected by require_admin before the handler body runs. An admin caller
must pass the gate.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.exceptions import Unauthorized

from custom_components.secure_me import ws_alarm, ws_floorplan, ws_modules, ws_sensors

PROTECTED_HANDLERS: list[tuple[str, str]] = [
    ("ws_alarm", "ws_skip_delay"),
    ("ws_alarm", "ws_get_speaker_profiles"),
    ("ws_alarm", "ws_get_home_alone_messages"),
    ("ws_alarm", "ws_get_auto_actions"),
    ("ws_alarm", "ws_get_fake_presence_v2"),
    ("ws_floorplan", "ws_get_floorplan"),
    ("ws_modules", "ws_get_modules"),
    ("ws_modules", "ws_get_module_entities"),
    ("ws_modules", "ws_get_notifications"),
    ("ws_modules", "ws_get_notify_services"),
    ("ws_modules", "ws_get_automations"),
    ("ws_modules", "ws_get_health_summary"),
    ("ws_modules", "ws_get_scheduled_tests"),
    ("ws_modules", "ws_get_test_results"),
    ("ws_modules", "ws_get_fake_presence"),
    ("ws_modules", "ws_get_home_alone_cameras"),
    ("ws_sensors", "ws_get_sensor_groups"),
    ("ws_sensors", "ws_get_alarm_state"),
    ("ws_sensors", "ws_get_sensors"),
    ("ws_sensors", "ws_get_zones"),
    ("ws_sensors", "ws_get_users"),
    ("ws_sensors", "ws_get_nfc_tags"),
    ("ws_sensors", "ws_get_ha_nfc_tags"),
    ("ws_sensors", "ws_get_persons"),
]


_MODULES = {
    "ws_alarm": ws_alarm,
    "ws_floorplan": ws_floorplan,
    "ws_modules": ws_modules,
    "ws_sensors": ws_sensors,
}


def _handler(module_name: str, handler_name: str):
    return getattr(_MODULES[module_name], handler_name)


class _Connection:
    """Minimal stand-in for websocket_api.ActiveConnection."""

    def __init__(self, is_admin: bool) -> None:
        self.send_result = MagicMock()
        self.send_error = MagicMock()
        self.user = MagicMock()
        self.user.is_admin = is_admin
        self.async_handle_exception = MagicMock()


def test_protected_list_is_complete() -> None:
    """Guard against the list drifting: 23 get_* commands plus skip_delay."""
    assert len(PROTECTED_HANDLERS) == 24
    get_commands = [name for _, name in PROTECTED_HANDLERS if name.startswith("ws_get_")]
    assert len(get_commands) == 23


@pytest.mark.parametrize(("module_name", "handler_name"), PROTECTED_HANDLERS)
@pytest.mark.asyncio
async def test_non_admin_is_rejected(hass, module_name, handler_name):
    handler = _handler(module_name, handler_name)
    connection = _Connection(is_admin=False)

    with pytest.raises(Unauthorized):
        handler(hass, connection, {"id": 1})

    connection.send_result.assert_not_called()
    await hass.async_block_till_done(wait_background_tasks=True)


@pytest.mark.parametrize(("module_name", "handler_name"), PROTECTED_HANDLERS)
@pytest.mark.asyncio
async def test_admin_passes_gate(hass, module_name, handler_name):
    handler = _handler(module_name, handler_name)
    connection = _Connection(is_admin=True)

    # The gate must not raise for an admin. Handler errors are reported by
    # async_response on the connection, so they do not surface here.
    handler(hass, connection, {"id": 1})
    await hass.async_block_till_done(wait_background_tasks=True)
