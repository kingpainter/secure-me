"""Tests for Secure Me constants."""
# VERSION = "1.5.0"

import pytest

from custom_components.secure_me.const import (
    DOMAIN,
    VERSION,
    PLATFORMS,
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    DEFAULT_EXIT_DELAY,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_TRIGGER_TIME,
    MODULE_CAMERA,
    MODULE_LOCK,
    MODULE_LIGHTS,
    MODULE_CLIMATE,
    MODULE_SIREN,
    MODULE_TTS,
    ZONE_TYPE_ENTRY,
    ZONE_TYPE_INSTANT,
    ZONE_TYPE_INTERIOR,
    ZONE_TYPE_PERIMETER,
)


class TestConstants:
    """Test constants are properly defined."""

    def test_domain(self):
        assert DOMAIN == "secure_me"

    def test_version_format(self):
        parts = VERSION.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()

    def test_version_is_current(self):
        """VERSION constant must match manifest.json (single source of truth)."""
        import json
        from pathlib import Path
        manifest_path = Path(__file__).parent.parent / "custom_components" / "secure_me" / "manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        assert VERSION == manifest["version"], (
            f"VERSION constant ({VERSION}) does not match manifest.json "
            f"({manifest['version']}). Bump both or run validate_version.py --fix."
        )

    def test_platforms_not_empty(self):
        assert len(PLATFORMS) > 0

    def test_platforms_include_alarm_panel(self):
        platform_values = [p.value if hasattr(p, "value") else str(p) for p in PLATFORMS]
        assert "alarm_control_panel" in platform_values

    def test_all_alarm_states_defined(self):
        states = [
            STATE_ALARM_DISARMED,
            STATE_ALARM_ARMING,
            STATE_ALARM_ARMED_AWAY,
            STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT,
            STATE_ALARM_ARMED_VACATION,
            STATE_ALARM_PENDING,
            STATE_ALARM_TRIGGERED,
        ]
        assert len(states) == 8
        assert len(set(states)) == 8  # All unique

    def test_default_delays_positive(self):
        assert DEFAULT_EXIT_DELAY > 0
        assert DEFAULT_ENTRY_DELAY > 0
        assert DEFAULT_TRIGGER_TIME > 0

    def test_default_trigger_time_is_5_minutes(self):
        assert DEFAULT_TRIGGER_TIME == 300

    def test_all_modules_defined(self):
        modules = [MODULE_CAMERA, MODULE_LOCK, MODULE_LIGHTS,
                   MODULE_CLIMATE, MODULE_SIREN, MODULE_TTS]
        assert len(modules) == 6
        assert len(set(modules)) == 6

    def test_all_zone_types_defined(self):
        zone_types = [ZONE_TYPE_ENTRY, ZONE_TYPE_INSTANT,
                      ZONE_TYPE_INTERIOR, ZONE_TYPE_PERIMETER]
        assert len(zone_types) == 4
        assert len(set(zone_types)) == 4

    def test_event_names_use_domain_prefix(self):
        from custom_components.secure_me.const import (
            EVENT_ALARM_ARMED,
            EVENT_ALARM_DISARMED,
            EVENT_ALARM_TRIGGERED,
        )
        assert EVENT_ALARM_ARMED.startswith(DOMAIN)
        assert EVENT_ALARM_DISARMED.startswith(DOMAIN)
        assert EVENT_ALARM_TRIGGERED.startswith(DOMAIN)

    def test_fake_presence_constants_defined(self):
        from custom_components.secure_me.const import (
            CONF_FAKE_PRESENCE,
            CONF_HOME_ALONE_CAMERAS,
            NOTIFY_ID_FAKE_PRESENCE,
            EVENT_FAKE_PRESENCE_CHANGED,
        )
        assert CONF_FAKE_PRESENCE == "fake_presence"
        assert CONF_HOME_ALONE_CAMERAS == "home_alone_cameras"
        assert NOTIFY_ID_FAKE_PRESENCE == "secure_me_fake_presence"
        assert EVENT_FAKE_PRESENCE_CHANGED.startswith(DOMAIN)

    def test_auto_actions_v2_constants_defined(self):
        from custom_components.secure_me.const import (
            CONF_AUTO_ACTIONS,
            AA_LOCK_ENABLED, AA_LOCK_DELAY,
            AA_ALARM_ENABLED, AA_ALARM_DELAY,
            AA_CAMERA_ENABLED, AA_CAMERA_DELAY,
            AA_ARRIVAL_DELAY, AA_NOTIFY_ALL,
            DEFAULT_AA_LOCK_DELAY, DEFAULT_AA_ALARM_DELAY,
            DEFAULT_AA_CAMERA_DELAY, DEFAULT_AA_ARRIVAL_DELAY,
            FP_ACTIVE, FP_BLOCK_ALARM, FP_BLOCK_LOCKS, FP_BLOCK_CAMERAS,
            EVENT_HOME_EMPTY, EVENT_PERSON_HOME, EVENT_AUTO_ACTION_DONE,
            NOTIFY_ID_AUTO_ACTIONS,
        )
        assert CONF_AUTO_ACTIONS == "auto_actions"
        assert AA_LOCK_ENABLED == "auto_lock_enabled"
        assert AA_ALARM_DELAY == "auto_alarm_delay"
        assert DEFAULT_AA_LOCK_DELAY == 120
        assert DEFAULT_AA_ALARM_DELAY == 300
        assert DEFAULT_AA_CAMERA_DELAY == 0
        assert DEFAULT_AA_ARRIVAL_DELAY == 60
        assert FP_ACTIVE == "active"
        assert FP_BLOCK_ALARM == "block_alarm"
        assert FP_BLOCK_LOCKS == "block_locks"
        assert FP_BLOCK_CAMERAS == "block_cameras"
        assert EVENT_HOME_EMPTY.startswith(DOMAIN)
        assert EVENT_PERSON_HOME.startswith(DOMAIN)
        assert EVENT_AUTO_ACTION_DONE.startswith(DOMAIN)
        assert NOTIFY_ID_AUTO_ACTIONS == "secure_me_auto_actions"
