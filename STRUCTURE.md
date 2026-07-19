# Secure Me - Project Structure

Complete technical documentation of the Secure Me integration architecture and file organization.

**Version:** 1.4.2
**Last Updated:** 2026-04-26

---

## Directory Structure

```
secure-me/                              # GitHub repo root
|
+-- custom_components/secure_me/        # Integration root
|   |
|   +-- __init__.py                     # Integration entry point, store + coordinator setup
|   +-- manifest.json                   # Integration metadata (v1.4.2, bcrypt>=4.0.0)
|   +-- const.py                        # Constants, retry config, error messages, push events
|   +-- config_flow.py                  # GUI configuration wizard
|   +-- panel.py                        # Sidebar panel + Lovelace alarm-card registration
|   +-- icons.json                      # Icon mappings for HA UI
|   +-- services.yaml                   # Service definitions (arm_*, disarm, run_test, etc.)
|   +-- strings.json                    # English source strings for translations
|   |
|   +-- coordinator.py                  # DataUpdateCoordinator + PresenceMonitor (auto-arm)
|   +-- state_machine.py                # Alarm state logic, async lock, auto-reset, RestoreEntity support
|   +-- zones.py                        # Zone manager, sensor groups, debouncing, per-sensor config
|   +-- store.py                        # MigratableStore v2, bcrypt PIN hashing, schema migration
|   +-- module_manager.py               # Legacy module lifecycle helper (most logic in coordinator)
|   +-- websocket_api.py                # 51 WebSocket endpoints
|   +-- system_health.py                # HA system health integration
|   +-- diagnostics.py                  # Enhanced diagnostics with redaction
|   +-- notification_dispatcher.py      # User-routed notifications, smoke/water always-on, TTS quiet hours
|   |
|   +-- alarm_control_panel.py          # Main alarm entity (RestoreEntity, code_format=NUMBER)
|   +-- binary_sensor.py                # Health binary sensors (system + 6 modules + battery + presence)
|   +-- sensor.py                       # Battery sensors (auto-discovery, cached)
|   +-- switch.py                       # Switch entities
|   +-- select.py                       # Select entities
|   |
|   +-- modules/
|   |   +-- __init__.py                 # Module exports
|   |   +-- base.py                     # AlarmModule abstract base + retry/degraded logic
|   |   +-- camera.py                   # Camera: POE smart-delay, recording mode
|   |   +-- lock.py                     # Lock: lock-on-arm, retry-protected
|   |   +-- lights.py                   # Lights: emergency flash + steady-white split
|   |   +-- climate.py                  # Climate: away preset / temperature
|   |   +-- siren.py                    # Siren: native siren entities + switch/input_boolean fallback
|   |   +-- tts.py                      # TTS: speaker profiles, parallel playback, per-speaker queue
|   |
|   +-- frontend/
|   |   +-- secure-me-panel.js          # ~5100 lines, EMOJI-FREE - sidebar configuration panel
|   |   +-- secure-me-alarm-card.js     # Lovelace alarm control card
|   |
|   +-- translations/
|   |   +-- en.json                     # English
|   |   +-- da.json                     # Danish
|   |
|   +-- tools/
|       +-- validate_version.py         # Version consistency checker (all .py + manifest + JS + services.yaml)
|       +-- validate_encoding.py        # UTF-8 / emoji corruption detector
|       +-- clean_encoding.py           # Encoding cleanup helper
|       +-- PREVENTION_GUIDE.md         # Internal guide: avoiding emoji corruption
|
+-- tests/                              # Pytest unit tests (291 tests across 12 files)
|   +-- __init__.py
|   +-- conftest.py                     # MockHass, MockConfigEntry, MockModule fixtures
|   +-- test_const.py                   # Constants and version sync tests (12 tests)
|   +-- test_diagnostics.py             # Diagnostics redaction (5 tests)
|   +-- test_files.py                   # manifest.json, services.yaml, strings.json (13 tests)
|   +-- test_init_.py                   # Integration setup/unload (8 tests)
|   +-- test_modules.py                 # Module health, lock functional, severity (43 tests)
|   +-- test_sensors.py                 # Battery discovery, summary (16 tests)
|   +-- test_state_machine.py           # State machine baseline (21 tests)
|   +-- test_state_machine_v2.py        # Auto-reset, race condition, real SM async (35 tests)
|   +-- test_store.py                   # Store CRUD, fake presence (25 tests)
|   +-- test_v1_2_0.py                  # bcrypt, sensor groups, push actions, speaker profiles (56 tests)
|   +-- test_zones_edge_cases.py        # Sensor edge cases, debounce (28 tests)
|   +-- test_base_module.py             # Retry, degraded state, recovery (29 tests)
|
+-- .github/workflows/
|   +-- validate.yaml                   # HACS + Hassfest + version consistency
|   +-- pytest.yaml                     # Pytest 3.11 + 3.12
|
+-- brands/secure_me/                   # 8 branding images (HACS requirement)
|   +-- icon.png / icon@2x.png
|   +-- logo.png / logo@2x.png
|   +-- dark variants
|
+-- docs/                               # Additional documentation assets
|
+-- hacs.json                           # HACS metadata
+-- README.md                           # Public README with feature overview
+-- CHANGELOG.md                        # Version history
+-- INSTALLATION.md                     # Clean install + first-config guide
+-- info.md                             # HACS store page
+-- FEATURES.md                         # Detailed feature documentation
+-- STATUS.md                           # Current development status
+-- STRUCTURE.md                        # This file - architecture documentation
+-- LICENSE                             # MIT
+-- pytest.ini                          # Pytest configuration
+-- requirements.txt                    # Python dependencies (bcrypt, etc.)
+-- .gitattributes                      # Git LF line endings + UTF-8 enforcement
+-- .gitignore
```

