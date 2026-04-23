# Secure Me - Project Structure

Complete technical documentation of the Secure Me integration architecture and file organization.

**Version:** 1.4.2
**Last Updated:** 2026-04-23

---

## Directory Structure

```
secure-me/                              # GitHub repo root
|
+-- custom_components/secure_me/        # Integration root
|   |
|   +-- __init__.py                     # Integration entry point
|   +-- manifest.json                   # Integration metadata (v0.9.0, panel_custom dep)
|   +-- const.py                        # Constants, retry config, error messages
|   +-- config_flow.py                  # GUI configuration wizard
|   +-- panel.py                        # Panel registration (Alarmo-style)
|   |
|   +-- coordinator.py                  # DataUpdateCoordinator (perf optimized v0.6.0)
|   +-- state_machine.py                # Alarm state logic (race-safe, auto-reset v0.5.0)
|   +-- zones.py                        # Zone manager (debounced v0.6.0, edge-case safe v0.5.0)
|   +-- module_manager.py               # Module lifecycle manager
|   +-- store.py                        # Persistent storage
|   +-- websocket_api.py                # WebSocket API (~800 lines)
|   +-- system_health.py                # HA system health integration (10 metrics)
|   +-- diagnostics.py                  # Enhanced diagnostics (6 sections)
|   |
|   +-- alarm_control_panel.py          # Main alarm entity
|   +-- binary_sensor.py                # Module health sensors (6 sensors)
|   +-- sensor.py                       # Battery sensors (auto-discovery, cached)
|   +-- switch.py                       # Switch entities
|   +-- select.py                       # Select entities
|   |
|   +-- modules/
|   |   +-- __init__.py                 # Module exports
|   |   +-- base.py                     # Base class: retry + degraded state (v0.4.0)
|   |   +-- camera.py                   # Camera: POE control, recording, smart delay
|   |   +-- lock.py                     # Lock: exponential backoff retry
|   |   +-- lights.py                   # Lights: auto control, emergency flash
|   |   +-- climate.py                  # Climate: multi-zone heating/cooling
|   |   +-- siren.py                    # Siren: alarm sounds and patterns
|   |   +-- tts.py                      # TTS: announcements (Danish support)
|   |
|   +-- frontend/
|   |   +-- secure-me-panel.js          # ~4400 lines, EMOJI-FREE
|   |
|   +-- translations/
|       +-- en.json                     # English
|       +-- da.json                     # Danish
|
+-- tests/                              # Unit tests (repo root, NOT custom_components)
|   +-- __init__.py
|   +-- conftest.py                     # Pytest fixtures and mocks
|   +-- test_const.py                   # Constants tests
|   +-- test_diagnostics.py             # Diagnostics tests
|   +-- test_files.py                   # File structure / manifest tests
|   +-- test_modules.py                 # Module system tests
|   +-- test_sensors.py                 # Battery sensor tests
|   +-- test_state_machine.py           # State machine tests (v0.3.0 baseline)
|   +-- test_store.py                   # Store tests
|   +-- test_base_module.py             # Retry/degraded state tests (NEW v0.9.0)
|   +-- test_zones_edge_cases.py        # Sensor edge case tests (NEW v0.9.0)
|   +-- test_state_machine_v2.py        # State machine v0.5.0 edge case tests (NEW v0.9.0)
|
+-- .github/workflows/
|   +-- validate.yaml                   # HACS + Hassfest + version consistency
|   +-- pytest.yaml                     # Pytest 3.11 + 3.12
|
+-- brands/secure_me/                   # 8 branding images (HACS requirement)
|   +-- icon.png / icon@2x.png
|   +-- logo.png / logo@2x.png
|   +-- dark versions of the above
|
+-- validate_version.py                 # Version consistency checker (26+ files)
+-- validate_encoding.py                # UTF-8 / emoji validator
+-- clean_encoding.py                   # Encoding cleanup tool
|
+-- hacs.json                           # HACS metadata
+-- README.md                           # v0.9.0 full documentation
+-- CHANGELOG.md                        # v0.0.1 through v0.9.0
+-- INSTALLATION.md                     # Clean install guide
+-- info.md                             # HACS store page
+-- LICENSE                             # MIT
+-- requirements.txt
```

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
|  |  - Setup & initialization                             |  |
|  |  - Config entry management                            |  |
|  |  - Device registration                                |  |
|  |  - Panel registration                                 |  |
|  +-------------------------+-----------------------------+  |
|                            |                                 |
|                            v                                 |
|  +-------------------------------------------------------+  |
|  |          Coordinator (coordinator.py)                 |  |
|  |  - State management (perf optimized v0.6.0)          |  |
|  |  - Module coordination (graceful degradation v0.4.0) |  |
|  |  - Event handling                                     |  |
|  |  - Health event throttling (max 1x/5s v0.6.0)        |  |
|  +------+----------------+---------------+---------------+  |
|         |                |               |                   |
|   +-----+-----+   +------+----+   +------+-----+           |
|   |   State   |   |   Zone    |   |   Module   |           |
|   |  Machine  |   |  Manager  |   |  Manager   |           |
|   | (v0.5.0)  |   | (v0.5.0+  |   |            |           |
|   |           |   |  v0.6.0)  |   |            |           |
|   +-----------+   +-----------+   +------------+           |
|                                                              |
|  +-------------------------------------------------------+  |
|  |         Alarm Control Panel Entity                    |  |
|  |  States: disarmed, arming, armed_*, pending,         |  |
|  |          triggered                                    |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  |         Smart Modules (6 total)                       |  |
|  |  +--------+ +------+ +--------+ +-------+            |  |
|  |  | Camera | | Lock | | Lights | |Climate|            |  |
|  |  +--------+ +------+ +--------+ +-------+            |  |
|  |  +-------+ +-----+                                   |  |
|  |  | Siren | | TTS |                                   |  |
|  |  +-------+ +-----+                                   |  |
|  |  All modules: retry + degraded state (v0.4.0)        |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  |  Health & Battery Monitoring                          |  |
|  |  - 6 module health binary sensors                    |  |
|  |  - Battery auto-discovery (3 tracking entities)      |  |
|  |  - System health integration (10 metrics)            |  |
|  |  - Enhanced diagnostics (6 sections)                 |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  |  Frontend Panel (secure-me-panel.js ~4400 lines)     |  |
|  |  - Toast notifications (replaces all alert() calls)  |  |
|  |  - Async confirm dialogs (replaces confirm())        |  |
|  |  - Module health badges per module                   |  |
|  |  - Triggered state pulse animation                   |  |
|  |  - Render batching (_queueRender 50ms debounce)      |  |
|  +-------------------------------------------------------+  |
|                                                              |
|  +-------------------------------------------------------+  |
|  |  Persistent Storage (store.py)                       |  |
|  |  - Configuration data                                |  |
|  |  - User preferences                                  |  |
|  |  - Test results (last 10)                            |  |
|  |  - Audit logs                                        |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
```

---

## Core Components

### __init__.py (Integration Entry)

**Purpose:** Integration lifecycle management

**Key Functions:**
```python
async def async_setup_entry(hass, entry):
    # 1. Initialize store
    # 2. Initialize coordinator
    # 3. Register WebSocket API
    # 4. Register frontend panel
    # 5. Setup platforms (alarm_control_panel, binary_sensor,
    #    sensor, switch, select)

