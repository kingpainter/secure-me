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
# VERSION = "1.5.3"
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
    websocket_api.async_register_command(hass, ws_get_sensors)
    websocket_api.async_register_command(hass, ws_save_sensors)
    websocket_api.async_register_command(hass, ws_hide_sensor)
    websocket_api.async_register_command(hass, ws_unmark_environmental)
    # Arm / disarm commands (used by alarm card for custom modes)
    websocket_api.async_register_command(hass, ws_arm_away)
    websocket_api.async_register_command(hass, ws_arm_home)
    websocket_api.async_register_command(hass, ws_arm_night)
    websocket_api.async_register_command(hass, ws_arm_vacation)
    websocket_api.async_register_command(hass, ws_arm_home_alone)
    websocket_api.async_register_command(hass, ws_disarm)
    websocket_api.async_register_command(hass, ws_skip_delay)  # v1.4.3
    # Speaker profiles (v1.4.0)
    websocket_api.async_register_command(hass, ws_get_speaker_profiles)
    websocket_api.async_register_command(hass, ws_save_speaker_profiles)
    # Home Alone quick messages for alarm card
    websocket_api.async_register_command(hass, ws_get_home_alone_messages)
    websocket_api.async_register_command(hass, ws_get_zones)
    websocket_api.async_register_command(hass, ws_save_zone)
    websocket_api.async_register_command(hass, ws_delete_zone)
    websocket_api.async_register_command(hass, ws_get_users)
    websocket_api.async_register_command(hass, ws_save_user)
    websocket_api.async_register_command(hass, ws_delete_user)
    websocket_api.async_register_command(hass, ws_get_nfc_tags)
    websocket_api.async_register_command(hass, ws_get_persons)
    websocket_api.async_register_command(hass, ws_get_modules)
    websocket_api.async_register_command(hass, ws_save_module)
    websocket_api.async_register_command(hass, ws_get_module_entities)
    websocket_api.async_register_command(hass, ws_get_notifications)
    websocket_api.async_register_command(hass, ws_save_notification)
    websocket_api.async_register_command(hass, ws_delete_notification)
    websocket_api.async_register_command(hass, ws_test_notification)
    websocket_api.async_register_command(hass, ws_get_notify_services)
    websocket_api.async_register_command(hass, ws_test_tts)
    # v1.2.0: sensor groups (anti-masking)
    websocket_api.async_register_command(hass, ws_get_sensor_groups)
    websocket_api.async_register_command(hass, ws_save_sensor_group)
    websocket_api.async_register_command(hass, ws_delete_sensor_group)
    websocket_api.async_register_command(hass, ws_get_automations)
    websocket_api.async_register_command(hass, ws_save_automation)
    websocket_api.async_register_command(hass, ws_delete_automation)
    websocket_api.async_register_command(hass, ws_test_automation)
    websocket_api.async_register_command(hass, ws_get_scheduled_tests)
    websocket_api.async_register_command(hass, ws_save_scheduled_test)
    websocket_api.async_register_command(hass, ws_delete_scheduled_test)
    websocket_api.async_register_command(hass, ws_run_scheduled_test_now)
    websocket_api.async_register_command(hass, ws_get_alarm_state)
    websocket_api.async_register_command(hass, ws_get_health_summary)
    websocket_api.async_register_command(hass, ws_run_test)
    websocket_api.async_register_command(hass, ws_quick_test_siren)
    websocket_api.async_register_command(hass, ws_quick_test_lights)
    websocket_api.async_register_command(hass, ws_get_test_results)
    websocket_api.async_register_command(hass, ws_get_fake_presence)
    websocket_api.async_register_command(hass, ws_set_fake_presence)
    websocket_api.async_register_command(hass, ws_get_home_alone_cameras)
    websocket_api.async_register_command(hass, ws_save_home_alone_cameras)
    # Auto Actions v2 (v1.5.0)
    websocket_api.async_register_command(hass, ws_get_auto_actions)
    websocket_api.async_register_command(hass, ws_save_auto_actions)
    websocket_api.async_register_command(hass, ws_get_fake_presence_v2)
    websocket_api.async_register_command(hass, ws_save_fake_presence_v2)
    # Floorplan (v1.5.0)
    websocket_api.async_register_command(hass, ws_get_floorplan)
    websocket_api.async_register_command(hass, ws_save_floorplan_image)
    websocket_api.async_register_command(hass, ws_save_floorplan_markers)
    websocket_api.async_register_command(hass, ws_delete_floorplan)

    # Start notification dispatcher (listens for alarm + sensor events)
    dispatcher = async_setup_dispatcher(hass)
    hass.data.setdefault(DOMAIN, {})["_notification_dispatcher"] = dispatcher

    _LOGGER.info("Secure Me WebSocket API registered")
