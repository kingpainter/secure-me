# 🎯 Secure Me - Features

Complete feature documentation for the Secure Me Home Assistant alarm system integration.

**Version:** 0.3.0 (Phase 3 Complete - Testing & Monitoring)  
**Last Updated:** 2026-02-13

---

## 📑 Table of Contents

1. [Core Alarm System](#core-alarm-system)
2. [Zone Management](#zone-management)
3. [Smart Modules](#smart-modules)
4. [Testing Framework](#testing-framework) ✨ **NEW in v0.3.0**
5. [Health Monitoring](#health-monitoring) ✨ **NEW in v0.3.0**
6. [Battery Tracking](#battery-tracking) ✨ **NEW in v0.3.0**
7. [Configuration Dashboard](#configuration-dashboard)
8. [Automation & Events](#automation--events)
9. [Advanced Features](#advanced-features)

---

## 🆕 What's New in v0.3.0

### 🧪 Testing Framework
- **Three-tier test system** (Quick, Standard, Full)
- **Real-time test execution** in configuration panel
- **Health scoring** with PASS/FAIL/UNKNOWN states
- **Test result persistence** across sessions
- **Detailed error reporting** with actionable messages

### 🏥 Health Monitoring
- **Module health binary sensors** (6 sensors)
- **Entity availability checking** in real-time
- **Configuration validation** for all modules
- **Visual health indicators** in dashboard
- **Auto-refresh** health status

### 🔋 Battery Tracking
- **Auto-discovery** of all battery entities
- **Battery level sensors** for monitoring
- **Low battery warnings** (< 20%)
- **Dashboard integration** ready
- **Informational tracking** (doesn't affect tests)

---

## 🔐 Core Alarm System

### Arming Modes

**5 Distinct Modes** for different scenarios:

| Mode | Use Case | Typical Sensors |
|------|----------|-----------------|
| 🏠 **Armed Home** | Evening, family home | Perimeter only (doors/windows) |
| 🌙 **Armed Night** | Sleeping | Downstairs + perimeter |
| ✈️ **Armed Away** | Vacation, work | All sensors active |
| 🎯 **Armed Vacation** | Extended absence | All sensors + special rules |
| ✅ **Disarmed** | Daily living | All sensors inactive |

### State Machine

**8 Intelligent States:**

```
┌─────────────┐
│  DISARMED   │ ←──────────────┐
└──────┬──────┘                │
       │ ARM command           │
       ↓                       │
┌─────────────┐                │
│   ARMING    │ (Exit delay)   │
└──────┬──────┘                │
       │ Countdown ends        │
       ↓                       │
┌─────────────┐                │
│  ARMED_*    │                │
└──────┬──────┘                │
       │ Sensor triggered      │
       ↓                       │
┌─────────────┐                │
│   PENDING   │ (Entry delay)  │
└──────┬──────┘                │
       │ Timeout or code       │
       ├───────────────────────┘
       │ No code              
       ↓                      
┌─────────────┐               
│  TRIGGERED  │ 🚨            
└─────────────┘               
```

### Entry/Exit Delays

**Smart Countdown System:**
- **Exit Delay**: Time to leave after arming (default 30s)
- **Entry Delay**: Time to disarm after trigger (default 30s)
- **Visual Countdown**: Real-time display in UI
- **Audio Feedback**: TTS announcements (optional)
- **Adjustable**: Configure per zone/sensor

### Code Protection

**PIN Security:**
- 4-6 digit codes
- Multiple user codes
- Retry limit (3 attempts)
- Lockout period after failures
- NFC tag alternative (planned)
- Code history logging

---

## 🗺️ Zone Management

### Multi-Zone Architecture

**Zone-Based Control:**
Create independent security zones for different areas:

```
Home Layout Example:
┌─────────────────────────────┐
│  Zone: Living Room          │
│  Sensors: 3 motion, 2 doors │
│  Armed: home, night, away   │
└─────────────────────────────┘
┌─────────────────────────────┐
│  Zone: Bedrooms             │
│  Sensors: 2 motion, 4 windows│
│  Armed: away only           │
└─────────────────────────────┘
```

**Zone Features:**
- **Independent monitoring** per zone
- **Flexible sensor grouping**
- **Conditional arming** based on mode
- **Zone bypass** for temporary disabling
- **Trigger callbacks** for automation
- **Zone health monitoring** ✨ NEW

### Sensor Types

**3 Main Categories:**

| Type | Examples | Behavior |
|------|----------|----------|
| 🚶 **Motion** | PIR, mmWave, presence | Instant trigger |
| 🚪 **Contact** | Door/window sensors | Entry delay |
| 📍 **Presence** | Location, occupancy | Context aware |

### Open Sensor Detection

**Smart Pre-Arming Checks:**
- Detects open doors/windows before arming
- Visual warning in UI
- Optional blocking (prevents arming)
- Override capability for special cases
- Real-time status updates

---

## 🤖 Smart Modules

### Module System Overview

**6 Intelligent Modules** that integrate with your alarm:

| Module | Purpose | Key Features |
|--------|---------|--------------|
| 📷 **Camera** | Visual verification | POE control, recording |
| 🔒 **Lock** | Access control | Auto lock, retry logic |
| 💡 **Lights** | Presence simulation | Auto control, flash alerts |
| 🌡️ **Climate** | Energy saving | Temperature presets |
| 🚨 **Siren** | Alert system | Multiple patterns, volume |
| 🔊 **TTS** | Voice feedback | Danish support, templates |

### 📷 Camera Module

**Smart Camera Management:**

**POE Port Control:**
- Powers cameras on/off via network switch
- Smart delay (skips if already on)
- Saves ~120 seconds on startup
- Supports multiple switches (Vision, UniFi, etc.)

**Recording Modes:**
- **Armed:** Continuous recording
- **Disarmed:** Motion-only recording
- **Off:** No recording
- **Smart:** Based on presence

**Features:**
```yaml
enabled: true
poe_ports:
  - switch.vision_port_1_poe
  - switch.vision_port_5_poe
cameras:
  - camera.front_door
  - camera.back_yard
  - camera.garage
recording_mode: input_select.camera_recording
```

**Actions:**
- **On Arm:** Enable POE + set continuous recording
- **On Disarm:** Set motion recording
- **On Trigger:** Ensure continuous recording

**Health Monitoring:** ✨ NEW
- Entity availability checks
- POE switch status
- Camera feed verification
- Configuration validation

---

### 🔒 Lock Module

**Smart Lock Automation:**

**Features:**
- Auto-lock on arming
- Auto-unlock on disarming (optional)
- Retry logic (3 attempts with 5s delay)
- Always-locked safety (ensures final locked state)
- Multiple lock support

**Configuration:**
```yaml
enabled: true
locks:
  - lock.front_door
  - lock.back_door
lock_on_arm: true
unlock_on_disarm: false
retry_attempts: 3
retry_delay: 5
```

**Smart Behaviors:**
- **On Arm:** Lock all doors, retry on failure
- **On Disarm:** Optional unlock, user configurable
- **On Trigger:** Ensure all locks engaged

**Safety Features:**
- Final state verification
- Retry on communication failure
- Status logging
- Manual override capability

**Health Monitoring:** ✨ NEW
- Lock entity availability
- Response time tracking
- Battery status (if applicable)
- Configuration validation

---

### 💡 Lights Module

**Intelligent Lighting Control:**

**Features:**
- Auto-control based on alarm state
- Emergency flash patterns on trigger
- Zone-based activation
- Brightness management
- Presence simulation

**Flash Patterns:**
- **Rapid:** 0.5s on, 0.5s off (attention grabbing)
- **Slow:** 2s on, 2s off (subtle warning)
- **Intermittent:** 5s on, 2s off (periodic alert)

**Configuration:**
```yaml
enabled: true
lights:
  - light.living_room
  - light.kitchen
  - light.bedroom
arm_action: turn_off
disarm_action: turn_on
flash_on_trigger: true
flash_pattern: rapid
flash_duration: 300
```

**Actions:**
- **On Arm:** Turn off or leave as-is
- **On Disarm:** Turn on or restore previous state
- **On Trigger:** Flash pattern for duration

**Health Monitoring:** ✨ NEW
- Light entity availability
- Response time checks
- Brightness level validation
- Group sync verification

---

### 🌡️ Climate Module

**Smart Temperature Management:**

**Features:**
- Multi-zone support
- Temperature presets
- Energy optimization
- Mode management
- Schedule integration

**Modes:**
- **Armed (Away):** Eco temperature (16-18°C)
- **Armed (Home/Night):** Comfort temperature (20-22°C)
- **Disarmed:** Normal operation
- **Triggered:** Emergency mode (optional)

**Configuration:**
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

**Actions:**
- **On Arm:** Set eco mode, reduce temperature
- **On Disarm:** Set comfort mode, restore temperature
- **On Trigger:** Optional freeze protection

**Health Monitoring:** ✨ NEW
- Thermostat entity availability
- Temperature sensor status
- HVAC connection verification
- Mode transition validation

---

### 🚨 Siren Module

**Professional Alert System:**

**Features:**
- Multiple sound patterns
- Volume control (0-100%)
- Duration settings (10-600s)
- Multiple siren support
- Emergency override

**Patterns:**
- **Continuous:** Solid alarm sound
- **Intermittent:** Alternating on/off
- **Rapid:** Fast pulsing alarm

**Configuration:**
```yaml
enabled: true
sirens:
  - siren.alarm_main
  - siren.alarm_basement
pattern: intermittent
duration: 300
volume: 80
```

**Actions:**
- **On Trigger:** Sound alarm with pattern
- **On Disarm:** Stop all sirens
- **Emergency:** Manual activation available

**Health Monitoring:** ✨ NEW
- Siren entity availability
- Volume level checks
- Pattern support verification
- Battery status (if applicable)

---

### 🔊 TTS Module

**Voice Notification System:**

**Features:**
- Danish language support (Google TTS)
- Message templates
- Priority handling
- Multi-speaker support
- Volume control

**Message Templates:**
- **Armed:** "Alarmen er aktiveret i {mode} tilstand"
- **Disarmed:** "Alarmen er deaktiveret"
- **Triggered:** "ALARM! Zone {zone} er udløst!"
- **Custom:** User-defined messages

**Configuration:**
```yaml
enabled: true
media_players:
  - media_player.living_room_speaker
  - media_player.bedroom_speaker
language: da
volume: 0.7
message_templates:
  armed: "Alarm activated in {mode} mode"
  disarmed: "Alarm deactivated"
  triggered: "ALARM! Zone {zone} triggered!"
```

**Actions:**
- **On Arm:** Announce arming with mode
- **On Disarm:** Confirm disarming
- **On Trigger:** Alert with zone information
- **Countdown:** Entry/exit delay announcements

**Health Monitoring:** ✨ NEW
- Media player availability
- TTS service status
- Volume level validation
- Network connectivity check

---

## 🧪 Testing Framework ✨ NEW in v0.3.0

### Test Levels

**Three-Tier System:**

#### Quick Test (~30 seconds)
**Purpose:** Rapid configuration validation

**Tests:**
- Module configuration structure
- Required fields present
- Entity ID format validation
- Basic syntax checks

**Best For:**
- After configuration changes
- Quick health check
- Pre-deployment validation

#### Standard Test (~60 seconds)
**Purpose:** Comprehensive entity validation

**Tests:**
- All Quick Test checks
- Entity availability verification
- Module health status
- Configuration consistency
- Entity response times

**Best For:**
- Regular health monitoring
- Post-installation verification
- Troubleshooting issues

#### Full Test (~90 seconds)
**Purpose:** Complete functionality verification

**Tests:**
- All Standard Test checks
- Battery status scan
- Integration health
- WebSocket connectivity
- End-to-end functionality
- Performance metrics

**Best For:**
- Complete system validation
- Pre-production testing
- Comprehensive diagnostics

### Test Execution

**Via Configuration Panel:**
1. Open Secure Me panel
2. Navigate to Testing tab
3. Select test level
4. Click "Run Test"
5. Monitor real-time progress
6. Review detailed results

**Via Command Line:**
```bash
# Run all tests
pytest custom_components/secure_me/tests/ -v

# Run specific module tests
pytest custom_components/secure_me/tests/test_modules.py -v

# Run with coverage
pytest --cov=custom_components/secure_me
```

### Test Results

**Health Scoring:**
- ✅ **PASS:** All critical tests passed
- ⚠️ **WARNING:** Non-critical issues found
- ❌ **FAIL:** Critical tests failed
- ❓ **UNKNOWN:** Tests not run or incomplete

**Result Details:**
- Module-by-module breakdown
- Entity availability status
- Configuration validation results
- Error messages with solutions
- Test timestamp and duration
- Historical comparison

### Test Result Persistence

**Stored Information:**
- Last test timestamp
- Test level executed
- Overall result (PASS/FAIL/UNKNOWN)
- Module-specific results
- Battery status snapshot
- Error details

**Access History:**
- View in Testing tab
- Export to JSON/CSV (planned)
- Compare between runs
- Trend analysis (planned)

---

## 🏥 Health Monitoring ✨ NEW in v0.3.0

### Module Health Sensors

**6 Binary Sensors Created:**

```yaml
binary_sensor.secure_me_camera_health    # Camera module
binary_sensor.secure_me_lock_health      # Lock module
binary_sensor.secure_me_lights_health    # Lights module
binary_sensor.secure_me_climate_health   # Climate module
binary_sensor.secure_me_siren_health     # Siren module
binary_sensor.secure_me_tts_health       # TTS module
```

**Sensor States:**
- **ON (Healthy):** All entities available, configuration valid
- **OFF (Unhealthy):** Entity unavailable or configuration issue
- **UNKNOWN:** Module disabled or not configured

### Health Checks Performed

**Entity Availability:**
- Checks if all configured entities exist
- Verifies entities are responsive
- Tests entity state accessibility
- Monitors response times

**Configuration Validation:**
- Required fields present
- Valid entity IDs
- Proper data types
- Logical consistency

**Module Status:**
- Module enabled/disabled state
- Last successful operation
- Error count tracking
- Performance metrics

### Real-Time Updates

**Auto-Refresh:**
- Health status updates every 30 seconds
- Manual refresh available
- On-demand health checks
- Event-driven updates

**Visual Indicators:**
- ✅ Green badge: Healthy
- ⚠️ Yellow badge: Warning
- ❌ Red badge: Unhealthy
- 📊 Health percentage score

### Dashboard Integration

**Example Lovelace Card:**
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

**Automation Example:**
```yaml
automation:
  - alias: "Alert on Module Health Issue"
    trigger:
      - platform: state
        entity_id:
          - binary_sensor.secure_me_camera_health
          - binary_sensor.secure_me_lock_health
        to: 'off'
    action:
      - service: notify.mobile_app
        data:
          title: "Secure Me Health Issue"
          message: "Module {{ trigger.to_state.name }} is unhealthy"
```

---

## 🔋 Battery Tracking ✨ NEW in v0.3.0

### Auto-Discovery

**Automatic Detection:**
- Scans all entities with `device_class: battery`
- Creates sensor for each discovered battery
- Updates every 5 minutes
- No manual configuration required

**Discovery Process:**
```python
# Automatically finds batteries like:
sensor.front_door_battery           # 85%
sensor.window_sensor_1_battery      # 72%
sensor.motion_detector_battery      # 45%
sensor.smoke_detector_battery       # 20% (LOW!)
```

### Battery Sensors

**Sensor Attributes:**
- **State:** Battery percentage (0-100%)
- **Device Class:** Battery
- **Unit:** %
- **Low Warning:** < 20%
- **Critical Warning:** < 10%

**Naming Convention:**
```
sensor.secure_me_{original_entity_name}_battery
```

### Battery Monitoring

**Dashboard Display:**
- Battery count indicator
- Individual battery levels
- Low battery warnings
- Last update timestamp
- Battery health trend (planned)

**Low Battery Alerts:**
```yaml
automation:
  - alias: "Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.secure_me_*_battery
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "Low Battery Warning"
          message: "{{ trigger.to_state.name }} at {{ trigger.to_state.state }}%"
```

### Battery Status in Tests

**Full Test Includes:**
- Complete battery scan
- Battery level reporting
- Low battery identification
- Battery count summary

**Important:** Battery status is **informational only** and does NOT affect test PASS/FAIL determination.

### Battery Dashboard Integration

**Example Card:**
```yaml
type: entities
title: Battery Status
entities:
  - sensor.secure_me_front_door_battery
  - sensor.secure_me_window_sensor_1_battery
  - sensor.secure_me_motion_detector_battery
  - sensor.secure_me_smoke_detector_battery
state_color: true
```

---

## 🎛️ Configuration Dashboard

### Panel Overview

**7 Main Tabs:**

1. **Sensors** - Overview and status
2. **Zones** - Zone configuration
3. **Users** - PIN code management
4. **Modules** - Smart module settings
5. **Automations** - Trigger templates
6. **Settings** - System configuration
7. **Testing** - Health monitoring ✨ NEW

### Testing Tab Features ✨ NEW

**Interface Components:**
- Test level selection (Quick/Standard/Full)
- Real-time progress indicator
- Detailed results display
- Module health summary
- Battery status overview
- Test history log
- Export results button (planned)

**User Workflow:**
1. Select test level
2. Click "Run Test"
3. Watch real-time progress
4. Review detailed results
5. Address any issues
6. Re-test to verify fixes

**Visual Design:**
- Clean, professional interface
- Color-coded results
- Expandable sections
- Mobile-responsive layout
- Clear action buttons

### Module Configuration

**Each Module Card Shows:**
- Enable/disable toggle
- Configuration status
- Health indicator ✨ NEW
- Entity count
- Last updated timestamp
- Quick actions (configure, test)

**Configuration Options:**
- Visual entity selection
- Search/filter functionality
- Form validation
- Add/remove entities
- Professional dialogs
- Mobile-responsive design

### WebSocket Integration

**Real-Time Features:**
- Live status updates
- Configuration changes
- Test execution
- Health monitoring
- Battery status
- Error notifications

---

## 🔄 Automation & Events

### Event Types

**System Events:**
- `alarm_armed` - Alarm activated
- `alarm_disarmed` - Alarm deactivated
- `alarm_triggered` - Sensor triggered alarm
- `zone_triggered` - Specific zone triggered
- `module_action` - Module executed action
- `health_changed` - Module health status changed ✨ NEW
- `battery_low` - Battery below threshold ✨ NEW

### Automation Templates

**Example Automations:**

**Low Battery Notification:**
```yaml
automation:
  - alias: "Battery Low Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.secure_me_*_battery
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "Low Battery"
          message: "{{ trigger.to_state.name }}: {{ trigger.to_state.state }}%"
```

**Module Health Alert:**
```yaml
automation:
  - alias: "Module Health Issue"
    trigger:
      - platform: state
        entity_id: binary_sensor.secure_me_*_health
        to: 'off'
    action:
      - service: notify.mobile_app
        data:
          title: "Module Unhealthy"
          message: "{{ trigger.to_state.name }} needs attention"
```

**Daily Health Report:**
```yaml
automation:
  - alias: "Daily Health Report"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Secure Me Health Report"
          message: >
            Modules: {{ states.binary_sensor | selectattr('entity_id', 'search', 'secure_me.*_health') | selectattr('state', 'eq', 'on') | list | count }}/6 healthy
            Batteries: {{ states.sensor | selectattr('entity_id', 'search', 'secure_me.*_battery') | selectattr('state', 'lt', '20') | list | count }} low
```

---

## 🚀 Advanced Features

### Performance Optimization

**POE Smart Delay:**
- Checks if ports already on
- Skips unnecessary power cycles
- Saves ~120 seconds on startup
- Reduces wear on equipment

**Parallel Execution (Planned):**
- Simultaneous module actions
- Faster state transitions
- Optimized for performance
- Configurable per module

### State Backup/Restore

**State Persistence:**
- Alarm state across restarts
- Module configurations
- Zone settings
- User preferences
- Test history ✨ NEW

**Backup Features:**
- Automatic backups
- Manual export/import
- Version history
- Recovery mode

### Diagnostics

**System Health Reporting:**
- Integration status
- Module health summary ✨ NEW
- Battery overview ✨ NEW
- Configuration validation
- Performance metrics
- Error logs
- Test results ✨ NEW

**Diagnostic Data:**
```yaml
diagnostics:
  integration_version: 0.3.0
  modules_enabled: 6
  zones_configured: 4
  users_registered: 3
  modules_healthy: 6/6
  batteries_monitored: 17
  last_test: "2026-02-13 14:30:00"
  test_result: "PASS"
```

### Future Enhancements

**Planned Features:**
- NFC tag integration
- Advanced automation templates
- Cloud backup (optional)
- Mobile app companion
- Advanced analytics
- Machine learning patterns
- Voice assistant integration
- Video verification

---

## 📊 Statistics & Metrics

### Current Implementation (v0.3.0)

**Code Statistics:**
- Total lines: ~8,000+
- Python files: 20+
- Test cases: 100
- Module health sensors: 6
- Battery sensors: Auto-discovered
- Configuration panel: 3,800 lines
- WebSocket API: 800 lines

**Feature Completion:**
- Core alarm: 100%
- Zones: 100%
- Modules: 100%
- Testing: 100% ✨ NEW
- Health monitoring: 100% ✨ NEW
- Battery tracking: 100% ✨ NEW
- Configuration panel: 100%
- Automations: 80%
- Diagnostics: 80%

**Platform Support:**
- Alarm Control Panel: ✅
- Binary Sensors: ✅ (including health)
- Sensors: ✅ (including batteries)
- Switches: ✅
- Selects: ✅

---

## 🎯 Use Cases

### Home Security
- Complete perimeter protection
- Multi-zone monitoring
- Smart automation integration
- Health monitoring ✨ NEW
- Battery management ✨ NEW

### Vacation Mode
- Extended away settings
- Energy optimization
- Presence simulation
- Remote monitoring
- Automated testing ✨ NEW

### Family Home
- Kid-safe zones
- Pet-friendly sensors
- Smart scheduling
- User management
- Health alerts ✨ NEW

### Smart Home Integration
- Works with existing devices
- Flexible automation
- Voice control ready
- Dashboard integration
- Real-time testing ✨ NEW

---

**Version:** 0.3.0  
**Status:** Production Ready with Testing  
**Last Updated:** 2026-02-13  
**Next Release:** v1.0.0 (Final Polish & HACS)