async def async_unload_entry(hass, entry):
    # 1. Shutdown coordinator
    # 2. Cleanup modules
    # 3. Remove listeners
    # 4. Unload platforms
```

**Data Structure:**
```python
hass.data[DOMAIN] = {
    "store": <Store>,                   # Global
    "_websocket_registered": True,      # Global
    "_panel_registered": True,          # Global
    "entry_id_1": {                     # Per-entry
        COORDINATOR: <coordinator>,
        UNDO_UPDATE_LISTENER: <listener>,
    }
}
```

---

### coordinator.py (State Coordinator)

**Purpose:** Central state management and module coordination

**Class:** `SecureMeCoordinator(DataUpdateCoordinator)`

**v0.6.0 Performance Changes:**
- `_countdown_updated()` writes countdown in-place + calls `async_update_listeners()` instead of full refresh every second (~80% reduction)
- Health events throttled to max 1x per 5 seconds via `time.monotonic()`
- Full refresh only at countdown=0 or every 5 seconds

**Key Methods:**
```python
async def async_arm(self, mode, code=None):
    """Arm the alarm."""

async def async_disarm(self, code):
    """Disarm the alarm."""

async def _execute_modules(self, action, call):
    """Unified module executor - graceful degradation (v0.4.0)."""

async def _zone_triggered(self, zone):
    """Handle zone trigger - ignores triggers during arming state (v0.5.0)."""