---

## File Sizes (verified 2026-04-26)

| File | Lines | Notes |
|------|-------|-------|
| frontend/secure-me-panel.js | 5136 | EMOJI-FREE, vanilla Custom Element |
| websocket_api.py | 2106 | 51 endpoints |
| coordinator.py | 1401 | Includes PresenceMonitor class |
| zones.py | 585 | ZoneManager + Zone + SensorGroup |
| store.py | 540 | MigratableStore + bcrypt + ThreadPoolExecutor |
| state_machine.py | 389 | Async lock, RestoreEntity support |
| base.py | 263 | Retry + degraded state base class |
| tests/ (combined) | ~3500 | 291 test cases |

---

## Architecture Overview

```
+-------------------------------------------------------------+
|                     Home Assistant Core                      |
+------------------------+------------------------------------+
                         |
                         v
+-------------------------------------------------------------+
|                   Secure Me Integration                      |
|                                                              |
|  +-------------------------------------------------------+  |
|  |            Integration Entry (__init__.py)            |  |
|  |  - Setup & initialization per config entry            |  |
|  |  - Global store (one instance, shared)                |  |
|  |  - Device registration                                |  |
|  |  - Panel + Lovelace card registration (once)          |  |
|  |  - WebSocket API registration (once)                  |  |
|  +-------------------------+-----------------------------+  |
|                            |                                 |
|                            v                                 |
|  +-------------------------------------------------------+  |
|  |          Coordinator (coordinator.py)                 |  |
|  |  - DataUpdateCoordinator (1s tick during countdown)   |  |
|  |  - State machine integration                          |  |
|  |  - Module orchestration with graceful degradation     |  |
|  |  - Push notification action handler                   |  |
|  |  - PresenceMonitor (presence-based auto-arm)          |  |
|  |  - Health event throttling (max 1x/5s)                |  |
|  |  - Scheduled test runner (1-min cron)                 |  |
|  |  - Code validation via bcrypt                         |  |
|  +------+----------------+---------------+---------------+  |
|         |                |               |                   |
|   +-----+-----+   +------+----+   +------+-----+           |
|   |   State   |   |   Zone    |   |   6 Smart  |           |
|   |  Machine  |   |  Manager  |   |   Modules  |           |
|   |           |   |           |   |            |           |
|   | RestoreEnt|   | Sensor    |   | Camera     |           |
|   | Async lock|   | groups    |   | Lock       |           |
|   | Auto-reset|   | Per-sensor|   | Lights     |           |
|   |           |   | config    |   | Climate    |           |
|   |           |   | Debounce  |   | Siren      |           |
|   |           |   |           |   | TTS        |           |
|   +-----------+   +-----------+   +------------+           |
|                                                              |
|  +-------------------------------------------------------+  |
|  |         Alarm Control Panel Entity                    |  |
|  |  - 7 states: disarmed, arming, armed_*, pending,     |  |
|  |              triggered                                |  |
|  |  - 5 arm modes: away, home, night, vacation,         |  |
|  |                 home_alone                            |  |
|  |  - code_format=NUMBER (HA standard dialog shows PIN)  |  |
|  |  - RestoreEntity (state persists across HA restart)   |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  |  Notification Dispatcher                              |  |
|  |  - Smoke/water_leak: ALWAYS-ON critical broadcast    |  |
|  |  - Triggered/pending:  broadcast to receive_critical |  |
|  |  - Armed/disarmed:     ROUTED to acting user only    |  |
|  |  - Low battery:        broadcast to receive_alerts   |  |
|  |  - TTS respects per-user quiet hours                  |  |
|  |  - Home Alone door triggers: snapshot + push actions  |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  |  Health & Battery Monitoring                          |  |
|  |  - System Health binary sensor (overall problem)     |  |
|  |  - Per-module health binary sensors (6 modules)      |  |
|  |  - Battery alert binary sensor (critical level)      |  |
|  |  - Presence binary sensor (anyone home)              |  |
|  |  - Battery auto-discovery sensors                     |  |
|  |  - System Health integration (HA built-in)           |  |
|  |  - Enhanced diagnostics download                      |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  |  Frontend                                             |  |
|  |  Sidebar panel (secure-me-panel.js, 5136 lines)      |  |
|  |    - 8 tabs: Sensors, Zones, Users, Modules,         |  |
|  |              Actions, Test, Future, Settings          |  |
|  |    - Toast notifications, in-panel confirm dialogs    |  |
|  |    - Live countdown pill in sidebar                   |  |
|  |    - WebSocket subscription (state + health events)   |  |
|  |  Lovelace alarm card (secure-me-alarm-card.js)        |  |
|  |    - 4-digit PIN entry, OK confirmation required      |  |
|  |    - Live exit/entry countdown                        |  |
|  |    - Home Alone quick-message buttons (dynamic)       |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  |  Persistent Storage (store.py - MigratableStore v2)   |  |
|  |  - bcrypt-hashed user PINs (10 rounds)                |  |
|  |  - Zones, sensors, sensor_groups, users               |  |
|  |  - Module configs                                     |  |
|  |  - Notifications, automations                         |  |
|  |  - Speaker profiles (v1.4.0)                          |  |
|  |  - Scheduled tests                                    |  |
|  |  - Test history (last 10 results)                     |  |
|  |  - Fake Presence flag, home_alone_cameras             |  |
|  |  - Schema migration v1 -> v2 (auto on load)           |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
```

