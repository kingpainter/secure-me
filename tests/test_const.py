"""Tests for Secure Me constants."""
# VERSION = "1.0.0"

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

    def test_version_is_1_0_0(self):
        assert VERSION == "1.0.0"

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