async def _countdown_updated(self, countdown):
    """Perf-optimized countdown tick handler (v0.6.0)."""

async def _state_changed(self, new_state, countdown):
    """Handle state machine state change."""
```

---

### state_machine.py (State Logic)

**Purpose:** Alarm state transitions and validation

**Class:** `AlarmStateMachine`

**States:**
```
disarmed -> arming -> armed_away / armed_home / armed_night / armed_vacation
armed_* -> pending -> triggered
triggered -> disarmed (manual or auto-reset)
```

**v0.5.0 Edge Case Fixes:**
- `_cancel_countdown()` is async and awaits task completion (race condition fix)
- `asyncio.Lock()` on all arm/disarm methods (simultaneous transition guard)
- `_trigger_reset_timer()` -- auto-resets to disarmed after `trigger_time` seconds (was TODO since v0.1.0)
- Double-arm guard: returns False if already armed
- Arming-state guard: zone triggers ignored while in `arming` state

**Key Methods:**
```python
async def arm_away(self, skip_delay=False) -> bool
async def arm_home(self, skip_delay=False) -> bool
async def arm_night(self, skip_delay=False) -> bool
async def arm_vacation(self, skip_delay=False) -> bool
async def disarm(self) -> bool
async def trigger_alarm(self, source) -> bool
async def trigger_entry_delay(self, zone_type) -> bool
async def cancel_pending(self) -> bool
async def _cancel_countdown(self) -> None    # async, awaited (v0.5.0)
async def _trigger_reset_timer(self) -> None # auto-reset (v0.5.0)
def cleanup(self) -> None
```

---

### zones.py (Zone Manager)

**Purpose:** Multi-zone management, sensor grouping and event handling

**Class:** `ZoneManager`

**v0.5.0 Edge Case Fixes:**
- `new_state=None` (entity deleted from HA): treated as closed, user notified
- `unavailable`/`unknown` state: treated as closed, user notified
- `check_for_open_sensors()`: skips unavailable/missing sensors (arming not blocked)
- Sensor opens during exit delay: ignored (user still leaving)

**v0.6.0 Performance:**
- Per-sensor debounce: 500ms cooldown per entity_id
- Flapping sensors fire trigger callback only once within debounce window

**Key Methods:**
```python
def add_zone(self, zone_id, zone_type, sensors, enabled) -> None
def update_sensor_state(self, entity_id, state) -> tuple[bool, Zone | None]
def check_for_open_sensors(self) -> bool
def start_monitoring(self) -> None
def stop_monitoring(self) -> None
def clear_all_triggers(self) -> None
```

---

### modules/base.py (Base Module Class)

**Purpose:** Abstract base class with centralized retry and degraded state logic

**v0.4.0 Features:**
- `async_call_service_with_retry()`: 3 retries, 2s -> 4s -> 8s exponential backoff
- `async_call_service()`: single attempt (for test calls and state reads)
- Degraded state tracking: `self._degraded`, `self._consecutive_errors`
- `_on_failure()`: sets degraded, fires `persistent_notification` to user
- `_on_success()`: clears degraded, fires recovery notification if previously degraded
- Configurable per module via `retry_max`, `retry_delay`, `retry_backoff` config keys

**Interface:**
```python
class AlarmModule(ABC):
    # Properties
    @property
    def enabled(self) -> bool
    @property
    def degraded(self) -> bool        # True if all retries exhausted
    @property
    def module_name(self) -> str

    # Abstract (must implement)
    async def async_arm(self, mode) -> bool
    async def async_disarm(self) -> bool
    async def async_trigger(self) -> bool
    async def async_test(self) -> dict

    # Provided by base
    async def async_call_service_with_retry(...) -> bool   # 3 retries + backoff
    async def async_call_service(...) -> bool              # single attempt
    def backup_state(self, entity_id) -> None
    def get_backup_state(self, entity_id) -> dict | None
    def is_entity_available(self, entity_id) -> bool
    def get_entity_state(self, entity_id) -> str | None
    def enable(self) -> None          # clears degraded state
    def disable(self) -> None