---

## Core Components

### __init__.py - Integration Entry

**Purpose:** Lifecycle management - setup, unload, options reload.

**Key Functions:**
```python
async def async_setup_entry(hass, entry):
    # 1. Initialize global store (shared across config entries)
    # 2. Create coordinator for this entry
    # 3. Load module/zone/sensor config from store into coordinator
    # 4. Register WebSocket API (once globally)
    # 5. Register frontend panel + Lovelace card (once globally)
    # 6. Setup platforms (alarm_control_panel, binary_sensor,
    #    sensor, switch, select)
    # 7. Register device

async def async_unload_entry(hass, entry):
    # 1. Shutdown coordinator (cancels scheduled timers, presence monitor,
    #    push handler, modules)
    # 2. Unload platforms
    # 3. Remove update listener
    # 4. Unregister panel if last entry
```

**Data Structure:**
```python
hass.data[DOMAIN] = {
    "store": <SecureMeStore>,           # Global, shared
    "_websocket_registered": True,      # Global flag
    "_panel_registered": True,          # Global flag
    "_static_registered": True,         # aiohttp routes (one-shot)
    "<entry_id>": {                     # Per-entry
        COORDINATOR: <coordinator>,
        UNDO_UPDATE_LISTENER: <listener>,
    }
}
```

---

### coordinator.py - State Coordinator

**Purpose:** Central state, module orchestration, presence monitor, push handler.

**Class:** `SecureMeCoordinator(DataUpdateCoordinator)`

**Embedded class:** `PresenceMonitor` - presence-based auto-arm

**Key responsibilities:**
- `state_machine` integration with state-change + countdown callbacks
- `zone_manager` integration with trigger callbacks (`_zone_triggered`,
  `_arm_on_close_triggered`)
- 6 modules registered and orchestrated via `_execute_modules_arm_*` /
  `_execute_modules_disarm` / `_execute_modules_trigger`
- Per-module exception isolation: one failure does not block others
- `_handle_push_event` listens on `mobile_app_notification_action` for
  arm/disarm/force_arm via push notification action buttons
- `validate_code()` uses bcrypt via store.authenticate_user()
- `identify_user()` and `identify_user_id()` resolve PIN -> user
- `async_restore_state()` re-applies persisted state silently after restart
- `_check_scheduled_tests` runs every minute, fires due tests
- `PresenceMonitor` watches person entities, starts 15-min auto-arm
  countdown when all residents leave, respects Fake Presence

**Performance optimizations:**
- `_countdown_updated()` writes countdown in-place + calls
  `async_update_listeners()` instead of full refresh every second
- Health events throttled to max 1x per 5 seconds via `time.monotonic()`
- Full refresh only at countdown=0 or every 5 seconds

**Public methods:**
```python
async def async_arm_away(code, skip_delay, auto, force) -> bool
async def async_arm_home(code, skip_delay, force) -> bool
async def async_arm_night(code, skip_delay, force) -> bool
async def async_arm_vacation(code, skip_delay, force) -> bool
async def async_arm_home_alone(code, skip_delay, force) -> bool
async def async_disarm(code) -> bool
async def async_trigger(source) -> bool
async def async_set_fake_presence(active)
async def async_load_store_config(store)
async def async_restore_state(state, armed_by)
def get_health_score() -> int
def get_module_health() -> dict
def get_presence_status() -> dict
```

---

### state_machine.py - State Logic

**Purpose:** Alarm state transitions, delays, race-safe async behavior.

**Class:** `AlarmStateMachine`

**States (7):**
```
disarmed -> arming -> armed_away / armed_home / armed_night /
                      armed_vacation / armed_home_alone
armed_* -> pending -> triggered
triggered -> disarmed (manual or auto-reset after trigger_time)
```

**Race-condition protection:**
- `asyncio.Lock()` on every arm/disarm method
- `_cancel_countdown()` is async and awaits task completion before
  returning (prevents zombie tasks during rapid arm/disarm cycles)
- Double-arm guard: returns False if already armed
- Arming-state guard: zone triggers ignored while in `arming` state

**Auto-reset:**
- `_trigger_reset_timer()` runs after `trigger_time` seconds in triggered
  state, returns alarm to disarmed
- Configurable per integration entry (default 300s)

**RestoreEntity support:**
- `restore_state(state)` sets `_current_state` directly without firing
  callbacks or starting timers
- Only stable states are restorable: disarmed, armed_*
- Transient states (arming, pending, triggered) reset to disarmed
  with warning - countdown context is lost across restarts

**Key methods:**
```python
async def arm_away(skip_delay) -> bool
async def arm_home(skip_delay) -> bool
async def arm_night(skip_delay) -> bool
async def arm_vacation(skip_delay) -> bool
async def arm_home_alone(skip_delay) -> bool
async def disarm() -> bool
async def trigger_alarm(source) -> bool
async def trigger_entry_delay(zone_type) -> bool
async def cancel_pending() -> bool
def restore_state(state) -> None
def cleanup() -> None
```

---

### zones.py - Zone Manager

**Purpose:** Multi-zone management, sensor groups (anti-masking),
per-sensor configuration, debouncing.

**Classes:**
- `Zone` - individual zone with sensors and trigger state
- `SensorGroup` - anti-masking group: N sensors must activate within
  timeout window
- `ZoneManager` - top-level zone management

**Edge case handling:**
- `new_state=None` (entity deleted from HA): treated as closed,
  `WARNING + persistent_notification` sent
- `unavailable`/`unknown` state: treated as closed, **DEBUG-level only**
  (v1.4.2 fix - was WARNING + persistent_notification, caused log spam
  from flapping Zigbee/WiFi sensors)
