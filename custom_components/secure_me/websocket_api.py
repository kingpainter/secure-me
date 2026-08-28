"""WebSocket API for Secure Me panel.

This module is the registration entry point only. All command handlers
live in the focused sub-modules below (split out of this file so it no
longer duplicates their logic):
  - ws_sensors.py   -- sensors, zones, users, sensor groups, alarm state
  - ws_modules.py   -- modules, notifications, automations, tests, health,
                       fake presence (legacy), home alone cameras
  - ws_floorplan.py -- floorplan image + rooms/openings/markers
  - ws_alarm.py     -- arm/disarm, speaker profiles, auto actions v2,
                       fake presence v2

This file just imports and registers them, and starts the notification
dispatcher.
"""
# VERSION = "1.5.5"
from __future__ import annotations

import logging

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .notification_dispatcher import async_setup_dispatcher

from .ws_sensors import (
    ws_get_sensor_groups,
    ws_save_sensor_group,
    ws_delete_sensor_group,
    ws_get_alarm_state,
    ws_get_sensors,
    ws_save_sensors,
    ws_get_zones,
    ws_save_zone,
    ws_delete_zone,
    ws_get_users,
    ws_save_user,
    ws_delete_user,
    ws_get_nfc_tags,
    ws_get_persons,
    ws_hide_sensor,
    ws_unmark_environmental,
)
from .ws_modules import (
    ws_get_modules,
    ws_save_module,
    ws_get_module_entities,
    ws_get_notifications,
    ws_save_notification,
    ws_delete_notification,
    ws_test_notification,
    ws_get_notify_services,
    ws_test_tts,
    ws_get_automations,
    ws_save_automation,
    ws_delete_automation,
    ws_test_automation,
    ws_get_health_summary,
    ws_run_test,
    ws_quick_test_siren,
    ws_quick_test_lights,
    ws_get_scheduled_tests,
    ws_save_scheduled_test,
    ws_delete_scheduled_test,
    ws_run_scheduled_test_now,
    ws_get_test_results,
    ws_get_fake_presence,
    ws_set_fake_presence,
    ws_get_home_alone_cameras,
    ws_save_home_alone_cameras,
)
from .ws_floorplan import (
    ws_get_floorplan,
    ws_save_floorplan_image,
    ws_save_floorplan_markers,
    ws_delete_floorplan,
)
from .ws_alarm import (
    ws_arm_away,
    ws_arm_home,
    ws_arm_night,
    ws_arm_vacation,
    ws_arm_home_alone,
    ws_disarm,
    ws_skip_delay,
    ws_get_speaker_profiles,
    ws_save_speaker_profiles,
    ws_get_home_alone_messages,
    ws_get_auto_actions,
    ws_save_auto_actions,
    ws_get_fake_presence_v2,
    ws_save_fake_presence_v2,
)

_LOGGER = logging.getLogger(__name__)


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register all websocket commands and start the notification dispatcher."""
    _registered_types: list[str] = []

    def _register(handler) -> None:
        """Register a command and record its type string for diagnostics.py.

        Fix: diagnostics.py has always read
        hass.data[f"{DOMAIN}_websocket_commands"] to report how many Secure
        Me commands are registered, but nothing ever wrote that key -- it
        silently reported 0 regardless of the ~50 real registrations below.
        Wrapping websocket_api.async_register_command() here (instead of
        changing every call site) fixes that with one change. HA's
        @websocket_command decorator sets handler._ws_command to the raw
        command-type string (e.g. "secure_me/save_zone"); fall back to the
        function name if that internal attribute isn't present.
        """
        websocket_api.async_register_command(hass, handler)
        cmd_type = getattr(handler, "_ws_command", None)
        _registered_types.append(cmd_type if isinstance(cmd_type, str) else getattr(handler, "__name__", "unknown"))

    _register(ws_get_sensors)
    _register(ws_save_sensors)
    _register(ws_hide_sensor)
    _register(ws_unmark_environmental)
    # Arm / disarm commands (used by alarm card for custom modes)
    _register(ws_arm_away)
    _register(ws_arm_home)
    _register(ws_arm_night)
    _register(ws_arm_vacation)
    _register(ws_arm_home_alone)
    _register(ws_disarm)
    _register(ws_skip_delay)  # v1.4.3
    # Speaker profiles (v1.4.0)
    _register(ws_get_speaker_profiles)
    _register(ws_save_speaker_profiles)
    # Home Alone quick messages for alarm card
    _register(ws_get_home_alone_messages)
    _register(ws_get_zones)
    _register(ws_save_zone)
    _register(ws_delete_zone)
    _register(ws_get_users)
    _register(ws_save_user)
    _register(ws_delete_user)
    _register(ws_get_nfc_tags)
    _register(ws_get_persons)
    _register(ws_get_modules)
    _register(ws_save_module)
    _register(ws_get_module_entities)
    _register(ws_get_notifications)
    _register(ws_save_notification)
    _register(ws_delete_notification)
    _register(ws_test_notification)
    _register(ws_get_notify_services)
    _register(ws_test_tts)
    # v1.2.0: sensor groups (anti-masking)
    _register(ws_get_sensor_groups)
    _register(ws_save_sensor_group)
    _register(ws_delete_sensor_group)
    _register(ws_get_automations)
    _register(ws_save_automation)
    _register(ws_delete_automation)
    _register(ws_test_automation)
    _register(ws_get_scheduled_tests)
    _register(ws_save_scheduled_test)
    _register(ws_delete_scheduled_test)
    _register(ws_run_scheduled_test_now)
    _register(ws_get_alarm_state)
    _register(ws_get_health_summary)
    _register(ws_run_test)
    _register(ws_quick_test_siren)
    _register(ws_quick_test_lights)
    _register(ws_get_test_results)
    _register(ws_get_fake_presence)
    _register(ws_set_fake_presence)
    _register(ws_get_home_alone_cameras)
    _register(ws_save_home_alone_cameras)
    # Auto Actions v2 (v1.5.0)
    _register(ws_get_auto_actions)
    _register(ws_save_auto_actions)
    _register(ws_get_fake_presence_v2)
    _register(ws_save_fake_presence_v2)
    # Floorplan (v1.5.0)
    _register(ws_get_floorplan)
    _register(ws_save_floorplan_image)
    _register(ws_save_floorplan_markers)
    _register(ws_delete_floorplan)

    hass.data[f"{DOMAIN}_websocket_commands"] = _registered_types

    # Start notification dispatcher (listens for alarm + sensor events)
    dispatcher = async_setup_dispatcher(hass)
    hass.data.setdefault(DOMAIN, {})["_notification_dispatcher"] = dispatcher

    _LOGGER.info("Secure Me WebSocket API registered (%d commands)", len(_registered_types))
