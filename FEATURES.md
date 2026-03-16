# Secure Me - Features

Complete feature documentation for the Secure Me Home Assistant alarm system integration.

**Version:** 1.1.0
**Last Updated:** 2026-03-16

---

## Table of Contents

1. [Core Alarm System](#core-alarm-system)
2. [Zone Management](#zone-management)
3. [Smart Modules](#smart-modules)
4. [Error Handling and Reliability](#error-handling-and-reliability)  -- NEW v0.4.0
5. [Edge Case Handling](#edge-case-handling)  -- NEW v0.5.0
6. [Performance](#performance)  -- NEW v0.6.0
7. [User Experience](#user-experience)  -- NEW v0.7.0
8. [Testing Framework](#testing-framework)
9. [Health Monitoring](#health-monitoring)
10. [Battery Tracking](#battery-tracking)
11. [Configuration Dashboard](#configuration-dashboard)
12. [Automation and Events](#automation-and-events)
13. [Advanced Features](#advanced-features)

---

## What's New

### v1.1.0 -- Feature Release
- Environmental sensors always-on section with forced notifications and remove button
- TTS multi-service support: cloud_say, google_translate_say, google_say, piper, voice_rss, custom
- Sensor hide/exclude: inactive sensors have Hide button, irrelevant device_trackers auto-hidden
- User to person tracker binding for presence-based automation
- Fake Presence toggle on Sensors tab blocks automatic arming
- Home Alone Monitor camera selector in Future tab
- Chevron SVG bug fix (giant icon in module panels)

### v1.0.0 -- Production Release
- HACS submission completed, end-to-end testing passed, panel flickering resolved

### v0.9.0 -- Pre-Release Testing
- 68 new unit tests covering v0.4.0-v0.8.0 changes
- Total test suite: 168 tests (100 baseline + 68 new)
- Full coverage: retry logic, edge cases, state machine async behaviour

### v0.8.0 -- Documentation
- README.md complete rewrite with full API reference
- CHANGELOG.md all versions documented
- INSTALLATION.md clean install guide
- info.md HACS store page updated

### v0.7.0 -- UX Improvements
- Toast notification system replaces all 38 alert() calls
- In-panel confirm dialogs replace browser confirm()
- Module health badges on Modules tab (OK/Warning/Error/Degraded)
- Triggered state pulses red, pending state pulses yellow

### v0.6.0 -- Performance
- Countdown uses async_update_listeners() instead of full refresh every second (~80% less work)
- Health events throttled to max 1x per 5 seconds
- Per-sensor debounce: 500ms cooldown prevents flapping triggers
- Frontend render batching: 50ms debounce on data loads

### v0.5.0 -- Edge Case Handling
- Race condition fix: _cancel_countdown() is now async and properly awaited
- Auto-reset after trigger_time (was TODO since v0.1.0)
- Sensor deleted from HA while armed: graceful handling, user notified
- Sensor unavailable while armed: treated as closed, not as trigger
- Sensor opens during exit delay: ignored (user still leaving)

### v0.4.0 -- Error Handling
- Centralized retry with exponential backoff across all 6 modules (20 calls total)
- Graceful degradation: one module failure does not stop others
- Degraded state tracking per module with user notifications
- Recovery notifications when a degraded module recovers

---

## Core Alarm System

### Arming Modes

5 distinct modes for different scenarios:

| Mode | Use Case | Typical Sensors Active |
|------|----------|------------------------|
| Armed Home | Evening, family home | Perimeter only (doors/windows) |
| Armed Night | Sleeping | Downstairs + perimeter |
| Armed Away | Work, short absence | All sensors |
| Armed Vacation | Extended absence | All sensors + special rules |
| Disarmed | Daily living | None |

### State Machine

8 intelligent states with race-condition-safe transitions (v0.5.0):

```
DISARMED
    |
    | ARM command + asyncio.Lock() acquired
    v
ARMING  (exit delay countdown)
    |
    | Countdown expires
    v
ARMED_*  (away / home / night / vacation)
    |
    | Sensor triggered (ignored if still in ARMING -- v0.5.0)
    v
PENDING  (entry delay countdown)
    |
    +-- Code entered in time --> DISARMED
    |
    | Countdown expires
    v
TRIGGERED
    |
    +-- Manual disarm  --> DISARMED
    |
    | trigger_time expires (auto-reset -- v0.5.0)
    v
DISARMED
```

Race condition protection (v0.5.0):
- asyncio.Lock() on all arm/disarm methods
- _cancel_countdown() awaits task completion before proceeding
- Double-arm guard: returns False if already armed or arming

### Entry/Exit Delays

- Exit delay: configurable time to leave after arming (default 30s)
- Entry delay: configurable time to disarm after sensor trigger (default 30s)
- Visual countdown in real-time in the panel
- TTS countdown announcements (optional)
- Auto-reset: alarm automatically returns to disarmed after trigger_time seconds

### Code Protection

- 4-6 digit PIN codes
- Multiple user codes supported
- Retry limit with lockout after failures
- Code history logging
- NFC tag support (planned)

---

## Zone Management

### Multi-Zone Architecture

Create independent security zones for different areas of your home.

**Zone Types:**

| Type | Behaviour |
|------|-----------|
| Entry | Starts entry delay countdown on trigger |
| Instant | Triggers alarm immediately, no delay |
| Interior | Active in away mode only |
| Perimeter | Active in all armed modes |

**Zone Features:**
- Independent monitoring per zone
- Flexible sensor grouping
- Mode-based activation (arm_away only, etc.)
- Zone bypass for temporary disabling
- Trigger callbacks for automation

### Sensor Edge Case Handling (v0.5.0)

**Sensor deleted from HA while armed:**
- Treated as closed (not as open/trigger)
- Persistent notification sent to user
- No false alarm triggered

**Sensor goes unavailable or unknown while armed:**
- Treated as closed (prevents false alarms during WiFi outages)
- Persistent notification sent to user

**Sensor opens during exit delay:**
- Ignored -- user is still leaving the building
- Monitored normally once fully armed

**check_for_open_sensors() at arming time:**
- Skips unavailable and missing sensors
- Arming is not blocked by an offline sensor

### Sensor Debounce (v0.6.0)

- 500ms per-sensor cooldown on zone trigger callbacks
- Each sensor tracked independently
- Flapping sensors (on/off/on within 500ms) fire callback only once
- Prevents cascading triggers and log spam

---

## Smart Modules

### Overview

6 intelligent modules that respond to alarm state changes:

| Module | Purpose | Retry-protected calls |
|--------|---------|----------------------|
| Camera | POE control, recording management | 4 |
| Lock | Smart lock automation | 3 |
| Lights | Auto control, emergency flash | 3 |
| Climate | Multi-zone heating/cooling | 5 |
| Siren | Alarm sounds and patterns | 3 |
| TTS | Voice notifications (Danish support) | 2 |

**Total: 20 retry-protected HA service calls across all modules.**

All modules share centralized retry logic from the base class (v0.4.0).

---

### Camera Module

**Smart Camera Management:**

POE Port Control:
- Powers cameras on/off via network switch
- Smart delay: skips the 120s boot wait if cameras are already on
- Supports multiple POE switches (Vision, UniFi, etc.)

Recording Modes:
- Armed: continuous recording
- Disarmed: motion-only recording
- Manual: user-controlled

Configuration:
```yaml
enabled: true
poe_switches:
  - switch.vision_port_1_poe
  - switch.vision_port_5_poe
cameras:
  - camera.front_door
  - camera.back_yard
recording_entities:
  - input_select.camera_recording_mode
poe_delay: 120
auto_record: true
```

Actions:
- On Arm: smart POE check + optional delay + start recording (4 retry-protected calls)
- On Disarm: set motion recording, optional POE off
- On Trigger: ensure continuous recording

---

### Lock Module

**Smart Lock Automation:**

Configuration:
```yaml
enabled: true
locks:
  - lock.front_door
  - lock.back_door
lock_on_arm: true
unlock_on_disarm: false
```

Actions:
- On Arm: lock all doors, skip if door sensor shows open (3 retry-protected calls)
- On Disarm: optional unlock
- On Trigger: ensure all locks engaged

Retry behaviour (v0.4.0):
- 3 attempts with 2s -> 4s -> 8s exponential backoff
- Degraded state set if all retries exhausted
- User notified via persistent_notification on failure and on recovery

---

### Lights Module

**Intelligent Lighting Control:**

Flash Patterns:
- Rapid: 0.5s on, 0.5s off
- Slow: 2s on, 2s off
- Intermittent: 5s on, 2s off

Configuration:
```yaml
enabled: true
lights:
  - light.living_room
  - light.kitchen
arm_action: turn_off
disarm_action: restore
flash_on_trigger: true
flash_pattern: rapid
```

Actions:
- On Arm: turn off lights, backup current state (3 retry-protected calls)
- On Disarm: restore previous brightness and state
- On Trigger: flash pattern for configured duration

---

### Climate Module

**Smart Temperature Management:**

Modes:
- Armed Away: eco temperature (16-18 deg C)
- Armed Home/Night: comfort temperature (20-22 deg C)
- Disarmed: restore previous preset

Configuration:
```yaml
enabled: true
thermostats:
  - climate.living_room
  - climate.bedroom
arm_mode: eco
disarm_mode: heat
eco_temperature: 16
comfort_temperature: 21
```

Actions:
- On Arm: set eco preset + temperature (5 retry-protected calls)
- On Disarm: restore comfort mode
- On Trigger: optional freeze protection mode

---

### Siren Module

**Professional Alert System:**

Patterns:
- Continuous: solid alarm sound
- Intermittent: alternating on/off
- Rapid: fast pulsing

Configuration:
```yaml
enabled: true
sirens:
  - siren.alarm_main
pattern: intermittent
duration: 300
volume: 80
```

Actions:
- On Trigger: sound alarm with configured pattern (3 retry-protected calls)
- On Disarm: stop all sirens and reset gateway light

---

### TTS Module

**Voice Notification System:**

Features:
- Danish language support (Google TTS)
- Message templates per alarm state
- Multi-speaker support
- Volume control

Configuration:
```yaml
enabled: true
media_players:
  - media_player.living_room_speaker
language: da
volume: 0.7
message_templates:
  armed: "Alarmen er aktiveret i {mode} tilstand"
  disarmed: "Alarmen er deaktiveret"
  triggered: "ALARM! Zone {zone} er udloest!"
```

Actions:
- On Arm: announce mode (2 retry-protected calls)
- On Disarm: confirm deactivation
- On Trigger: alert with zone information
- Countdown: entry/exit delay announcements

---

## Error Handling and Reliability

### Centralized Retry (v0.4.0)

All 20 critical HA service calls across all 6 modules use exponential backoff retry:

```
Attempt 1 -- immediate
Attempt 2 -- wait 2s
Attempt 3 -- wait 4s
Give up   -- set module to degraded, notify user
```

Configurable per module via config keys:
```yaml
retry_max: 3       # default: 3
retry_delay: 2.0   # seconds, default: 2.0
retry_backoff: 2.0 # multiplier, default: 2.0
```

### Graceful Degradation (v0.4.0)

- One module failing does NOT stop other modules from executing
- Modules track their own degraded state independently
- Coordinator uses unified _execute_modules() with per-module error isolation

### User Notifications (v0.4.0)

On module failure (all retries exhausted):
- persistent_notification created in HA with module name and failed action
- Degraded badge shown on module card in panel

On module recovery (first successful call after degraded state):
- persistent_notification created confirming recovery
- Badge updated to OK automatically

---

## Edge Case Handling

All edge cases added in v0.5.0:

| Scenario | Behaviour |
|----------|-----------|
| Sensor deleted from HA while armed | Treated as closed, persistent_notification sent |
| Sensor unavailable/unknown while armed | Treated as closed, persistent_notification sent |
| Sensor opens during exit delay (arming) | Ignored, alarm not triggered |
| Rapid arm -> disarm -> arm | asyncio.Lock() prevents race condition |
| Countdown task cancel | Awaited properly, no task leak into next cycle |
| Already triggered + trigger again | Guard returns False, no double-schedule |
| trigger_time = 0 | Auto-reset disabled, manual disarm only |
| Arming with offline sensors | Skipped in open sensor check, arming not blocked |

---

## Performance

### Countdown Optimization (v0.6.0)

Previous: full coordinator refresh every second during countdown
(full entity update + health events for all listeners)

New:
- Write countdown value directly to self.data in-place
- Call async_update_listeners() -- lightweight, updates countdown sensor only
- Full refresh only at countdown=0 or every 5 seconds
- Result: ~80% reduction in coordinator work during entry/exit delays

### Health Event Throttling (v0.6.0)

- secure_me_health_updated event throttled to max 1x per 5 seconds
- Prevents health events from firing every countdown tick
- Uses time.monotonic() for zero-overhead timing

### Sensor Debounce (v0.6.0)

- 500ms per-sensor cooldown on zone trigger callbacks
- Each sensor tracked independently in _last_trigger_time dict
- Flapping sensors fire callback only once per debounce window

### Frontend Render Batching (v0.6.0)

- _loadData() and health subscription handler use _queueRender() with 50ms debounce
- Parallel data loads merge into one DOM update instead of multiple redraws
- Direct _render() reserved for immediate user actions (tab switch, dialog open)

---

## User Experience

### Toast Notifications (v0.7.0)

Replaces all 38 alert() calls with styled in-panel toasts:

| Type | Colour | Use |
|------|--------|-----|
| success | Green | Save confirmed, test passed |
| error | Red | Save failed, test failed |
| warning | Yellow | Non-critical issue |
| info | Blue | Informational message |

- Auto-dismiss after 4 seconds
- Manual close button
- Animates in from right, fades out
- No blocking: multiple toasts can stack

### Confirm Dialogs (v0.7.0)

Replaces browser confirm() with styled async overlay dialogs:
- Descriptive message tailored to the action ("This zone and all its sensors will be removed")
- Cancel and Delete buttons with distinct visual styling
- Click-outside to dismiss
- Returns a Promise -- fully awaitable in async flow

### Module Health Badges (v0.7.0)

Each module card on the Modules tab shows a live badge:

| Badge | Meaning |
|-------|---------|
| OK | All entities available, no errors |
| Warning | Non-critical issue (e.g. 0 entities configured) |
| Error | Entity unavailable or health check failed |
| Degraded | All retries exhausted, module in degraded state (v0.4.0) |

Updates automatically when health event fires -- no polling needed.

### State Pulse Animations (v0.7.0)

- Triggered state: status pill pulses red in sidebar and mobile header
- Pending state: status pill shown in yellow
- CSS @keyframes animation -- zero JavaScript polling overhead

### Mobile Navigation (v0.3.3)

- Bottom navigation bar on screens 768px and below
- 5 primary tabs visible + More drawer for remaining tabs
- Mobile top header with logo and alarm status pill
- iOS safe-area inset support

---

## Testing Framework

### Test Levels

**Quick Test (~30 seconds)**
- Module configuration structure validation
- Required fields present
- Entity ID format checks
- Basic syntax validation

Best for: after configuration changes, quick pre-arm check

**Standard Test (~60 seconds)**
- All Quick checks
- Entity availability verification
- Module health status check
- Configuration consistency

Best for: regular health monitoring, post-installation verification

**Full Test (~90 seconds)**
- All Standard checks
- Battery status scan
- Integration health metrics
- WebSocket connectivity check
- Performance metrics

Best for: complete system validation, pre-production testing

### Test Execution

Via Configuration Panel:
1. Open Secure Me panel, navigate to Testing tab
2. Select test level (Quick / Standard / Full)
3. Click "Run Test"
4. Monitor real-time progress
5. Review detailed results per module

Via Command Line:
```bash
# All 168 unit tests
pytest tests/ -v

# Specific new test files
pytest tests/test_base_module.py -v
pytest tests/test_zones_edge_cases.py -v
pytest tests/test_state_machine_v2.py -v

# With coverage report
pytest tests/ --cov=custom_components/secure_me
```

### Test Results

| Result | Meaning |
|--------|---------|
| PASS | All critical tests passed |
| WARNING | Non-critical issues found (does not block PASS) |
| FAIL | One or more critical tests failed |
| UNKNOWN | Tests not run yet |

Result details include:
- Module-by-module breakdown
- Entity availability per module
- Configuration validation results
- Error messages with suggested solutions
- Timestamp and duration
- Last 10 results persisted across restarts

### Unit Test Suite (v0.9.0)

168 tests across 11 test files:

| File | Tests | Covers |
|------|-------|--------|
| test_base_module.py | 12 | Retry, degraded state, recovery notifications |
| test_zones_edge_cases.py | 28 | Sensor deleted/unavailable, debounce, open sensor check |
| test_state_machine_v2.py | 28 | Auto-reset, race condition fix, transition lock, async |
| Existing 8 files | 100 | Baseline v0.3.0 coverage |
| **Total** | **168** | |

GitHub Actions runs full suite on Python 3.11 and 3.12 on every push to main and dev.

---

## Health Monitoring

### Module Health Sensors

6 binary sensors, one per module:

```
binary_sensor.secure_me_camera_health
binary_sensor.secure_me_lock_health
binary_sensor.secure_me_lights_health
binary_sensor.secure_me_climate_health
binary_sensor.secure_me_siren_health
binary_sensor.secure_me_tts_health
```

States:
- ON: module healthy, all entities available
- OFF: entity unavailable or configuration issue
- UNKNOWN: module disabled or not configured

### System Health Integration

10 metrics available via Developer Tools -> Info -> System Health:
- Integration version and state
- Modules enabled count and healthy count
- Zones configured
- Batteries monitored
- Last test result and timestamp

### Real-Time Updates

- Health events fired on state change, throttled to max 1x/5s (v0.6.0)
- Event-driven panel updates (no polling)
- Manual refresh available in Testing tab

### Dashboard Integration

```yaml
type: entities
title: Secure Me Health
entities:
  - binary_sensor.secure_me_camera_health
  - binary_sensor.secure_me_lock_health
  - binary_sensor.secure_me_lights_health
  - binary_sensor.secure_me_climate_health
  - binary_sensor.secure_me_siren_health
  - binary_sensor.secure_me_tts_health
```

---

## Battery Tracking

### Auto-Discovery

- Scans all entities with device_class: battery automatically
- Creates 3 tracking entities per discovered battery
- No manual configuration required
- Updates periodically and on demand during Full Test

### Battery Thresholds

| Level | Range | Action |
|-------|-------|--------|
| OK | 30-100% | None |
| Low | 20-29% | Plan replacement |
| Critical | 10-19% | Replace soon |
| Urgent | 0-9% | Replace now |

Battery status is **informational only** and does NOT affect test PASS/FAIL determination.

### Dashboard Integration

```yaml
type: entities
title: Battery Status
entities:
  - sensor.secure_me_front_door_battery
  - sensor.secure_me_window_sensor_1_battery
  - sensor.secure_me_motion_detector_battery
state_color: true
```

---

## Configuration Dashboard

### Panel Overview

8 tabs in the Secure Me sidebar panel (~4900 lines, emoji-free):

1. Sensors -- sensor overview, Fake Presence toggle, environmental always-on section
2. Zones -- zone configuration and management
3. Users -- PIN code, NFC, and person tracker binding
4. Modules -- smart module settings with live health badges
5. Actions -- automation trigger templates
6. Test -- health monitoring and test execution
7. Future -- Home Alone Monitor camera configuration
8. Settings -- system configuration

### Module Configuration

Each module card shows:
- Enable/disable toggle
- Live health badge (OK/Warning/Error/Degraded)
- Configured entity count
- Entity list with availability status
- Quick test button

### WebSocket Real-Time Features

- Live alarm state and countdown updates
- Configuration changes applied immediately
- Test execution with real-time progress
- Health push events (no polling)
- Battery status on demand

---

## Automation and Events

### Event Types

```
secure_me_armed          -- alarm activated (data: mode, armed_by)
secure_me_disarmed       -- alarm deactivated (data: disarmed_by)
secure_me_triggered      -- alarm triggered (data: triggered_by)
secure_me_health_updated -- module health changed (throttled 1x/5s)
```

### Example Automations

**Notify on alarm trigger:**
```yaml
automation:
  - alias: "Alarm Triggered Alert"
    trigger:
      - platform: event
        event_type: secure_me_triggered
    action:
      - service: notify.mobile_app
        data:
          title: "ALARM TRIGGERED"
          message: "Triggered by: {{ trigger.event.data.triggered_by }}"
```

**Low battery alert:**
```yaml
automation:
  - alias: "Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.secure_me_front_door_battery
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "Low Battery"
          message: "{{ trigger.to_state.name }}: {{ trigger.to_state.state }}%"
```

**Module health issue:**
```yaml
automation:
  - alias: "Module Degraded Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.secure_me_camera_health
        to: "off"
    action:
      - service: notify.mobile_app
        data:
          title: "Secure Me Module Issue"
          message: "{{ trigger.to_state.name }} needs attention"
```

**Daily health report:**
```yaml
automation:
  - alias: "Daily Health Report"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Secure Me Daily Report"
          message: >
            Modules: {{ states.binary_sensor
              | selectattr('entity_id', 'search', 'secure_me.*_health')
              | selectattr('state', 'eq', 'on') | list | count }}/6 healthy.
            Batteries low: {{ states.sensor
              | selectattr('entity_id', 'search', 'secure_me.*_battery')
              | selectattr('state', 'lt', '20') | list | count }}
```

---

## Advanced Features

### Diagnostics

Enhanced diagnostics with 6 sections, downloadable from Devices and Services:
- Integration version and alarm state
- Module health summary (enabled, healthy, degraded count)
- Battery overview (monitored count, low count)
- Configuration validation results
- Performance metrics
- Test results (last run timestamp and result)

Sensitive data (codes, PINs, NFC tags) is automatically redacted.

### State Backup/Restore

- Alarm state persists across HA restarts
- Module configurations stored in HA .storage
- Test results (last 10) persisted across restarts
- Light state backed up before arm, restored on disarm

### UTF-8 and Encoding Standards

All code files (.js and .py) are guaranteed emoji-free.
Emojis corrupt to garbled characters when processed by automation tools.
Validated by dedicated script and CI on every commit.

---

## Statistics (v0.9.0)

**Code:**

| Component | Lines |
|-----------|-------|
| Frontend panel (secure-me-panel.js) | ~4400 |
| Total Python source files | 22+ |
| Unit tests | 168 |
| WebSocket API | ~800 |
| Retry-protected service calls | 20 |

**Feature Completion:**

| Area | Status |
|------|--------|
| Core alarm | 100% |
| Zone management | 100% |
| Smart modules (6) | 100% |
| Error handling and retry | 100% |
| Edge case handling | 100% |
| Performance optimization | 100% |
| UX improvements | 100% |
| Testing framework | 100% |
| Health monitoring | 100% |
| Battery tracking | 100% |
| Documentation | 100% |
| Unit test suite | 168 / 168 passing |

**Platform Support:**
- Alarm Control Panel: yes
- Binary Sensors (health): yes
- Sensors (battery): yes
- Switches: yes
- Selects: yes

---

## Use Cases

**Home Security**
- Complete perimeter and interior protection
- Multi-zone monitoring with per-mode activation
- Smart automation integration
- Real-time health monitoring and degradation alerts

**Vacation Mode**
- Armed Vacation mode with extended-absence rules
- Energy optimization via Climate module
- Camera recording and smart POE management
- Remote monitoring via HA mobile app

**Family Home**
- Multiple user codes
- Kid-safe interior zones (away-only activation)
- Pet-friendly sensor configuration
- Daily health report automation

**Smart Home Integration**
- Works with all existing HA devices and automations
- No external cloud dependencies
- Full WebSocket API for custom integrations
- HACS-installable

---

**Version:** 1.1.0
**Status:** Production Release
**Last Updated:** 2026-03-16
