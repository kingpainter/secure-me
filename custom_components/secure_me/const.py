"""Constants for Secure Me integration."""
# VERSION = "1.5.0"

from homeassistant.const import Platform

# Integration domain
DOMAIN = "secure_me"

# Version and device info
VERSION = "1.5.0"
MANUFACTURER = "KingPainter"
MODEL = "Secure Me Alarm System"

# -- Error handling ----------------------------------------------------------
DEFAULT_RETRY_MAX = 3
DEFAULT_RETRY_DELAY = 2.0
DEFAULT_RETRY_BACKOFF = 2.0

# Notification IDs (persistent_notification)
NOTIFY_ID_MODULE_ERROR = "secure_me_module_error"
NOTIFY_ID_RECOVERY = "secure_me_recovery"
NOTIFY_ID_FAKE_PRESENCE = "secure_me_fake_presence"
NOTIFY_ID_AUTO_ACTIONS = "secure_me_auto_actions"

# -- Fake Presence (v1 legacy + v2 config keys) ------------------------------
CONF_FAKE_PRESENCE = "fake_presence"
CONF_HOME_ALONE_CAMERAS = "home_alone_cameras"

FAKE_PRESENCE_ON_EN = "Secure Me: Fake Presence activated. Automatic arming is blocked."
FAKE_PRESENCE_OFF_EN = "Secure Me: Fake Presence deactivated. Automatic arming resumed."
FAKE_PRESENCE_ON_DA = "Secure Me: Fake Presence aktiveret. Automatisk aktivering er blokeret."
FAKE_PRESENCE_OFF_DA = "Secure Me: Fake Presence deaktiveret. Automatisk aktivering genoptaget."

EVENT_FAKE_PRESENCE_CHANGED = f"{DOMAIN}_fake_presence_changed"
EVENT_PRESENCE_CHANGED = f"{DOMAIN}_presence_changed"

# Fake Presence v2 config field names (stored under 'fake_presence' store key)
FP_ACTIVE        = "active"
FP_BLOCK_ALARM   = "block_alarm"
FP_BLOCK_LOCKS   = "block_locks"
FP_BLOCK_CAMERAS = "block_cameras"

# -- Error messages - English ------------------------------------------------
ERROR_MODULE_FAILED_EN = "Secure Me: Module '{module}' failed during '{action}'. Check logs."
ERROR_ENTITY_UNAVAILABLE_EN = "Secure Me: Entity '{entity}' is unavailable. Check device connection."
ERROR_RETRY_EXHAUSTED_EN = "Secure Me: Module '{module}' failed after {retries} retries for '{action}'."
ERROR_RECOVERY_OK_EN = "Secure Me: Module '{module}' recovered successfully after retry."

# -- Error messages - Danish -------------------------------------------------
ERROR_MODULE_FAILED_DA = "Secure Me: Modul '{module}' fejlede under '{action}'. Tjek loggen."
ERROR_ENTITY_UNAVAILABLE_DA = "Secure Me: Enhed '{entity}' er ikke tilgaengelig. Tjek enhedens forbindelse."
ERROR_RETRY_EXHAUSTED_DA = "Secure Me: Modul '{module}' fejlede efter {retries} forsoeg paa '{action}'."
ERROR_RECOVERY_OK_DA = "Secure Me: Modul '{module}' gendannet korrekt efter nyt forsoeg."

# Platforms
PLATFORMS = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]

# Panel / sidebar configuration
CONF_SIDEBAR_TITLE = "sidebar_title"
CONF_SIDEBAR_ICON  = "sidebar_icon"
CONF_PANEL_ENABLED = "panel_enabled"
CONF_REQUIRE_ADMIN = "require_admin"

DEFAULT_SIDEBAR_TITLE = "Secure Me"
DEFAULT_SIDEBAR_ICON  = "mdi:shield-lock"
DEFAULT_PANEL_ENABLED = True
DEFAULT_REQUIRE_ADMIN = False

# Configuration
CONF_CODE = "code"
CONF_EXIT_DELAY = "exit_delay"
CONF_ENTRY_DELAY = "entry_delay"
CONF_TRIGGER_TIME = "trigger_time"

# Defaults
DEFAULT_NAME = "Secure Me"
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
STATE_ALARM_ARMED_HOME_ALONE = "armed_home_alone"
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

# v1.4.3 rich error events
EVENT_ALARM_ARM_FAILED       = f"{DOMAIN}_arm_failed"
EVENT_ALARM_INVALID_CODE     = f"{DOMAIN}_invalid_code"
EVENT_ALARM_COMMAND_REJECTED = f"{DOMAIN}_command_rejected"

EVENT_READY_TO_ARM_MODES_CHANGED = f"{DOMAIN}_ready_to_arm_modes_changed"

# Mobile push notification action events
PUSH_EVENT = "mobile_app_notification_action"

EVENT_ACTION_FORCE_ARM      = "SECURE_ME_FORCE_ARM"
EVENT_ACTION_RETRY_ARM      = "SECURE_ME_RETRY_ARM"
EVENT_ACTION_DISARM         = "SECURE_ME_DISARM"
EVENT_ACTION_ARM_AWAY       = "SECURE_ME_ARM_AWAY"
EVENT_ACTION_ARM_HOME       = "SECURE_ME_ARM_HOME"
EVENT_ACTION_ARM_NIGHT      = "SECURE_ME_ARM_NIGHT"
EVENT_ACTION_ARM_VACATION   = "SECURE_ME_ARM_VACATION"
EVENT_ACTION_ARM_HOME_ALONE = "SECURE_ME_ARM_HOME_ALONE"