```

**Retry coverage across all 6 modules: 20 retry-protected service calls total.**

| Module | Retry calls |
|--------|-------------|
| Lock | 3 (lock on arm, unlock on disarm, test) |
| Camera | 4 (POE on/off, recording on/off) |
| Lights | 3 (off on arm, off/restore on disarm, on trigger) |
| Climate | 5 (away preset/temp, home preset, restore, eco) |
| Siren | 3 (play, stop, gateway light off) |
| TTS | 2 (arm announcement, trigger announcement) |

---

## Frontend Architecture

### secure-me-panel.js (~4400 lines)

**Single-file Custom Element -- EMOJI-FREE**

**Render Strategy:**
- `_render()` -- immediate, for user actions (tab switch, dialog open)
- `_queueRender()` -- 50ms debounce, for data loads and background updates (v0.6.0)

**UX Improvements (v0.7.0):**
- `_toast(msg, type)` -- replaces all 38 `alert()` calls (success/error/warning/info)
- `_confirm(msg, title)` -- async Promise overlay, replaces all `confirm()` calls
- Module health badges on Modules tab (OK/Warning/Error/Degraded)
- Triggered state pulses red, pending state yellow in sidebar + mobile header

**Key Architecture Notes:**
- `subscribeEvents()` must be **awaited** -- returns a Promise, not a function
- `_healthUpdateUnsubscribe` uses `typeof === 'function'` guard before calling
- Mobile bottom navigation bar with 5 tabs + More drawer (<=768px)
- iOS safe-area support

**Tabs:**
1. Sensors -- sensor management
2. Zones -- zone configuration
3. Users -- user and NFC management
4. Modules -- module configuration + health badges
5. Automations -- custom automations
6. Settings -- system configuration
7. Testing -- health monitoring and test execution

---

## WebSocket API

### websocket_api.py

**Configuration commands:**
```
secure_me/get_config
secure_me/save_config
secure_me/update_zone
secure_me/delete_zone
secure_me/update_user
secure_me/delete_user
```

**Alarm control commands:**
```
secure_me/arm
secure_me/disarm
secure_me/get_state
```

**Testing commands:**
```
secure_me/run_test          # level: quick | standard | full
secure_me/get_test_results  # last 10 results
secure_me/get_health_status
secure_me/get_battery_status
```

**Message Format:**
```javascript
// Request
{ type: "secure_me/run_test", id: 123, level: "standard" }

// Response
{
    id: 123,
    type: "result",
    success: true,
    result: {
        status: "PASS",
        duration: 58,
        modules: { ... },
        batteries: { ... }
    }
}
```

---

## Data Flow

### Arming Sequence

```
User clicks "Arm Away"
        |
        v
Frontend sends WebSocket command
        |
        v
Coordinator validates code
        |
        v
asyncio.Lock() acquired (v0.5.0)
        |
        v
State Machine: disarmed -> arming
        |
        v
Exit delay countdown starts
async_update_listeners() every second (v0.6.0)
Full refresh every 5s only
        |
        v
Countdown expires -> armed_away
        |
        v
Zone Manager activates zones + starts monitoring
        |
        v
Module Manager arms modules (parallel, graceful degradation v0.4.0):
        +-> Camera: POE smart check + optional delay + recording
        +-> Lock: lock doors (retry x3 if needed)
        +-> Lights: turn off (retry x3)
        +-> Climate: eco/away preset (retry x5)
        +-> Siren: ready state
        +-> TTS: "Armed Away" announcement
        |
        v