- `check_for_open_sensors()`: skips unavailable/missing sensors
  (arming not blocked by offline sensors)
- Sensor opens during exit delay: ignored at coordinator level
  (user is still leaving)

**Per-sensor configuration:**
- `entry_delay` - override zone default (None = use zone default)
- `auto_bypass` - silently bypass open sensors at arm time
- `arm_on_close` - auto-arm in away mode when this sensor closes
- `home_alone_camera` - camera to snapshot when triggered in home_alone
- `home_alone_tts_speaker` - speaker for door announcement
- `home_alone_action_1`, `home_alone_action_2` - push action button text

**Sensor groups (anti-masking):**
- `event_count` sensors must activate within `timeout` seconds
- Prevents false alarms from single sensor glitches
- Designed against masking attacks (e.g. cover one sensor with foam)

**Debounce:**
- 500ms per-sensor cooldown on trigger callbacks
- Each sensor tracked independently in `_last_trigger_time`
- Flapping sensors fire callback only once per debounce window

**Key methods:**
```python
def add_zone(zone_id, zone_type, sensors, enabled, arm_modes)
def update_sensor_state(entity_id, state) -> tuple[bool, Zone | None]
def check_for_open_sensors(bypass_list) -> bool
def get_auto_bypass_sensors(sensors) -> list[str]
def get_sensor_entry_delay(entity_id, zone_default) -> int
def get_home_alone_sensor_config(entity_id) -> dict
def load_sensor_configs(configs)
def load_sensor_groups(groups)
def reset_sensor_groups()
def start_monitoring(arm_mode)
def stop_monitoring()
def clear_all_triggers()
```

---

### store.py - Persistent Storage

**Purpose:** Versioned schema storage with auto-migration and bcrypt PIN
hashing.

**Class:** `SecureMeStore` extends `_MigratableStore` extends HA's `Store`.

**Schema version:** `STORAGE_VERSION_MAJOR = 2`, `STORAGE_VERSION_MINOR = 0`.

**Migration from v1 -> v2:**
- `sensor_groups` key added (empty dict)
- Per-sensor fields backfilled with defaults: `entry_delay=None`,
  `auto_bypass=False`, `arm_on_close=False`
- Plaintext user codes flagged for re-hashing on next save
  (`code_hashed=False`)

**bcrypt PIN hashing:**
- 10 rounds, base64-encoded for storage
- `_hash_code(plaintext)` -> hash string
- `_check_code(plaintext, hash)` -> bool
- `authenticate_user(code)` uses `ThreadPoolExecutor` with max 4 workers
  for non-blocking parallel code checks across all enabled users

**Stored data:**
```json
{
    "version": 2,
    "key": "secure_me.panel_config",
    "data": {
        "sensors": { ... },                    // per-sensor config
        "sensor_groups": { ... },              // anti-masking groups
        "zones": { ... },                      // zone definitions + arm_modes
        "users": { ... },                      // bcrypt-hashed PINs
        "modules": { ... },                    // 6 module configs
        "notifications": { ... },              // user-routed notifications
        "automations": { ... },                // trigger-based automations
        "scheduled_tests": { ... },            // cron-style test schedule
        "speaker_profiles": [ ... ],           // TTS speaker definitions
        "fake_presence": false,
        "home_alone_cameras": []
    }
}
```

**Key methods:**
```python
# bcrypt
@staticmethod _hash_code(plaintext) -> str
@staticmethod _check_code(plaintext, hash) -> bool
def authenticate_user(code, user_id=None) -> dict | None

# CRUD
def get_zones() / async_save_zone() / async_delete_zone()
def get_users() / async_save_user() / async_delete_user()
def get_modules() / async_save_module()
def get_notifications() / async_save_notification() / async_delete_notification()
def get_automations() / async_save_automation() / async_delete_automation()
def get_sensors() / async_save_sensor() / async_save_sensors_bulk()
def get_sensor_groups() / async_save_sensor_group() / async_delete_sensor_group()
def get_scheduled_tests() / async_save_scheduled_test() /
    async_delete_scheduled_test()
def get_speaker_profiles() / async_save_speaker_profiles()
def get_fake_presence() / async_set_fake_presence()
def get_home_alone_cameras() / async_save_home_alone_cameras()
```

---

### modules/base.py - AlarmModule Base Class

**Purpose:** Abstract base with centralized retry and degraded state.

**Class:** `AlarmModule(ABC)`

**Retry logic:**
- `async_call_service_with_retry()`: 3 retries, 2s -> 4s -> 8s exponential
  backoff
- `async_call_service()`: single attempt (for test calls and state reads)
- Configurable per-module: `retry_max`, `retry_delay`, `retry_backoff`

**Graceful degradation:**
- `_degraded` boolean tracked per module
- `_consecutive_errors` counter
- `_on_failure(action)`: set degraded, fire `persistent_notification`
- `_on_success(action)`: clear degraded, fire recovery notification if
  previously degraded

**Per-module retry coverage:**

| Module | Retry-protected calls |
|--------|----------------------|
| Camera | 4 (POE on/off, recording on/off) |
| Lock | 3 (lock on arm, unlock on disarm, test) |
| Lights | 3 (off on arm, off/restore on disarm, on trigger) |
| Climate | 5 (away preset/temp, restore preset/temp, eco) |
| Siren | 3 (turn on/off, gateway light off) |
| TTS | 0 (single-attempt to avoid duplicate playback) |

**Total retry-protected calls: 18 across 5 modules.** TTS uses
`async_call_service` (single attempt) because retries cause double
playback.

