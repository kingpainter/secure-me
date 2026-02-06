# 🎯 Secure Me - Features

Complete feature documentation for the Secure Me Home Assistant alarm system integration.

**Version:** 0.2.0 (Phase 2 Complete)  
**Last Updated:** 2026-02-06

---

## 📑 Table of Contents

1. [Core Alarm System](#core-alarm-system)
2. [Zone Management](#zone-management)
3. [Smart Modules](#smart-modules)
4. [Configuration Dashboard](#configuration-dashboard)
5. [Automation & Events](#automation--events)
6. [Advanced Features](#advanced-features)

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
- NFC tag alternative
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
│  Zone: Kitchen              │
│  Sensors: 1 motion, 1 window│
│  Armed: away only           │
└─────────────────────────────┘
┌─────────────────────────────┐
│  Zone: Bedrooms             │
│  Sensors: 2 motion, 3 windows│
│  Armed: away, vacation      │
└─────────────────────────────┘
```

### Zone Features

**Per-Zone Configuration:**
- ✅ Custom sensor assignments
- ✅ Arming mode selection
- ✅ Entry/exit delays override
- ✅ Module behavior rules
- ✅ Priority levels
- ✅ Status indicators

**Zone States:**
- **Ready** - All sensors cleared
- **Not Ready** - Open sensors
- **Bypassed** - Temporarily disabled
- **Triggered** - Alarm active

---

## 🔌 Smart Modules

### 📷 Camera Module

**Purpose:** Intelligent POE and recording management

**Features:**
- **POE Control**: Auto power on/off for POE cameras
- **Smart Timing**: Checks if already powered (saves 120s!)
- **Recording Modes**: Auto switch between 24/7 and event-only
- **Parallel Execution**: All cameras powered simultaneously
- **Status Monitoring**: Real-time camera health

**Configuration:**
```json
{
  "camera": {
    "enabled": true,
    "poe_switches": [
      "switch.poe_port_1",
      "switch.poe_port_2"
    ],
    "cameras": [
      "camera.front_door",
      "camera.back_door"
    ],
    "recording_entities": [
      "select.front_door_recording",
      "select.back_door_recording"
    ],
    "poe_delay": 120,
    "auto_record": true
  }
}
```

**When Armed:**
1. Check if POE already on → Skip delay if yes
2. Turn on POE switches → Wait 120s for boot
3. Switch recording to 24/7 mode
4. Verify camera availability

**When Disarmed:**
1. Switch recording to event-only mode
2. Keep POE on (optional setting)

---

### 🔒 Lock Module

**Purpose:** Smart lock control with retry logic

**Features:**
- **Auto Lock**: Lock doors when arming
- **Auto Unlock**: Optional unlock when disarming
- **Retry Logic**: 3 attempts with 5s delay
- **Door Sensors**: Integration with door contacts
- **Status Verification**: Confirm lock state
- **Failed Lock Alerts**: Notifications on failures

**Configuration:**
```json
{
  "lock": {
    "enabled": true,
    "locks": [
      "lock.front_door",
      "lock.back_door"
    ],
    "door_sensors": {
      "lock.front_door": "binary_sensor.front_door",
      "lock.back_door": "binary_sensor.back_door"
    },
    "max_retries": 3,
    "retry_delay": 5,
    "lock_on_arm": true,
    "unlock_on_disarm": false
  }
}
```

**Smart Behavior:**
- Won't lock if door is open (sensor check)
- Retries if lock command fails
- Logs lock/unlock events
- Alerts on failures

---

### 💡 Lights Module

**Purpose:** Automated lighting control

**Features:**
- **Auto On**: Lights on when armed (night mode)
- **Auto Off**: Lights off when disarmed
- **Emergency Blink**: Flashing lights when triggered
- **Scene Support**: Restore previous states
- **Brightness Control**: Adjustable levels per mode
- **Color Support**: RGB lights change color by state

**Configuration:**
```json
{
  "lights": {
    "enabled": true,
    "lights": [
      "light.living_room",
      "light.kitchen",
      "light.hallway"
    ],
    "emergency_lights": [
      "light.outdoor_front",
      "light.outdoor_back"
    ],
    "auto_on_arm": true,
    "brightness": 80,
    "blink_on_trigger": true
  }
}
```

**Emergency Blink Pattern:**
```
ON (500ms) → OFF (500ms) → repeat
Color: RED for triggered state
```

---

### 🌡️ Climate Module

**Purpose:** Multi-zone heating/cooling management

**Features:**
- **Multi-Zone**: Control multiple climate entities
- **Auto Eco Mode**: Lower temp when armed away
- **Smart Resume**: Restore temps when disarmed
- **Vacation Mode**: Extended away settings
- **Zone Schedules**: Different rules per zone
- **Energy Savings**: Track energy saved

**Configuration:**
```json
{
  "climate": {
    "enabled": true,
    "climate_entities": [
      "climate.living_room",
      "climate.bedroom_1",
      "climate.bedroom_2"
    ],
    "away_temperature": 15,
    "home_temperature": 21,
    "auto_eco": true,
    "restore_on_disarm": true
  }
}
```

**Temperature Profiles:**
- **Armed Home**: Normal temps (21°C)
- **Armed Night**: Slightly lower (19°C)
- **Armed Away**: Eco mode (15°C)
- **Armed Vacation**: Minimum safe (10°C)

---

### 🚨 Siren Module

**Purpose:** Alarm sound management

**Features:**
- **Multiple Patterns**: Continuous, pulsing, intermittent
- **Volume Control**: Adjustable loudness (0-100%)
- **Duration Limit**: Auto stop after X minutes
- **Schedule Support**: Quiet hours (night mode)
- **Multiple Sirens**: Indoor + outdoor
- **Test Mode**: Safe testing without alarm

**Configuration:**
```json
{
  "siren": {
    "enabled": true,
    "sirens": [
      "siren.indoor",
      "siren.outdoor"
    ],
    "volume": 80,
    "pattern": "pulsing",
    "max_duration": 300,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00"
  }
}
```

**Sound Patterns:**
- **Continuous**: Solid alarm tone
- **Pulsing**: ON 1s → OFF 0.5s
- **Intermittent**: ON 0.5s → OFF 1s
- **Emergency**: Fastest pulsing

---

### 🔊 TTS Module

**Purpose:** Danish voice announcements

**Features:**
- **Countdown Announcements**: Exit/entry delays
- **Status Updates**: Armed/disarmed confirmations
- **Zone Alerts**: Which zone triggered
- **Multi-Room**: Announce to multiple speakers
- **Volume Control**: Adjustable per speaker
- **Danish Language**: Google TTS (da-DK)

**Configuration:**
```json
{
  "tts": {
    "enabled": true,
    "tts_service": "tts.google_translate_say",
    "media_players": [
      "media_player.living_room",
      "media_player.kitchen"
    ],
    "volume": 0.7,
    "language": "da",
    "announce_countdown": true
  }
}
```

**Voice Messages:**
- "Alarmanlæg aktiveres om 30 sekunder"
- "Alarmanlæg aktiveret - Armed Away"
- "Adgangsperiode - 30 sekunder til alarm"
- "Alarm udløst i Stuen!"

---

## 🎨 Configuration Dashboard

### Modern UI Interface

**7 Tabs** for complete control:

#### 1️⃣ Sensorer (Sensors)
- View all security sensors
- Add/remove sensors
- Configure trigger delays
- Test sensor status
- Battery monitoring

#### 2️⃣ Zoner (Zones)
- Create/edit zones
- Assign sensors to zones
- Configure zone modes
- Set zone priorities
- Visual zone status

#### 3️⃣ Brugere (Users)
- Manage user accounts
- Assign PIN codes
- Link NFC tags
- Set permissions
- Access logs

#### 4️⃣ Moduler (Modules)
- Enable/disable modules
- Configure module settings
- View module status
- Test module functions
- Health monitoring

#### 5️⃣ Handlinger (Automations)
- Create custom automations
- Configure notifications
- Set up webhooks
- Event triggers
- Action sequences

#### 6️⃣ Test (Testing)
- System health check
- Module testing
- Sensor testing
- Zone testing
- Simulation mode

#### 7️⃣ Fremtid (Advanced)
- System diagnostics
- Performance metrics
- Battery tracking
- Energy monitoring
- Debug logs

### WebSocket API

**Real-Time Communication:**
- Bidirectional messaging
- Instant status updates
- Live sensor states
- Module health monitoring
- Configuration sync

**API Commands:**
```javascript
// Get config
ws.send({ type: "get_config" })

// Update zone
ws.send({ type: "update_zone", data: {...} })

// Test module
ws.send({ type: "test_module", module: "camera" })
```

---

## 🤖 Automation & Events

### Custom Events

**Event-Driven Architecture:**

```yaml
# Alarm state changed
event_type: secure_me_state_changed
event_data:
  old_state: "disarmed"
  new_state: "armed_away"
  zone: "living_room"
  timestamp: "2026-02-06T10:30:00"

# Sensor triggered
event_type: secure_me_sensor_triggered
event_data:
  sensor: "binary_sensor.motion_living_room"
  zone: "living_room"
  alarm_state: "armed_away"

# Module action
event_type: secure_me_module_action
event_data:
  module: "camera"
  action: "poe_on"
  status: "success"
```

### Automation Examples

**Example 1: Send notification on trigger**
```yaml
automation:
  - alias: "Alarm Triggered Notification"
    trigger:
      - platform: event
        event_type: secure_me_state_changed
        event_data:
          new_state: "triggered"
    action:
      - service: notify.mobile_app
        data:
          message: "🚨 ALARM! {{ trigger.event.data.zone }}"
```

**Example 2: Auto lights on evening arm**
```yaml
automation:
  - alias: "Evening Arm Lights"
    trigger:
      - platform: event
        event_type: secure_me_state_changed
        event_data:
          new_state: "armed_night"
    condition:
      - condition: sun
        after: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.outdoor_lights
```

---

## 🚀 Advanced Features

### NFC Tag Integration

**Tap to Arm/Disarm:**
- Tag-based authentication
- No code needed
- Multiple tags per user
- Tag management in dashboard
- Usage history

**Setup:**
1. Scan NFC tag with phone
2. Note tag ID
3. Add to user in dashboard
4. Configure actions (arm/disarm/toggle)

### Parallel Execution

**Optimized Performance:**
- All modules execute simultaneously
- No sequential waiting
- Faster arm/disarm times
- Typical savings: 120+ seconds

**Before (Sequential):**
```
Camera POE: 120s
Lock: 5s
Lights: 2s
Climate: 3s
Total: 130s
```

**After (Parallel):**
```
All modules: 120s (max duration)
Total: 120s ✅ (10s saved)
```

### POE Optimization

**Smart Camera Startup:**
```python
if poe_switch.state == "on":
    print("POE already on - skip 120s wait!")
    proceed_immediately()
else:
    turn_on_poe()
    wait(120)
```

**Typical Usage:**
- First arm: 120s wait
- Subsequent arms: 0s wait (if not powered off)
- **Saves:** 120s per arm cycle

### Battery Tracking

**Monitor 17+ Wireless Sensors:**
- Real-time battery levels
- Low battery alerts
- Replacement reminders
- Battery history graphs
- Estimated lifespan

**Tracked Devices:**
- Motion sensors
- Door/window contacts
- NFC tags
- Remote controls
- Smoke detectors

---

## 📊 System Health

### Health Monitoring

**Real-Time Diagnostics:**
- Module status (online/offline)
- Sensor connectivity
- Battery levels
- API response times
- Error rates
- Memory usage

### Performance Metrics

**Tracked Metrics:**
- Arm/disarm response time
- Module initialization time
- WebSocket latency
- API call success rate
- Event processing speed

**Dashboard Display:**
```
✅ All modules healthy
📶 WebSocket: 12ms latency
🔋 3 sensors below 20% battery
⏱️ Avg arm time: 2.3s
```

---

## 🔒 Security Features

### Code Protection
- Hashed PIN storage
- Retry limits (3 attempts)
- Lockout periods
- Failed attempt logging
- Two-factor option (NFC)

### Audit Logging
- All arm/disarm events
- User identification
- Timestamp records
- Action history
- Export capability

### Fail-Safe Design
- Graceful degradation
- Module independence
- Backup trigger methods
- Network loss handling
- Power failure recovery

---

## 🌍 Localization

**Supported Languages:**
- 🇬🇧 English (en)
- 🇩🇰 Danish (da)

**Translated Elements:**
- UI text
- Voice announcements (TTS)
- Notifications
- Error messages
- Documentation

---

## 🎯 Feature Comparison

### vs. Alarmo

| Feature | Secure Me | Alarmo |
|---------|-----------|--------|
| Multi-zone | ✅ Yes | ❌ No |
| Modules | ✅ 6 modules | ⚠️ Limited |
| Dashboard | ✅ Full UI | ⚠️ Basic |
| NFC Support | ✅ Yes | ❌ No |
| Parallel Exec | ✅ Yes | ❌ No |
| POE Optim | ✅ Yes | ❌ No |
| Climate Control | ✅ Yes | ❌ No |
| TTS Danish | ✅ Yes | ⚠️ EN only |

### vs. Manual Alarm

| Feature | Secure Me | Manual |
|---------|-----------|--------|
| Setup Time | ⏱️ 15 min | ⏱️ Hours |
| Maintenance | ✅ Easy | ⚠️ Complex |
| Updates | ✅ Auto | ❌ Manual |
| Testing | ✅ Built-in | ❌ DIY |
| Support | ✅ Community | ❌ None |

---

## 📈 Planned Features (Roadmap)

### Phase 3 (v0.3.0)
- [ ] Complete testing framework UI
- [ ] Health monitoring dashboard
- [ ] Battery tracking visualization
- [ ] Advanced automation builder
- [ ] Options flow UI

### Phase 4 (v1.0.0)
- [ ] Mobile app integration
- [ ] Cloud backup/restore
- [ ] Multi-home support
- [ ] AI anomaly detection
- [ ] Advanced analytics

---

**Documentation Version:** 0.2.0  
**Last Updated:** 2026-02-06  
**Status:** Phase 2 Complete ✅