Health event fired (throttled max 1x/5s v0.6.0)
        |
        v
Frontend receives state update -> UI shows "Armed Away"
```

### Sensor Trigger Sequence

```
Sensor state changes to "on"
        |
        v
Debounce check: last trigger < 500ms ago? -> skip (v0.6.0)
        |
        v
ZoneManager.update_sensor_state()
        +-> None state (entity deleted)? -> treat as closed + notify
        +-> "unavailable"/"unknown"?     -> treat as closed + notify
        +-> Normal open state?           -> mark zone triggered
        |
        v
Is alarm in "arming" state?
        +-> Yes -> ignore (user still leaving) (v0.5.0)
        +-> No  -> continue
        |
        v
Zone type?
        +-> "instant" -> trigger_alarm() immediately
        +-> "entry"   -> start entry delay countdown (pending state)
        |
        v
Entry delay expires -> trigger_alarm()
        |
        v
_trigger_reset_task created (auto-reset after trigger_time) (v0.5.0)
        |
        v
Module Manager triggers all modules:
        +-> Siren: sound alarm
        +-> Lights: emergency blink
        +-> TTS: "Alarm triggered!"
        +-> Camera: ensure recording
        |
        v
User disarms with code -> disarmed
OR trigger_time expires -> auto-reset to disarmed (v0.5.0)
```

---

## Data Storage

### store.py

**Storage Location:** `/config/.storage/secure_me.panel_config`

**Data Structure:**
```json
{
    "version": 1,
    "key": "secure_me.panel_config",
    "data": {
        "zones": { ... },
        "users": { ... },
        "automations": { ... },
        "settings": { ... },
        "test_results": {
            "last_test": "2026-02-21T10:00:00",
            "last_result": "PASS",
            "history": [ ... ]
        }
    }
}
```

---

## Constants (const.py)

**Key constants added in v0.4.0:**
```python
# Retry defaults
DEFAULT_RETRY_MAX = 3
DEFAULT_RETRY_DELAY = 2.0       # seconds
DEFAULT_RETRY_BACKOFF = 2.0     # multiplier (2s, 4s, 8s)

# Notification IDs
NOTIFY_ID_MODULE_ERROR = "secure_me_module_error"
NOTIFY_ID_RECOVERY = "secure_me_recovery"

# Error messages (EN + DA)
ERROR_RETRY_EXHAUSTED_EN = "Secure Me: Module '{module}' failed after {retries} retries."
ERROR_RECOVERY_OK_EN = "Secure Me: Module '{module}' recovered successfully."
```

---

## Dependencies

### manifest.json
```json
{
    "domain": "secure_me",
    "name": "Secure Me",
    "version": "0.9.0",
    "dependencies": ["frontend", "http", "websocket_api", "panel_custom"],
    "iot_class": "local_polling",
    "requirements": []
}
```

### Python Requirements
- Python 3.11+
- Home Assistant 2025.1.1+
- No external libraries

### Testing Requirements
```
pytest
pytest-homeassistant-custom-component
pytest-asyncio
```

---

## Testing Structure

### Test Organization (v0.9.0)

```
tests/                              168 tests total
+-- conftest.py                     MockHass, MockConfigEntry, MockModule fixtures
+-- test_const.py                   Constants and error message tests
+-- test_diagnostics.py             Diagnostics section tests
+-- test_files.py                   Manifest, hacs.json, file structure tests
+-- test_modules.py                 Module base interface, health, entity extraction
+-- test_sensors.py                 Battery sensor platform tests
+-- test_state_machine.py           State machine baseline tests (v0.3.0, 100 tests)
+-- test_store.py                   Store load/save tests
+-- test_base_module.py             Retry logic, degraded state, recovery (NEW v0.9.0)
+-- test_zones_edge_cases.py        Sensor deleted/unavailable, debounce (NEW v0.9.0)
+-- test_state_machine_v2.py        Auto-reset, race condition, exit delay (NEW v0.9.0)
```

**Test breakdown:**
| File | Tests | Covers |
|------|-------|--------|
| test_base_module.py | 12 | v0.4.0: retry, degraded state, recovery notifications |
| test_zones_edge_cases.py | 28 | v0.5.0+v0.6.0: sensor edge cases, debounce |
| test_state_machine_v2.py | 28 | v0.5.0: auto-reset, race condition, transition lock |
| Existing files | 100 | v0.3.0 baseline coverage |
| **Total** | **168** | |

**Running Tests:**
```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/test_base_module.py -v