**Interface:**
```python
class AlarmModule(ABC):
    @property def enabled(self) -> bool
    @property def degraded(self) -> bool
    @property def module_name(self) -> str

    @abstractmethod async def async_arm(mode) -> bool
    @abstractmethod async def async_disarm() -> bool
    @abstractmethod async def async_trigger() -> bool
    @abstractmethod async def async_test() -> dict

    # Provided by base
    async def async_call_service_with_retry(...) -> bool   # 3 retries
    async def async_call_service(...) -> bool              # single attempt
    def backup_state(entity_id)
    def get_backup_state(entity_id) -> dict | None
    def is_entity_available(entity_id) -> bool
    def get_entity_state(entity_id) -> str | None
    def enable() / disable()
```

---

### notification_dispatcher.py - User-Routed Notifications

**Purpose:** Route notifications to the right users via the right channels.

**Class:** `NotificationDispatcher`

**Routing rules:**

| Trigger | Recipients |
|---------|------------|
| `armed` / `disarmed` | Acting user only (by user_id, if `receive_own_actions`) |
| `arming` | Acting user only |
| `pending` | Broadcast to all users with `receive_critical=True` |
| `triggered` | Broadcast to all users with `receive_critical=True` |
| `smoke` | **ALWAYS-ON** broadcast critical to `receive_critical` users |
| `water_leak` | **ALWAYS-ON** broadcast critical to `receive_critical` users |
| `low_battery` | Broadcast to all users with `receive_alerts=True` |
| `home_alone_action` | Per-user via Home Alone door dispatch |
| `auto_arm` | Broadcast to all users with `notify_service` configured |

**Channels:**
- `push` - via per-user `notify_service`
- `tts` - via TTS module's `announce_system()` with optional speaker
  targeting

**Critical push payload bypasses iOS Do Not Disturb / Android silent mode.**

**Per-user notification settings:**
- `notify_service` (e.g. `notify.mobile_app_flemming`)
- `receive_critical` - triggered/smoke/water/pending
- `receive_alerts` - low_battery, arm_fail
- `receive_own_actions` - own arm/disarm confirmations
- `tts_quiet_start` / `tts_quiet_end` - hour 0-23

**Smoke/moisture sensors auto-discovered at startup**, monitored via
`state_changed` event. New sensors registered live as they appear in HA.

**Home Alone door dispatch:**
`dispatch_home_alone_door_trigger()` sends push with camera snapshot
attachment + 2 configurable action buttons + optional TTS announcement
on configured speaker.

---

### modules/tts.py - TTS Speaker Engine

**Purpose:** Multi-speaker TTS with speaker profiles, parallel playback,
per-speaker queuing.

**Speaker profiles:**
Each profile defines: `entity_id`, `name`, `volume`, `tts_service`,
`tts_entity`. Profiles are the single source of truth - all TTS output
references profiles.

**SpeakerQueue class:**
Per-speaker `asyncio.Queue` ensures messages play sequentially on the
same speaker (never overlapping). Messages on different speakers play in
parallel via `asyncio.gather()`.

**Service support:**
- `tts.*` (cloud_say, google_translate_say, google_say, piper, voice_rss)
  - auto-maps short language codes to BCP-47 (`da` -> `da-DK`)
- `notify.*` (e.g. House Voice scripts)
- Unknown service types warn once then skip silently

**Custom messages:**
Per-trigger custom messages (armed_away, disarmed, triggered, etc.) with
optional speaker targeting (None = all speakers).

**Home Alone quick messages:**
Notifications with trigger `home_alone_action` appear as buttons in the
alarm Lovelace card. Buttons are loaded dynamically via
`get_home_alone_messages` WebSocket endpoint.

---

## Frontend Architecture

### secure-me-panel.js (5136 lines)

**Single-file Custom Element, EMOJI-FREE, vanilla JS.**

**Render strategy:**
- `_render()` - immediate, for user actions (tab switch, dialog open)
- `_queueRender()` - 50ms debounce, for data loads and background updates

**UX system:**
- `_toast(msg, type)` - styled in-panel toasts (success/error/warning/info),
  4s auto-dismiss
- `_confirm(msg, title)` - async Promise overlay, replaces browser confirm()
- `_cancelDialog()` - closes dialog without confirm
- Module health badges on Modules tab (OK/Warning/Error/Degraded)
- Triggered state pulses red, pending pulses yellow

**Dialog architecture:**
- `shell-dialog-mount` is the single mount point for all dialogs
- `data-currentDialog` tracks which dialog is open
- `_attachDialogListeners()` called once per dialog build (no listener
  accumulation)
- `_rebuildDialog()` used when dialog content changes (e.g. adding a
  TTS message)
- Each `_open*Config()` resets `currentDialog` to ensure fresh listeners

**WebSocket integration:**
- `subscribeEvents()` is awaited (returns Promise, not function)
- `_healthUpdateUnsubscribe` uses `typeof === 'function'` guard
- Health subscription registered once in `_loadData` (was previously in
  `set hass`, fired 169x at startup)

**Tabs:**
1. Sensors - sensor management, environmental always-on, hide/exclude,
   Fake Presence toggle
2. Zones - zone configuration with arm_modes
3. Users - PIN, NFC, person tracker binding, notification settings
4. Modules - 6 modules with config + live health badges
5. Actions - notifications + automations split
6. Test - test runner, scheduled tests, severity-aware overall result
7. Future - Home Alone Monitor camera config
8. Settings - system configuration

