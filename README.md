# Secure Me — Professional Home Alarm Manager

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2025.1.1%2B-blue)](https://www.home-assistant.io/)
[![Version](https://img.shields.io/badge/version-1.5.0-green)](https://github.com/kingpainter/secure-me/releases)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

A comprehensive alarm system integration for Home Assistant with multi-zone support, 6 smart modules, an interactive floorplan, real-time health monitoring, and a modern configuration panel.

---

## Features

**Core Alarm System**
- Five arming modes: Away, Home, Night, Vacation, Home Alone
- Configurable exit delay (arming countdown) and entry delay (entry countdown)
- Auto-reset after trigger time — no permanent alarm state
- bcrypt PIN hashing — user codes never stored in plaintext
- State tracking: who armed, who disarmed, what triggered
- State restore on HA restart — alarm stays armed, zone monitoring resumes immediately

**Zone Management**
- Multiple zone types: Entry, Instant, Interior, Perimeter
- Each zone can contain multiple binary sensors
- Per-sensor overrides: individual entry delay, auto-bypass per arm mode, arm-on-close
- Allow Open flag: permanently bypass a sensor at all arm times (e.g. always-open window)
- Sensor groups (anti-masking): require N sensors to activate within a time window
- Sensor debouncing — prevents false alarms from flapping sensors
- Graceful handling of unavailable/missing sensors

**6 Smart Modules**
| Module | Function |
|--------|----------|
| Camera | POE port control, recording mode management |
| Lock | Smart lock automation with retry logic |
| Lights | Auto control, emergency flash patterns, steady white mode |
| Climate | Multi-zone heating/cooling management |
| Siren | Alarm sounds with multiple patterns |
| TTS | Voice notifications — supports cloud_say, google_say, piper, custom services, Alexa via script |

**Floorplan (v1.5.0)**
- Upload a PNG floor plan (up to 4 MB)
- Draw rooms as rectangles or polygons directly on the map
- Assign sensors to rooms — lights up when sensor activates in Home Alone mode
- Mark doors and windows by dragging a line; assign door/window sensors for live indication
- Full undo support (Ctrl+Z, up to 20 steps)
- Keyboard shortcuts: Esc, Delete, R/P/O to switch tools
- Touch support for tablets
- Configuration survives HACS updates: PNG backed up in HA storage, auto-restored on startup

**Presence-Based Auto-Arm**
- Arms automatically 15 minutes after all residents leave (locks + alarm + cameras)
- Arrival confirmation delay prevents GPS flicker from resetting timers
- Respects Fake Presence toggle
- Selective Fake Presence v2: block alarm, locks, or cameras independently

**Auto Actions (v1.5.0)**
- Three independent action timers with individual delays on alarm trigger
- Actions: arm alarm, activate cameras, send notification
- Configurable per action with delay slider
- Arrival confirmation delay prevents GPS flicker

**Monitoring**
- System health score with per-module status
- Battery auto-discovery across all HA devices
- Low/critical battery warnings
- Enhanced diagnostics download

**Testing**
- Three test levels: Quick (~30s), Standard (~60s), Full (~90s)
- Scheduled tests with configurable day, time, and type
- Test result history (last 10 runs)
- Per-module async test execution
- 2-column test dashboard: Last Run | History and Sensor Status | Battery Overview

**Configuration Panel**
- Modern sidebar UI (Alarmo-inspired)
- Mobile-responsive with bottom navigation
- Real-time WebSocket updates — no page reloads
- Toast notifications, in-panel confirm dialogs
- Environmental sensors always-on section with forced notifications
- Sensor hide/exclude for irrelevant device trackers and auto-hidden entries
- User to person tracker binding for presence automation
- Per-arm-mode auto-bypass per sensor: choose which modes a sensor bypasses in
- Mobile push actions: arm/disarm/force-arm from Companion app notification buttons
- Live arming/pending countdown in sidebar status pill
- Searchable sensor dropdowns throughout

---

## Requirements

- Home Assistant 2025.1.1 or newer
- Python 3.11 or newer

---

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to Integrations → Custom repositories
3. Add `https://github.com/kingpainter/secure-me` as type Integration
4. Search for **Secure Me** and install
5. Restart Home Assistant

### Manual

1. Download the latest release from [GitHub Releases](https://github.com/kingpainter/secure-me/releases)
2. Copy the `custom_components/secure_me/` folder to your HA config directory
3. Restart Home Assistant

### Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Secure Me**
3. Enter your alarm code and configure exit/entry delays
4. Open the **Secure Me** panel from the sidebar
5. Configure zones, modules, and sensors

---

## Configuration

### Initial Setup (Config Flow)

| Field | Description | Default |
|-------|-------------|---------|
| Alarm Code | PIN used to arm/disarm | Required |
| Exit Delay | Countdown after arming (seconds) | 30 |
| Entry Delay | Countdown after breach (seconds) | 30 |
| Trigger Time | How long alarm stays triggered (seconds) | 300 |

### Zone Types

| Type | Behavior |
|------|----------|
| Entry | Triggers entry delay countdown |
| Instant | Triggers alarm immediately, no delay |
| Interior | Triggers alarm immediately when armed away |
| Perimeter | Triggers alarm immediately in all armed modes |

### Per-Sensor Options

| Option | Description |
|--------|-------------|
| Entry Delay Override | Override the zone's entry delay for this sensor |
| Auto-Bypass Modes | Choose which arm modes bypass this sensor if open at arm time |
| Allow Open | Permanently bypass this sensor in all arm modes (e.g. always-open window) |
| Arm on Close | Automatically arm when this sensor closes (e.g. front door) |

### Module Configuration

All modules are configured via the **Modules tab** in the panel. Each module can be enabled/disabled independently. Configuration changes take effect immediately — no HA restart required.

---

## Floorplan Setup

1. Go to the **Floorplan** tab in the Secure Me panel
2. Click **Edit** and upload a PNG floor plan image
3. Use the **Rectangle** or **Polygon** tool to draw rooms
4. Click a room to name it and assign sensors
5. Use the **Door/Window** tool to mark openings — drag a line across a wall
6. Click an opening to assign a door or window sensor
7. In **Home Alone** mode the floorplan goes live: rooms glow when their sensors activate

**Keyboard shortcuts (edit mode):**
- `R` — rectangle tool
- `P` — polygon tool
- `O` — door/window tool
- `Delete` — delete selected room or opening
- `Ctrl+Z` — undo last action
- `Esc` — cancel drawing / deselect / exit edit mode

---

## Services

| Service | Description |
|---------|-------------|
| `secure_me.arm_away` | Arm in away mode (all zones active) |
| `secure_me.arm_home` | Arm in home mode (perimeter only) |
| `secure_me.arm_night` | Arm in night mode (perimeter + entry) |
| `secure_me.arm_vacation` | Arm in vacation mode (extended trigger) |
| `secure_me.arm_home_alone` | Arm in Home Alone mode (cameras live, no motion trigger) |
| `secure_me.disarm` | Disarm the alarm |
| `secure_me.trigger` | Manually trigger alarm |
| `secure_me.run_test` | Run a system test |
| `secure_me.enable_module` | Enable a specific module |
| `secure_me.disable_module` | Disable a specific module |

All arm services accept optional `code` (string), `skip_delay` (boolean), and `force` (boolean — bypass open sensor check) parameters.

---

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `alarm_control_panel.secure_me` | Alarm Control Panel | Main alarm entity |
| `binary_sensor.secure_me_anyone_home` | Binary Sensor | True when any tracked person is home |
| `sensor.secure_me_lowest_battery` | Sensor | Lowest battery level across all devices |
| `sensor.secure_me_battery_count` | Sensor | Total number of tracked battery devices |
| `binary_sensor.secure_me_camera_health` | Binary Sensor | Camera module health |
| `binary_sensor.secure_me_lock_health` | Binary Sensor | Lock module health |
| `binary_sensor.secure_me_lights_health` | Binary Sensor | Lights module health |
| `binary_sensor.secure_me_climate_health` | Binary Sensor | Climate module health |
| `binary_sensor.secure_me_siren_health` | Binary Sensor | Siren module health |
| `binary_sensor.secure_me_tts_health` | Binary Sensor | TTS module health |

---

## Events

| Event | Data | Description |
|-------|------|-------------|
| `secure_me_alarm_armed` | `mode`, `armed_by` | Fired when alarm is armed |
| `secure_me_alarm_disarmed` | `disarmed_by` | Fired when alarm is disarmed |
| `secure_me_alarm_triggered` | `triggered_by` | Fired when alarm triggers |
| `secure_me_arm_failed` | `command`, `open_sensors`, `bypassed_sensors` | Fired when arming fails due to open sensors |
| `secure_me_module_error` | `module`, `action`, `error` | Fired when a module fails |

---

## Automation Examples

### Auto-arm when everyone leaves

```yaml
automation:
  alias: "Secure Me - Auto arm away"
  trigger:
    - platform: state
      entity_id: binary_sensor.secure_me_anyone_home
      to: "off"
  condition:
    - condition: state
      entity_id: alarm_control_panel.secure_me
      state: "disarmed"
  action:
    - service: secure_me.arm_away
      data:
        skip_delay: false
```

### Auto-disarm on arrival

```yaml
automation:
  alias: "Secure Me - Auto disarm on arrival"
  trigger:
    - platform: state
      entity_id: person.your_name
      to: "home"
  condition:
    - condition: state
      entity_id: alarm_control_panel.secure_me
      state:
        - "armed_away"
        - "armed_vacation"
  action:
    - service: secure_me.disarm
      data:
        code: "1234"
```

### Night mode at bedtime

```yaml
automation:
  alias: "Secure Me - Night mode"
  trigger:
    - platform: time
      at: "23:00:00"
  condition:
    - condition: state
      entity_id: alarm_control_panel.secure_me
      state: "disarmed"
  action:
    - service: secure_me.arm_night
      data:
        skip_delay: true
```

### Force arm even with open sensors

```yaml
automation:
  alias: "Secure Me - Force arm away"
  action:
    - service: secure_me.arm_away
      data:
        force: true
```

### Notify on trigger

```yaml
automation:
  alias: "Secure Me - Trigger notification"
  trigger:
    - platform: state
      entity_id: alarm_control_panel.secure_me
      to: "triggered"
  action:
    - service: notify.mobile_app
      data:
        title: "ALARM TRIGGERED"
        message: "Secure Me alarm has been triggered. Check your home."
```

---

## Troubleshooting

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.secure_me: debug
```

View logs at: **Settings → System → Logs** (filter: `secure_me`)

### Download Diagnostics

Go to **Settings → Devices & Services → Secure Me → Download Diagnostics**

### System Health

Go to **Developer Tools → Info → System Health** to see Secure Me health metrics.

### Common Issues

**Panel shows blank / not loading**
Clear browser cache and force-reload: Chrome/Edge `Ctrl+Shift+R`, Firefox `Ctrl+F5`. After any update, a full browser reload is required for the new JS to take effect.

**Floorplan lost after HACS update**
From v1.5.0 the floor plan image is backed up in HA storage and restored automatically on the next startup. Room and sensor assignments always survive HACS updates. If the image is not restored, re-upload it — your rooms and sensor assignments will still be there.

**Alarm arms but doesn't trigger**
Check that sensors are enabled in the Sensors tab and zones are configured in the Zones tab. Verify the zone's arm modes include the mode you are using. Run a Full test from the Testing tab.

**Sensor blocks arming (open at arm time)**
Either enable auto-bypass for the relevant arm mode on that sensor, or enable **Allow Open** to permanently bypass it. Both options are in the Sensors tab.

**Module shows error health badge**
Check that the module's entities are available in HA. An entity marked `unavailable` will show as an error in Secure Me.

**Exit/entry delay countdown not showing**
The countdown updates every second. If it jumps (e.g. 30 → 25), this is by design — full entity refresh happens every 5 seconds for performance.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

**Developer:** KingPainter
**Version:** 1.5.0
**Repository:** [github.com/kingpainter/secure-me](https://github.com/kingpainter/secure-me)
