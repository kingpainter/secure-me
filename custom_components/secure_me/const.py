"""Constants for Secure Me integration."""
# VERSION = "0.0.1"

from homeassistant.const import Platform

# Integration domain
DOMAIN = "secure_me"

# Version
VERSION = "0.0.1"

# Platforms
PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]

# Configuration
CONF_CODE = "code"
CONF_EXIT_DELAY = "exit_delay"
CONF_ENTRY_DELAY = "entry_delay"
CONF_TRIGGER_TIME = "trigger_time"

# Defaults
DEFAULT_EXIT_DELAY = 30
DEFAULT_ENTRY_DELAY = 30
DEFAULT_TRIGGER_TIME = 300  # 5 minutes

# Alarm states
STATE_ALARM_DISARMED = "disarmed"
STATE_ALARM_ARMING = "arming"
STATE_ALARM_ARMED_AWAY = "armed_away"
STATE_ALARM_ARMED_HOME = "armed_home"
STATE_ALARM_ARMED_NIGHT = "armed_night"
STATE_ALARM_ARMED_VACATION = "armed_vacation"
STATE_ALARM_PENDING = "pending"
STATE_ALARM_TRIGGERED = "triggered"

# Module types
MODULE_CAMERA = "camera"
MODULE_LOCK = "lock"
MODULE_LIGHTS = "lights"
MODULE_CLIMATE = "climate"
MODULE_CURTAINS = "curtains"
MODULE_WATER_LEAK = "water_leak"
MODULE_SIREN = "siren"
MODULE_TTS = "tts"

# Events
EVENT_ALARM_ARMED = f"{DOMAIN}_armed"
EVENT_ALARM_DISARMED = f"{DOMAIN}_disarmed"
EVENT_ALARM_TRIGGERED = f"{DOMAIN}_triggered"
EVENT_ALARM_TEST_STARTED = f"{DOMAIN}_test_started"
EVENT_ALARM_TEST_COMPLETED = f"{DOMAIN}_test_completed"

# Services
SERVICE_ARM_AWAY = "arm_away"
SERVICE_ARM_HOME = "arm_home"
SERVICE_ARM_NIGHT = "arm_night"
SERVICE_ARM_VACATION = "arm_vacation"
SERVICE_DISARM = "disarm"
SERVICE_TRIGGER = "trigger"
SERVICE_RUN_TEST = "run_test"

# Attributes
ATTR_CODE = "code"
ATTR_MODE = "mode"
ATTR_TEST_TYPE = "test_type"
ATTR_ZONES = "zones"
ATTR_MODULES = "modules"
ATTR_HEALTH_SCORE = "health_score"
ATTR_BATTERY_LEVEL = "battery_level"
