# Secure Me — Professional Home Alarm Manager

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2025.1.1%2B-blue)](https://www.home-assistant.io/)
[![Version](https://img.shields.io/badge/version-1.1.0-green)](https://github.com/kingpainter/secure-me/releases)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

A comprehensive alarm system integration for Home Assistant with multi-zone support, 6 smart modules, real-time health monitoring, and a modern configuration panel.

---

## Features

**Core Alarm System**
- Four arming modes: Away, Home, Night, Vacation
- Configurable exit delay (arming countdown) and entry delay (entry countdown)
- Auto-reset after trigger time — no permanent alarm state
- Code-protected arming and disarming
- State tracking: who armed, who disarmed, what triggered

**Zone Management**
- Multiple zone types: Entry, Instant, Interior, Perimeter
- Each zone can contain multiple binary sensors
- Sensor debouncing — prevents false alarms from flapping sensors
- Graceful handling of unavailable/missing sensors

**6 Smart Modules**
| Module | Function |
|--------|----------|
| Camera | POE port control, recording mode management |
| Lock | Smart lock automation with retry logic |
| Lights | Auto control, emergency flash patterns |
| Climate | Multi-zone heating/cooling management |
| Siren | Alarm sounds with multiple patterns |
| TTS | Voice notifications, supports cloud_say, google_say, piper, and custom services |

**Monitoring**
- System health score with per-module status
- Battery auto-discovery across all HA devices
- Low/critical battery warnings
- Enhanced diagnostics download

**Testing**
- Three test levels: Quick (~30s), Standard (~60s), Full (~90s)
- Test result history (last 10 runs)
- Per-module async test execution

**Configuration Panel**
- Modern sidebar UI (Alarmo-style)
- Mobile-responsive with bottom navigation
- Real-time WebSocket updates
- Toast notifications — no browser popups
- In-panel confirm dialogs
- Environmental sensors always-on section with forced notifications
- Fake Presence toggle to block automatic arming
- Home Alone Monitor camera configuration
- Sensor hide/exclude for irrelevant device trackers
- User to person tracker binding for presence automation

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

### Module Configuration

All modules are configured via the **Modules tab** in the panel. Each module can be enabled/disabled independently. Configuration changes take effect after restarting Home Assistant.

---

## Automation Examples

### Auto-arm when everyone leaves

```yaml
automation:
  alias: "Secure Me - Auto arm away"
  trigger:
    - platform: state
      entity_id: group.family
      to: "not_home"
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

### Low battery alert

```yaml
automation:
  alias: "Secure Me - Low battery warning"
  trigger:
    - platform: numeric_state
      entity_id: sensor.secure_me_lowest_battery
      below: 20
  action:
    - service: notify.mobile_app
      data:
        title: "Low Battery"
        message: "A sensor battery is below 20%. Check Secure Me panel."
```

---

## Services

| Service | Description |
|---------|-------------|
| `secure_me.arm_away` | Arm in away mode (all zones active) |
| `secure_me.arm_home` | Arm in home mode (perimeter only) |
| `secure_me.arm_night` | Arm in night mode (perimeter + entry) |
| `secure_me.arm_vacation` | Arm in vacation mode (extended trigger) |
| `secure_me.disarm` | Disarm the alarm |
| `secure_me.trigger` | Manually trigger alarm |
| `secure_me.run_test` | Run a system test |
| `secure_me.enable_module` | Enable a specific module |
| `secure_me.disable_module` | Disable a specific module |

All arm services accept optional `code` (string) and `skip_delay` (boolean) parameters.

---

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| `alarm_control_panel.secure_me` | Alarm Control Panel | Main alarm entity |
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
| `secure_me_module_error` | `module`, `action`, `error` | Fired when a module fails |

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
Clear browser cache: Chrome/Edge `Ctrl+Shift+R`, Firefox `Ctrl+F5`

**Alarm arms but doesn't trigger**
Check that sensors are configured in the Sensors tab and zones are set up in the Zones tab. Run a Full test from the Testing tab.

**Module shows error health badge**
Check the module's entities are available in HA. An entity marked `unavailable` in HA will show as an error in Secure Me.

**Exit/entry delay countdown not showing**
The countdown updates every second. If it jumps (e.g. 30 → 25), this is by design — full entity refresh happens every 5 seconds for performance.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

**Developer:** KingPainter  
**Version:** 1.1.0  
**Repository:** [github.com/kingpainter/secure-me](https://github.com/kingpainter/secure-me)
