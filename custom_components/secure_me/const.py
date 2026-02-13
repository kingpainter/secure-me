"""Constants for Secure Me integration."""
# VERSION = "0.3.0"

from homeassistant.const import Platform

# Integration domain
DOMAIN = "secure_me"

# Version and device info
VERSION = "0.3.0"
MANUFACTURER = "KingPainter"
MODEL = "Secure Me Alarm System"

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

# Events
EVENT_ALARM_ARMED = f"{DOMAIN}_armed"
EVENT_ALARM_DISARMED = f"{DOMAIN}_disarmed"
EVENT_ALARM_TRIGGERED = f"{DOMAIN}_triggered"
EVENT_ALARM_TEST_STARTED = f"{DOMAIN}_test_started"
EVENT_ALARM_TEST_COMPLETED = f"{DOMAIN}_test_completed"
EVENT_MODULE_ENABLED = f"{DOMAIN}_module_enabled"
EVENT_MODULE_DISABLED = f"{DOMAIN}_module_disabled"
EVENT_MODULE_ERROR = f"{DOMAIN}_module_error"

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
ATTR_CHANGED_BY = "changed_by"
ATTR_CODE_ARM_REQUIRED = "code_arm_required"
ATTR_MODULE_ENABLED = "module_enabled"
ATTR_MODULE_STATE = "module_state"
ATTR_MODULE_STATUS = "module_status"
ATTR_MODULE_CONFIG = "module_config"

# Update intervals
SCAN_INTERVAL = 30  # seconds
STATE_MACHINE_UPDATE_INTERVAL = 1  # Update every second for countdown

# Coordinator
COORDINATOR = "coordinator"
UNDO_UPDATE_LISTENER = "undo_update_listener"
MODULES = "modules"

# Zone types
ZONE_TYPE_ENTRY = "entry"
ZONE_TYPE_INSTANT = "instant"
ZONE_TYPE_INTERIOR = "interior"
ZONE_TYPE_PERIMETER = "perimeter"

# Zone attributes
ATTR_ZONE_TYPE = "zone_type"
ATTR_ZONE_ENABLED = "zone_enabled"
ATTR_ZONE_SENSORS = "zone_sensors"
ATTR_ZONE_OPEN_SENSORS = "zone_open_sensors"

# Module types
MODULE_CAMERA = "camera"
MODULE_LOCK = "lock"
MODULE_LIGHTS = "lights"
MODULE_CLIMATE = "climate"
MODULE_SIREN = "siren"
MODULE_TTS = "tts"

# Module status
STATUS_DISABLED = "disabled"
STATUS_IDLE = "idle"
STATUS_ACTIVE = "active"
STATUS_ERROR = "error"

# Camera module
CAMERA_MODE_OFF = "off"
CAMERA_MODE_LIVE = "live"
CAMERA_MODE_RECORD_24 = "record_24"
CAMERA_MODE_RECORD_MOTION = "record_motion"

# Light modes
LIGHT_MODE_NORMAL = "normal"
LIGHT_MODE_ALARM = "alarm"
LIGHT_MODE_BLINKING = "blinking"

# TTS languages
TTS_LANG_DA = "da"  # Danish
TTS_LANG_EN = "en"  # English