**Mobile:**
- Bottom navigation bar at <=768px
- 5 primary tabs visible + More drawer for remaining
- iOS safe-area inset support

### secure-me-alarm-card.js

**Lovelace alarm control card (Mushroom-style).**

- 4-digit PIN entry, OK confirmation required (no auto-submit)
- 5 arm modes (away, home, night, vacation, home_alone)
- Live exit/entry countdown via `_manageCdTicker()` (1s setInterval)
- v1.5.0: away/home/night/vacation/disarm route through HA's standard
  `alarm_control_panel.*` services (vacation moved off websocket once
  `ARM_VACATION` became a first-class HA feature). Only `arm_home_alone`
  still goes through Secure Me's websocket API (`secure_me/arm_home_alone`),
  since HA has no standard command for it -- see `API.md` for the full
  arm/disarm contract.
- Home Alone quick-message buttons loaded dynamically from
  `secure_me/get_home_alone_messages`
- v1.5.0: floorplan live-view (room glow, opening fade, sensor pin markers)
  rendered in Home Alone mode, mirroring the panel's own live preview

---

## WebSocket API (51 endpoints)

### Configuration
```
secure_me/get_sensors            secure_me/save_sensors
secure_me/get_zones              secure_me/save_zone
secure_me/delete_zone            secure_me/get_users
secure_me/save_user              secure_me/delete_user
secure_me/get_nfc_tags           secure_me/get_persons
secure_me/hide_sensor            secure_me/unmark_environmental
secure_me/get_modules            secure_me/save_module
secure_me/get_module_entities
secure_me/get_sensor_groups      secure_me/save_sensor_group
secure_me/delete_sensor_group
secure_me/get_speaker_profiles   secure_me/save_speaker_profiles
secure_me/get_home_alone_cameras secure_me/save_home_alone_cameras
secure_me/get_home_alone_messages
```

### Notifications & Automations
```
secure_me/get_notifications      secure_me/save_notification
secure_me/delete_notification    secure_me/test_notification
secure_me/get_notify_services    secure_me/test_tts
secure_me/get_automations        secure_me/save_automation
secure_me/delete_automation      secure_me/test_automation
```

### Alarm Control
```
secure_me/get_alarm_state        secure_me/disarm
secure_me/arm_away               secure_me/arm_home
secure_me/arm_night              secure_me/arm_vacation
secure_me/arm_home_alone
```

### Testing & Health
```
secure_me/get_health_summary     secure_me/run_test
secure_me/quick_test_siren       secure_me/quick_test_lights
secure_me/get_scheduled_tests    secure_me/save_scheduled_test
secure_me/delete_scheduled_test  secure_me/run_scheduled_test_now
secure_me/get_test_results
```

### Presence
```
secure_me/get_fake_presence      secure_me/set_fake_presence
```

### Message format

```javascript
// Request
{ type: "secure_me/run_test", id: 123, level: "standard" }

// Response
{
    id: 123,
    type: "result",
    success: true,
    result: {
        overall: "pass",  // or warning, fail, critical
        timestamp: "2026-04-26T18:00:00",
        modules: { ... },
        sensors: { ... },
        alarm_cycle: { ... },
        batteries: { ... }
    }
}
```

---

## Data Flow

### Arming Sequence (with PIN)

```
User enters PIN in HA standard alarm dialog or Secure Me alarm card
        |
        v
HA fires alarm_arm_away service (or WS secure_me/arm_away)
        |
        v
alarm_control_panel.async_alarm_arm_away(code)
  |- coordinator.validate_code(code) -> bcrypt check via store
  |  |- ThreadPoolExecutor parallel check across enabled users
  |  +- Returns False on invalid -> log warning, no state change
  +- coordinator.async_arm_away(code)
        |
        v
asyncio.Lock() acquired (state_machine._transition_lock)
        |
        v
Open sensor check (skipped if force=True from push FORCE_ARM)
  |- get_auto_bypass_sensors() -> silently bypass marked sensors
  +- check_for_open_sensors() -> abort if non-bypass sensors open
        |
        v
state_machine.arm_away() returns True
        |
        v
identify_user(code) + identify_user_id(code) -> _armed_by + _armed_by_id
        |
        v
State machine: disarmed -> arming
        |
        v
Exit delay countdown starts (default 30s)
  |- _countdown_updated() called every second
  |  +- Writes countdown in-place + async_update_listeners()
  +- Full refresh every 5 seconds
        |
        v
Countdown expires -> armed_away
        |
        v
EVENT_ALARM_ARMED fired (mode=armed_away, armed_by, armed_by_id)
        |
        v
NotificationDispatcher routes:
  +- Push to acting user only (if receive_own_actions=True)
  +- TTS via configured speakers (respects quiet hours)
        |
        v
Zone Manager activates zones for "away" mode + starts monitoring
        |
        v
Coordinator executes modules in parallel (graceful degradation):
  +- Camera: POE smart-check + optional 120s delay + recording
  +- Lock: lock all doors (skip if door open via door_sensor)
  +- Lights: backup state + turn off
  +- Climate: away preset (or away_temperature)
  +- Siren: ready state (no action)
  +- TTS: "armed_away" custom messages on configured speakers
        |
        v
EVENT_secure_me_health_updated fired (throttled 1x/5s)
        |
        v
Frontend receives state update -> sidebar pill + alarm card update
```

### Sensor Trigger Sequence

