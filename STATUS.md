# Secure Me — Development Status

## Current version: 1.5.0 (unreleased)

---

## What is in 1.5.0

### Floorplan (complete)
- PNG upload, room drawing (rect + polygon), door/window opening markers
- Sensor assignment per room; rooms glow in Home Alone live view
- Sensor pin markers on floorplan (x_pct/y_pct positions, active = red pulse, inactive = green)
- Door/window openings show live open/closed state from assigned sensor
- Undo (Ctrl+Z, 20 steps), keyboard shortcuts, touch/pointer events
- HACS survival: PNG backed up as base64 in HA storage, auto-restored on startup
- Self-heal: missing PNG clears only image metadata, not room/sensor assignments

### Alarm state fix
- `alarm_control_panel.py` now overrides `alarm_state` property (not `state`) returning `AlarmControlPanelState` enum
- `armed_home_alone` maps to `ARMED_CUSTOM_BYPASS` for HA compatibility
- `secure_me_mode` attribute always exposes the true coordinator state
- Panel reads `secure_me_mode` attribute — fixes "Disarmed" shown when Home Alone was active

### Frontend UX
- Triggered sensor name shown in topbar pill (friendly name, max 22 chars)
- WS reconnect banner under topbar on connection loss, auto-hides on reconnect
- Skeleton shimmer loading state on first panel load
- Module tab render cache — skips re-render when modules + health data unchanged

### Architecture
- `websocket_api.py` split: `ws_sensors.py`, `ws_modules.py`, `ws_floorplan.py`, `ws_alarm.py`, `ws_helpers.py`
- `websocket_api.py` reduced to 172 lines (entry point only)
- Shared `_get_store()` / `_get_coordinator()` in `ws_helpers.py`

### Startup robustness
- 3x retry with 2s delay on `async_config_entry_first_refresh` before `ConfigEntryNotReady`

### Sensor options
- `allow_open` flag: permanent bypass regardless of arm mode
- `force` parameter on `arm_away` / `arm_home` WebSocket endpoints

### Special Features tab
- Auto Actions v2: three independent timers on trigger
- Fake Presence v2: selective blocking (alarm, locks, cameras independently)

---

## Files changed in 1.5.0 (relative to 1.4.3)

### New files
| File | Description |
|------|-------------|
| `custom_components/secure_me/ws_sensors.py` | WS sensors, zones, users, NFC sub-module |
| `custom_components/secure_me/ws_modules.py` | WS modules, notifications, tests, fake presence sub-module |
| `custom_components/secure_me/ws_floorplan.py` | WS floorplan sub-module |
| `custom_components/secure_me/ws_alarm.py` | WS arm/disarm, auto actions sub-module |
| `custom_components/secure_me/ws_helpers.py` | Shared `_get_store` / `_get_coordinator` helpers |
| `custom_components/secure_me/auto_actions.py` | Auto Actions v2 engine |
| `custom_components/secure_me/floorplan/` | PNG storage directory (git-ignored) |

### Modified files
| File | Key changes |
|------|-------------|
| `custom_components/secure_me/__init__.py` | 3x retry on first_refresh |
| `custom_components/secure_me/websocket_api.py` | Reduced to 172-line entry point |
| `custom_components/secure_me/alarm_control_panel.py` | `alarm_state` property, `secure_me_mode` attribute |
| `custom_components/secure_me/store.py` | Floorplan rooms/openings, PNG backup, allow_open, fake_presence_v2, auto_actions |
| `custom_components/secure_me/coordinator.py` | Auto Actions v2, fake presence v2, force-arm |
| `custom_components/secure_me/zones.py` | `allow_open`, force-arm bypass |
| `custom_components/secure_me/const.py` | Floorplan constants, `ATTR_SENSOR_ALLOW_OPEN`, FP_* |
| `custom_components/secure_me/frontend/secure-me-panel.js` | All frontend features above |
| `manifest.json` | version 1.5.0 |

---

## Test suite status

- **168 tests** in 11 files (baseline from 1.4.3 cycle)
- All 168 passing on Python 3.11 and 3.12
- GitHub Actions: HACS 7/8 (brands expected fail), Hassfest all pass

### Tests not yet written for 1.5.0 features
- Floorplan endpoints (`ws_get_floorplan`, `ws_save_floorplan_image`, `ws_save_floorplan_markers`)
- `alarm_control_panel.alarm_state` property mapping
- `ws_helpers._get_store` / `_get_coordinator`
- `allow_open` bypass in `zones.py`
- Force-arm `bypassed_sensors` response
- Auto Actions v2 timer logic
- Fake Presence v2 selective blocking

---

## Ready to commit?

### Blockers
- None — all known bugs fixed, all 168 existing tests pass

### Recommended before tagging 1.5.0
- [ ] Deploy to live server and smoke-test floorplan live view (sensor pins, room glow, opening indicators)
- [ ] Verify `armed_home_alone` pill shows correctly after `alarm_control_panel.py` change
- [ ] Verify WS reconnect banner appears/disappears correctly
- [ ] Write tests for 1.5.0 features (optional but good hygiene)
- [ ] Update README feature list

---

## Deployment order for 1.5.0

1. `ws_helpers.py` — new file (write)
2. `ws_sensors.py` — new file (write)
3. `ws_modules.py` — new file (write)
4. `ws_floorplan.py` — new file (write)
5. `ws_alarm.py` — new file (write)
6. `websocket_api.py` — replace existing
7. `alarm_control_panel.py` — replace existing
8. `__init__.py` — replace existing
9. `store.py` — replace existing (if updated)
10. `coordinator.py` — replace existing (if updated)
11. `frontend/secure-me-panel.js` — replace existing
12. HA restart
