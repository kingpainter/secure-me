# Secure Me Panel — User Guide

**Version:** 0.8.0  
**Last Updated:** 2026-02-20  
**Minimum HA Version:** 2025.1.1+

---

## Overview

The Secure Me panel is the main configuration interface for the integration. It lives in the Home Assistant sidebar and communicates with the backend via WebSocket for real-time updates.

**Access:** Sidebar → Secure Me

---

## Panel Tabs

| Tab | Purpose |
|-----|---------|
| Sensors | Enable/disable binary sensors to monitor |
| Zones | Create and configure alarm zones |
| Users | Manage alarm codes and user access |
| Modules | Configure the 6 smart modules |
| Automations | Custom automation triggers |
| Settings | Alarm delays and system settings |
| Testing | Run system tests and view health |

---

## Sensors Tab

Add the binary sensors (door contacts, motion, window sensors) you want the alarm to monitor.

- Toggle sensors on/off without removing them
- Set sensor type: Contact, Motion, Presence, Vibration, Smoke, CO, Water
- Disabled sensors are ignored by zone monitoring

---

## Zones Tab

Zones group sensors and define how they behave when the alarm is armed.

**Zone Types:**

| Type | Behavior when armed |
|------|-------------------|
| Entry | Starts entry delay countdown — gives you time to disarm |
| Instant | Triggers alarm immediately, no delay |
| Interior | Triggers immediately when Armed Away (ignored in Home/Night) |
| Perimeter | Triggers immediately in all armed modes |

**Creating a zone:**
1. Click Add Zone
2. Enter a name and select zone type
3. Assign sensors from your enabled sensor list
4. Save — zone is active immediately

---

## Users Tab

Manage who can arm and disarm the alarm.

- Each user has a unique numeric code (min. 4 digits)
- Codes are validated on arm/disarm operations
- Users can be deleted — confirm dialog prevents accidents

---

## Modules Tab

Enable and configure the 6 smart modules. Each module card shows:
- Toggle to enable/disable
- Health badge: **OK** / **Warning** / **Error** / **Degraded**
- Configure button (opens entity selection dialog)

**Health badges** update automatically from the coordinator — no manual refresh needed.

**After configuring a module, restart Home Assistant to activate changes.**

### Module Overview

**Camera** — Controls POE switches and recording mode when alarm arms/triggers.
Configure which camera entities and POE switch ports to manage.

**Lock** — Locks smart locks when armed, unlocks when disarmed.
Includes exponential backoff retry (2s → 4s → 8s) for reliability.

**Lights** — Turns lights off when arming, flashes them during alarm trigger.
Configure which light entities to control.

**Climate** — Sets away temperature when armed, restores on disarm.
Configure thermostats and preferred away/home temperatures.

**Siren** — Sounds alarm via Xiaomi gateway or compatible siren devices.
Configure gateway entity and ringtone settings.

**TTS** — Announces alarm status via media players.
Configure media player entities and volume level. Supports Danish.

---

## Testing Tab

Run system tests to verify everything is working correctly.

### Test Levels

**Quick Test (~30s)**
- Entity availability check for all enabled modules
- Flags modules with no entities configured (Warning)
- Battery discovery skipped

**Standard Test (~60s)**
- All Quick checks
- Calls `async_test()` on each enabled module
- Battery discovery and low/critical count

**Full Test (~90s)**
- All Standard checks
- Sensor signal verification (online/offline per sensor)
- Complete battery status with details

### Test Results

| Status | Meaning |
|--------|---------|
| PASS | All checks passed |
| WARNING | Unconfigured modules — system still functional |
| FAIL | One or more modules have unavailable entities |

Battery status is **informational only** — never affects PASS/FAIL.

Test history stores the last 10 results.

### Recommended Testing Schedule

```
After configuration change:  Quick Test
Weekly:                      Standard Test
Monthly:                     Full Test
```

### Module Health Automation