```
Binary sensor state changes (e.g. door opens)
        |
        v
ZoneManager._sensor_state_changed event handler
        |
        v
Debounce check: last trigger < 500ms ago? -> skip
        |
        v
update_sensor_state(entity_id, state)
  +- new_state=None? -> treated as closed + WARN + notification
  +- "unavailable"/"unknown"? -> treated as closed + DEBUG only
  +- Open state? -> mark zone triggered
        |
        v
Sensor in a sensor_group?
  +- Group records activation, returns True only if event_count met
  +- If group not satisfied, no trigger fired
        |
        v
Zone trigger callback (debounced, scheduled via async_create_task)
        |
        v
coordinator._zone_triggered(zone)
  +- State machine in arming? -> ignore (user still leaving)
  +- Not armed? -> return
  +- Otherwise call state_machine.trigger_entry_delay(zone_type)
        |
        v
Zone type:
  +- instant -> trigger_alarm() immediately
  +- entry -> start entry delay countdown (state=pending)
  +- interior/perimeter -> trigger_alarm() (no delay)
        |
        v
For pending: countdown shows in alarm card
  +- User enters PIN within delay? -> cancel_pending() -> disarmed
  +- Countdown expires -> trigger_alarm(zone_type)
        |
        v
state_machine.trigger_alarm(source)
  +- Fires _trigger_reset_task (auto-disarm after trigger_time)
        |
        v
EVENT_ALARM_TRIGGERED fired
        |
        v
NotificationDispatcher broadcasts:
  +- Critical push to all receive_critical users (bypasses DND)
  +- TTS via configured speakers
        |
        v
Modules trigger in parallel:
  +- Siren: turn on with configured pattern + duration auto-off
  +- Lights: emergency flash (red/blue) + steady-white at 100%
  +- TTS: triggered custom messages
  +- Camera: continue recording (already on from arm)
  +- Lock: no action (stay locked)
  +- Climate: no action
        |
        v
User disarms with PIN -> disarmed (cancels auto-reset)
OR trigger_time expires -> auto-reset to disarmed
```

### State Restore on HA Restart

```
HA starts up
        |
        v
SecureMeAlarmPanel.__init__() with RestoreEntity mixin
        |
        v
async_added_to_hass()
  +- super().async_added_to_hass()
  +- last = await self.async_get_last_state()
        |
        v
last is None? -> stay disarmed, log debug
        |
        v
last.state in (disarmed, armed_*)? -> restorable
last.state in (arming, pending, triggered)? -> reset to disarmed + warn
        |
        v
coordinator.async_restore_state(state, armed_by)
  +- state_machine.restore_state(state)
  |  +- Sets _current_state directly, no callbacks fired
  +- _armed_by = restored armed_by attribute
  +- _last_arm_mode = state (for push FORCE_ARM)
  +- If armed: zone_manager.start_monitoring(arm_mode)
        |
        v
Alarm operates normally - no false EVENT_ALARM_ARMED fired
```

---

## Constants (const.py)

**Versioning:**
```python
VERSION = "1.4.2"
STORAGE_VERSION_MAJOR = 2
STORAGE_VERSION_MINOR = 0
```

**Retry defaults:**
```python
DEFAULT_RETRY_MAX = 3
DEFAULT_RETRY_DELAY = 2.0       # seconds
DEFAULT_RETRY_BACKOFF = 2.0     # multiplier (2s, 4s, 8s)
```

**Auto-arm:**
```python
AUTO_ARM_AWAY_DELAY = 900       # 15 minutes
AUTO_ARM_PUSH_TITLE = "Secure Me: Auto-armed"
AUTO_ARM_PUSH_MESSAGE = "All residents left home..."
```

**Push notification action events:**
```python
PUSH_EVENT = "mobile_app_notification_action"
EVENT_ACTION_FORCE_ARM       = "SECURE_ME_FORCE_ARM"
EVENT_ACTION_RETRY_ARM       = "SECURE_ME_RETRY_ARM"
EVENT_ACTION_DISARM          = "SECURE_ME_DISARM"
EVENT_ACTION_ARM_AWAY        = "SECURE_ME_ARM_AWAY"
EVENT_ACTION_ARM_HOME        = "SECURE_ME_ARM_HOME"
EVENT_ACTION_ARM_NIGHT       = "SECURE_ME_ARM_NIGHT"
EVENT_ACTION_ARM_VACATION    = "SECURE_ME_ARM_VACATION"
EVENT_ACTION_ARM_HOME_ALONE  = "SECURE_ME_ARM_HOME_ALONE"
EVENT_HOME_ALONE_ACTION_1    = "SECURE_ME_HOME_ALONE_ACTION_1"
EVENT_HOME_ALONE_ACTION_2    = "SECURE_ME_HOME_ALONE_ACTION_2"
```

**States and modes:**
- 7 alarm states (disarmed, arming, armed_away, armed_home, armed_night,
  armed_vacation, armed_home_alone, pending, triggered)
- 4 zone types (entry, instant, interior, perimeter)
- 6 module types (camera, lock, lights, climate, siren, tts)

---

## Dependencies

### manifest.json
```json
{
    "domain": "secure_me",
    "name": "Secure Me",
    "version": "1.4.2",
    "dependencies": ["frontend", "http", "lovelace",
                     "websocket_api", "panel_custom"],
    "iot_class": "local_polling",
    "requirements": ["bcrypt>=4.0.0"]
}
```

### Python Requirements
- Python 3.11 or 3.12
- Home Assistant 2025.1.1+
- bcrypt >= 4.0.0 (PIN hashing)

### Testing Requirements
```
pytest
pytest-homeassistant-custom-component
pytest-asyncio
bcrypt
```

---

## Testing Structure

### Test Organization (291 tests)