# With coverage
pytest tests/ --cov=custom_components/secure_me
```

---

## UTF-8 / Encoding Standards (CRITICAL)

**Absolute ban: no emojis in ANY code file (.js or .py)**

Emojis corrupt to garbled text when processed by automation tools.

```javascript
// BANNED
alert("Saved!")
<span>camera</span>    // Unicode char

// CORRECT
this._toast("Saved!", "success");
<span>${icon('camera')}</span>
```

**Validate before every commit:**
```bash
python3 validate_encoding.py frontend/secure-me-panel.js
python3 validate_version.py
```

---

## GitHub Actions (v0.9.0)

| Workflow | Status | Notes |
|----------|--------|-------|
| HACS Validation | 7/8 passed | brands/ expected fail -- OK |
| Hassfest Validation | All passed | |
| Pytest Python 3.11 | 168/168 | |
| Pytest Python 3.12 | 168/168 | |
| Version Consistency | Passed | 26+ files checked |

---

## File Sizes (v0.9.0 estimated)

| Component | Lines | Notes |
|-----------|-------|-------|
| secure-me-panel.js | ~4400 | EMOJI-FREE |
| websocket_api.py | ~800 | |
| coordinator.py | ~500 | perf optimized |
| state_machine.py | ~300 | race-safe, auto-reset |
| zones.py | ~280 | debounced, edge-case safe |
| base.py | ~200 | retry + degraded logic |
| tests/ (total) | ~2500 | 168 test cases |

---

## Extension Points

### Adding a New Module

1. Create `modules/my_module.py`, inherit from `AlarmModule`
2. Implement `async_arm()`, `async_disarm()`, `async_trigger()`, `async_test()`
3. Use `async_call_service_with_retry()` for all critical HA service calls
4. Add to `modules/__init__.py`
5. Import and initialize in `coordinator.py`
6. Add health binary sensor in `binary_sensor.py`
7. Add configuration schema in `const.py`
8. Add tests in `tests/test_modules.py`

### Adding New Tests

1. Create `tests/test_my_feature.py`
2. Import fixtures from `conftest.py` (`mock_hass`, `mock_config_entry`, etc.)
3. Use `@pytest.mark.asyncio` for async tests
4. Use `MockHass`, `MockConfigEntry` for isolation (no real HA needed)
5. No emojis, no non-ASCII characters in test files
6. Run: `pytest tests/test_my_feature.py -v`

---

## Quality Metrics (v0.9.0)

### Code Quality
- Type hints (partial coverage)
- Docstrings on all public methods
- Comprehensive error handling with user notifications
- Debug/info/warning/error logging throughout
- Async/await patterns throughout
- UTF-8 / emoji-free enforced by CI

### Test Coverage
- 168 test cases (100 baseline + 68 new v0.9.0)
- Retry and degraded state logic tested
- Zone edge cases tested (sensor deleted, unavailable, debounce)
- State machine async behaviour tested (auto-reset, race conditions)
- Mock fixtures for all HA components

### Home Assistant Compliance
- Config entry based
- Modern entity naming
- Device registration
- DataUpdateCoordinator pattern
- Async/await throughout
- No external dependencies
- HACS compliant (7/8, brands expected)
- Hassfest validated

---

**Documentation Version:** 0.9.0
**Last Updated:** 2026-02-21
**Architecture:** Modular, event-driven, async, race-safe, UTF-8 clean
**Status:** v0.9.0 Pre-Release -- targeting v1.0.0