PUSH_EVENT_ACTIONS = [
    EVENT_ACTION_FORCE_ARM,
    EVENT_ACTION_RETRY_ARM,
    EVENT_ACTION_DISARM,
    EVENT_ACTION_ARM_AWAY,
    EVENT_ACTION_ARM_HOME,
    EVENT_ACTION_ARM_NIGHT,
    EVENT_ACTION_ARM_VACATION,
    EVENT_ACTION_ARM_HOME_ALONE,
]

# Services
SERVICE_ARM_AWAY       = "arm_away"
SERVICE_ARM_HOME       = "arm_home"
SERVICE_ARM_NIGHT      = "arm_night"
SERVICE_ARM_VACATION   = "arm_vacation"
SERVICE_ARM_HOME_ALONE = "arm_home_alone"
SERVICE_DISARM         = "disarm"
SERVICE_TRIGGER        = "trigger"
SERVICE_RUN_TEST       = "run_test"

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

ATTR_BYPASSED_SENSORS = "bypassed_sensors"
ATTR_LAST_TRIGGERED   = "last_triggered"

# Update intervals
SCAN_INTERVAL = 30
STATE_MACHINE_UPDATE_INTERVAL = 1

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
TTS_LANG_DA = "da"
TTS_LANG_EN = "en"

# Storage versioning
STORAGE_VERSION_MAJOR = 2
STORAGE_VERSION_MINOR = 1

# Sensor group constants
ATTR_SENSOR_GROUP_ID = "group_id"
ATTR_SENSOR_GROUP_NAME = "name"
ATTR_SENSOR_GROUP_ENTITIES = "entities"
ATTR_SENSOR_GROUP_TIMEOUT = "timeout"
ATTR_SENSOR_GROUP_EVENT_COUNT = "event_count"

# Per-sensor config fields
ATTR_SENSOR_ENTRY_DELAY = "entry_delay"
ATTR_SENSOR_AUTO_BYPASS = "auto_bypass"
ATTR_SENSOR_AUTO_BYPASS_MODES = "auto_bypass_modes"
ATTR_SENSOR_ARM_ON_CLOSE = "arm_on_close"
ATTR_SENSOR_ALLOW_OPEN   = "allow_open"    # permanent bypass — sensor ignoreres ved al arming

# Home Alone mode constants
CONF_HOME_ALONE_CAMERA   = "home_alone_camera"
CONF_HOME_ALONE_SPEAKER  = "home_alone_tts_speaker"
CONF_HOME_ALONE_ACTION_1 = "home_alone_action_1"
CONF_HOME_ALONE_ACTION_2 = "home_alone_action_2"

HOME_ALONE_DEFAULT_ACTION_1 = "Where are you going?"
HOME_ALONE_DEFAULT_ACTION_2 = "Please close the door."

EVENT_HOME_ALONE_ACTION_1 = "SECURE_ME_HOME_ALONE_ACTION_1"
EVENT_HOME_ALONE_ACTION_2 = "SECURE_ME_HOME_ALONE_ACTION_2"

# Floorplan (Home Alone live-view)
FLOORPLAN_DIR_NAME   = "floorplan"
FLOORPLAN_IMAGE_NAME = "floorplan.png"
FLOORPLAN_URL_PATH   = f"/api/{DOMAIN}-panel/floorplan/{FLOORPLAN_IMAGE_NAME}"
FLOORPLAN_MAX_BYTES  = 4 * 1024 * 1024

ATTR_FLOORPLAN_IMAGE_URL = "image_url"
ATTR_FLOORPLAN_WIDTH     = "width"
ATTR_FLOORPLAN_HEIGHT    = "height"
ATTR_FLOORPLAN_MARKERS   = "markers"

ATTR_MARKER_X_PCT = "x_pct"
ATTR_MARKER_Y_PCT = "y_pct"
ATTR_MARKER_LABEL = "label"
ATTR_MARKER_KIND  = "kind"

# Auto-arm (presence-based) - kept for backwards-compat with coordinator.py
AUTO_ARM_AWAY_DELAY   = 900
AUTO_ARM_PUSH_TITLE   = "Secure Me: Auto-armed"
AUTO_ARM_PUSH_MESSAGE = "All residents left home. Alarm, locks and cameras have been secured automatically."

# Auto Actions v2
# Presence-driven per-feature automatic actions with individual delays,
# arrival confirmation, and Fake Presence v2 selective blocking.

# HA events
EVENT_HOME_EMPTY       = f"{DOMAIN}_home_empty"
EVENT_PERSON_HOME      = f"{DOMAIN}_person_home"
EVENT_AUTO_ACTION_DONE = f"{DOMAIN}_auto_action_done"

# Store key
CONF_AUTO_ACTIONS = "auto_actions"

# Config field names
AA_LOCK_ENABLED   = "auto_lock_enabled"
AA_LOCK_DELAY     = "auto_lock_delay"
AA_ALARM_ENABLED  = "auto_alarm_enabled"
AA_ALARM_DELAY    = "auto_alarm_delay"
AA_CAMERA_ENABLED = "auto_camera_enabled"
AA_CAMERA_DELAY   = "auto_camera_delay"
AA_ARRIVAL_DELAY  = "arrival_confirmation_delay"
AA_NOTIFY_ALL     = "notify_all_users"

# Defaults (seconds)
DEFAULT_AA_LOCK_DELAY    = 120
DEFAULT_AA_ALARM_DELAY   = 300
DEFAULT_AA_CAMERA_DELAY  = 0
DEFAULT_AA_ARRIVAL_DELAY = 60