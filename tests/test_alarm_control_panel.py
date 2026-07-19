"""Tests for the alarm_control_panel entity's HA-state mapping.

Covers the revert of armed_home_alone from ARMED_CUSTOM_BYPASS back to its
own raw custom state string, so it can never collide with any other mode
that might occupy HA's single custom-bypass enum slot, and so Secure Me's
own frontend cards (which key off the raw 'armed_home_alone' string) work
without depending on the secure_me_mode fallback.
"""
# VERSION = "1.5.0"

from unittest.mock import MagicMock

from custom_components.secure_me.alarm_control_panel import SecureMeAlarmPanel
from custom_components.secure_me.const import (
    STATE_ALARM_ARMED_HOME_ALONE,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)


def _make_panel(alarm_state: str) -> SecureMeAlarmPanel:
    """Build a panel with just enough of a mock coordinator to read alarm_state."""
    coordinator = MagicMock()
    coordinator.alarm_state = alarm_state
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry"
    return SecureMeAlarmPanel(coordinator, config_entry)


def test_armed_home_alone_reports_raw_custom_string():
    """armed_home_alone must be its own distinct raw string, not shoehorned
    into AlarmControlPanelState.ARMED_CUSTOM_BYPASS.
    """
    panel = _make_panel(STATE_ALARM_ARMED_HOME_ALONE)
    assert panel.alarm_state == "armed_home_alone"
    # And it must NOT be the enum's custom-bypass member (the very collision
    # this revert exists to eliminate).
    from homeassistant.components.alarm_control_panel import AlarmControlPanelState
    assert panel.alarm_state != AlarmControlPanelState.ARMED_CUSTOM_BYPASS


def test_armed_vacation_still_uses_native_ha_enum():
    """Vacation must keep using the real ARMED_VACATION enum member
    (HA Core 2024.11+), completely unaffected by the home_alone revert.
    """
    from homeassistant.components.alarm_control_panel import AlarmControlPanelState
    panel = _make_panel(STATE_ALARM_ARMED_VACATION)
    assert panel.alarm_state == AlarmControlPanelState.ARMED_VACATION


def test_standard_states_unaffected():
    """The original HA states must remain untouched by this change."""
    from homeassistant.components.alarm_control_panel import AlarmControlPanelState
    cases = {
        STATE_ALARM_DISARMED: AlarmControlPanelState.DISARMED,
        STATE_ALARM_ARMED_AWAY: AlarmControlPanelState.ARMED_AWAY,
        STATE_ALARM_ARMED_HOME: AlarmControlPanelState.ARMED_HOME,
        STATE_ALARM_ARMED_NIGHT: AlarmControlPanelState.ARMED_NIGHT,
        STATE_ALARM_ARMING: AlarmControlPanelState.ARMING,
        STATE_ALARM_PENDING: AlarmControlPanelState.PENDING,
        STATE_ALARM_TRIGGERED: AlarmControlPanelState.TRIGGERED,
    }
    for secure_me_state, expected in cases.items():
        panel = _make_panel(secure_me_state)
        assert panel.alarm_state == expected, f"{secure_me_state} -> expected {expected}"


def test_unknown_state_falls_back_to_disarmed():
    """Any unrecognised coordinator state must fail safe to DISARMED."""
    from homeassistant.components.alarm_control_panel import AlarmControlPanelState
    panel = _make_panel("some_future_unknown_state")
    assert panel.alarm_state == AlarmControlPanelState.DISARMED