```
tests/                                  291 tests across 12 files
+-- conftest.py                         MockHass, MockConfigEntry,
|                                       MockModule, mock_hass_with_batteries
+-- test_const.py                       12  Constants and version sync
+-- test_diagnostics.py                  5  Redaction
+-- test_files.py                       13  Manifest, services, strings, hacs
+-- test_init_.py                        8  Setup, unload, reload
+-- test_modules.py                     43  Module health, lock functional, severity
+-- test_sensors.py                     16  Battery discovery and summary
+-- test_state_machine.py               21  State machine baseline (mock-based)
+-- test_state_machine_v2.py            35  Auto-reset, race condition, real SM
+-- test_store.py                       25  CRUD, fake presence, modules
+-- test_v1_2_0.py                      56  bcrypt, sensor groups, push, profiles
+-- test_zones_edge_cases.py            28  Sensor deleted, unavailable, debounce
+-- test_base_module.py                 29  Retry, degraded state, recovery
```

**Running tests:**
```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_v1_2_0.py -v

# With coverage
pytest tests/ --cov=custom_components/secure_me
```

---

## UTF-8 / Encoding Standards (CRITICAL)

**Absolute ban: no emojis in ANY code file (.js or .py)**

Emojis corrupt to garbled bytes when processed by automation tools.
The `frontend/secure-me-panel.js` provides an `icon()` function with
SVG-based icons - always use that instead of Unicode emojis.

```javascript
// BANNED
<span>📷</span>           // Camera emoji - corrupts to garbled bytes
alert("Saved!")            // Browser-style alerts banned

// CORRECT
<span>${icon('camera')}</span>
this._toast("Saved!", "success");
```

**Validation tools in `custom_components/secure_me/tools/`:**
- `validate_encoding.py <filepath>` - detects garbled UTF-8 sequences
- `clean_encoding.py <filepath>` - removes corrupted byte sequences
- `validate_version.py [--fix]` - ensures version consistency across all
  files (manifest, const.py, panel.py, panel.js, alarm-card.js,
  services.yaml, all .py files)

See `tools/PREVENTION_GUIDE.md` for the complete encoding policy.

---

## GitHub Actions

| Workflow | Status | Notes |
|----------|--------|-------|
| HACS Validation | 7/8 passed | brands/ expected fail until brands PR merged |
| Hassfest Validation | All passed | |
| Pytest Python 3.11 | 291/291 | |
| Pytest Python 3.12 | 291/291 | |
| Version Consistency | All passed | All files validated incl. services.yaml |

---

## Extension Points

### Adding a New Module

1. Create `modules/my_module.py`, inherit from `AlarmModule`
2. Implement `async_arm()`, `async_disarm()`, `async_trigger()`,
   `async_test()`
3. Use `async_call_service_with_retry()` for all critical HA service calls
4. Add export to `modules/__init__.py`
5. Import and instantiate in `coordinator._init_modules()`
6. Add health binary sensor entry in `binary_sensor.py:MODULE_INFO`
7. Add module config schema in `store.py:_default_data()`
8. Add WebSocket handlers in `websocket_api.py` if module has UI config
9. Add frontend dialog in `secure-me-panel.js` (Modules tab)
10. Add tests in `tests/test_modules.py`
11. Bump `VERSION` in all 26+ files via `validate_version.py --fix`

### Adding New Tests

1. Create `tests/test_my_feature.py` with `# VERSION = "X.Y.Z"` header
2. Import fixtures from `conftest.py`
3. Use `@pytest.mark.asyncio` for async tests
4. Use `MockHass`, `MockConfigEntry` for isolation (no real HA needed)
5. No emojis, no non-ASCII characters in test files
6. Run: `pytest tests/test_my_feature.py -v`

### Adding a New WebSocket Endpoint

1. Define schema with `vol.Required("type"): f"{DOMAIN}/my_endpoint"`
2. Decorate handler with `@websocket_api.async_response` or
   `@websocket_api.websocket_command(SCHEMA)`
3. Register in `async_register_websocket_api()` at bottom of file
4. Send response via `connection.send_result(msg["id"], result)`
5. Add frontend caller in `secure-me-panel.js`:
   `await this._ws({type: "secure_me/my_endpoint", ...})`
6. Add tests if endpoint has non-trivial logic

---

## Quality Metrics (v1.4.2)

### Code Quality
- Type hints on most public methods
- Docstrings on all public classes and methods
- Comprehensive error handling with user-facing notifications
- Debug/info/warning/error logging levels used appropriately
- Async/await patterns throughout
- UTF-8 / emoji-free enforced by CI
- Race-safe state transitions via `asyncio.Lock()`
- bcrypt password hashing for user PINs

### Test Coverage
- 291 test cases across 12 files
- Retry and degraded state logic tested (29 tests)
- Zone edge cases (deleted, unavailable, debounce) - 28 tests
- State machine async behaviour (auto-reset, race) - 35 tests
- bcrypt + sensor groups + push actions - 56 tests
- Module health, severity scoring, lock functional - 43 tests
- Mock fixtures available for all HA components

### Home Assistant Compliance
- Config entry based with options flow
- Modern entity naming (`_attr_has_entity_name = True`)
- Device registration via device_registry
- DataUpdateCoordinator pattern
- Async/await throughout (no blocking calls)
- Single external dependency (bcrypt)
- HACS compliant (7/8 - brands expected)
- Hassfest validated
- RestoreEntity for state persistence
- System Health integration
- Diagnostics with PII redaction

---

**Documentation Version:** 1.4.2
**Last Updated:** 2026-04-26
**Architecture:** Modular, event-driven, async, race-safe, UTF-8 clean
**Status:** v1.4.2 Released - production