```yaml
automation:
  alias: "Secure Me - Module health alert"
  trigger:
    - platform: state
      entity_id:
        - binary_sensor.secure_me_camera_health
        - binary_sensor.secure_me_lock_health
        - binary_sensor.secure_me_lights_health
        - binary_sensor.secure_me_climate_health
        - binary_sensor.secure_me_siren_health
        - binary_sensor.secure_me_tts_health
      to: "off"
      for: "00:05:00"
  action:
    - service: notify.mobile_app
      data:
        title: "Secure Me - Module Issue"
        message: "{{ trigger.to_state.attributes.friendly_name }} needs attention"
```

### Daily Health Summary

```yaml
automation:
  alias: "Secure Me - Daily health summary"
  trigger:
    - platform: time
      at: "08:00:00"
  action:
    - service: notify.mobile_app
      data:
        message: >
          Secure Me: {{ states.binary_sensor
            | selectattr('entity_id', 'search', 'secure_me.*_health')
            | selectattr('state', 'eq', 'on') | list | count }}/6 modules healthy.
          Lowest battery: {{ states('sensor.secure_me_lowest_battery') }}%
```

---

## Alarm Status

The sidebar and mobile header show the current alarm state at all times:

| State | Display |
|-------|---------|
| Disarmed | Green pill |
| Arming | Yellow pill with countdown |
| Armed | Red pill |
| Pending | Yellow pulsing — entry delay active |
| Triggered | Red pulsing — alarm is active |

---

## Notifications

All actions in the panel use **toast notifications** — non-blocking messages that appear in the top-right corner and auto-dismiss after 4 seconds. No browser popups.

Toast types:
- **Green** — success (saved, deleted, test sent)
- **Red** — error (save failed, entity not found)
- **Yellow** — warning (validation, missing fields)
- **Blue** — info (coming soon features)

---

## Mobile

On devices 768px wide or narrower, the panel switches to a mobile layout:
- Top header with logo and alarm status
- Bottom navigation bar with primary tabs
- "More" button opens slide-up drawer for additional tabs
- iOS safe-area support

---

## Battery Tracking

The integration auto-discovers all Home Assistant entities with `device_class: battery`.

Tracked via two sensors:
- `sensor.secure_me_lowest_battery` — lowest battery % across all devices
- `sensor.secure_me_battery_count` — total number of tracked batteries

**Battery thresholds:**
- Below 20% — Low warning
- Below 10% — Critical warning

**Low battery alert:**
```yaml
automation:
  alias: "Secure Me - Low battery"
  trigger:
    - platform: numeric_state
      entity_id: sensor.secure_me_lowest_battery
      below: 20
  action:
    - service: notify.mobile_app
      data:
        title: "Low Battery"
        message: "A Secure Me sensor battery is below 20%. Check the Testing tab."
```

---

## Troubleshooting

**Panel blank / not loading after update**
Hard refresh browser: Chrome/Edge `Ctrl+Shift+R`, Firefox `Ctrl+F5`, Safari `Cmd+Option+R`

**Module health badge shows Error**
Check that the module's configured entities are available in HA (Developer Tools → States). An unavailable entity triggers the error state.

**Test shows FAIL**
Click the failed module in test results for details. Common causes: entity ID changed, device offline, module configured but entity removed from HA.

**Battery not showing**
Run a Full Test to trigger battery discovery. Batteries must have `device_class: battery` set in HA.

**Alarm armed but sensors don't trigger**
Confirm sensors are enabled in the Sensors tab AND assigned to a zone in the Zones tab. Run Full Test to see sensor online/offline status.

**Enable debug logging:**
```yaml
logger:
  default: info
  logs:
    custom_components.secure_me: debug
```
View at: Settings → System → Logs (filter: `secure_me`)

---

## Support

- **GitHub Issues:** https://github.com/kingpainter/secure-me/issues
- **Diagnostics:** Settings → Devices & Services → Secure Me → Download Diagnostics
- **System Health:** Developer Tools → Info → System Health
