# Secure Me — Development Status

## Current version: 1.5.4 (committed 2026-08-23)

---

## What is in 1.5.4 (2026-08-23)

### Presence-system consolidation
- Removed `PresenceMonitor` (coordinator.py) entirely -- the older, hardcoded-900s, Secure-Me-users-only auto-arm mechanism. `AutoActionsManager` (Auto Actions v2, auto_actions.py) is now the sole presence-based automation system, eliminating the risk of duplicate notifications and inconsistent behaviour between the two.
- `AutoActionsManager` re-scoped to only watch `person_entity`/`tracker_entity` from enabled Secure Me user profiles (`async_refresh_trackers()`) -- previously it watched every `person.*` entity in the whole HA instance, so an unrelated person entity (guest, test account, another integration) could silently block or delay Auto Actions.
- New initial-presence check at startup (`_check_initial_presence()`, called from `async_start()`): if the house is already empty when HA restarts, Auto Actions now starts its timers immediately instead of waiting for a state_changed event that will never come.
- Fake Presence is now re-checked immediately before an action executes, not just once when the house was first found empty -- closes a race where toggling Fake Presence on mid-countdown didn't actually block the action.
- `tests/test_auto_actions.py` (new, 17 tests) locks in all of the above.

### Robustness
- `identify_user_id()` (coordinator.py) now delegates to a new `store.authenticate_user_with_id()`, reusing `authenticate_user()`'s parallel ThreadPoolExecutor bcrypt-check instead of running its own sequential per-user bcrypt loop directly on the caller's thread.

### Frontend
- `secure-me-panel.js`: extracted the near-identical Lock/Climate module entity-search-and-filter wiring (previously duplicated ~15 lines each) into one shared `_wireEntitySearchFilter()` helper.

### Dead code removed
- `notification_dispatcher.send_auto_arm_notification()` and the three `AUTO_ARM_*` constants in const.py -- both only ever backed the now-removed `PresenceMonitor`.

### Status
- Committed 2026-08-23. CI: all green.

---

## What is in 1.5.1 (released 2026-07-24)

### Critical fix: real sensor-caused alarm trigger never activated siren/camera/lights/lock/TTS
- A real sensor breach while armed went through `ZoneManager` → `coordinator._zone_triggered()` → `state_machine.trigger_entry_delay()` and never called `coordinator._execute_modules_trigger()` — the method that actually calls `siren.async_trigger()` and the other five modules. That method was only ever reachable from a manual `secure_me.trigger` service call. Result: on a real intrusion, state went to `triggered` and the push notification fired, but nothing physically happened (no siren, no camera activation, no lock, no lights, no TTS).
- Also fixed: `_triggered_by` and `_last_triggered` were only ever populated for a manual trigger, leaving both stale for every real sensor-caused trigger.
- Fixed by making `coordinator._state_changed()` the single dispatch point for module execution on any transition into `STATE_ALARM_TRIGGERED`, guarded so it runs exactly once per cycle regardless of entry path (instant zone, entry-delay countdown, or manual service call).
- New `tests/test_coordinator_trigger.py` (5 tests, real end-to-end, no mirrors) locks in the fix. Full suite: 367/367 green in CI.
- See `CHANGELOG.md` [1.5.1] for full detail.

---

## What was in 1.5.0 (released 2026-07-19)

### Floorplan (complete)
- PNG upload, room drawing (rect + polygon), door/window opening markers
- Sensor assignment per room; rooms glow in Home Alone live view
- Sensor pin markers on floorplan (x_pct/y_pct positions, active = red pulse, inactive = green)
- Door/window openings show live open/closed state from assigned sensor
- Undo (Ctrl+Z, 20 steps), keyboard shortcuts, touch/pointer events
- HACS survival: PNG backed up as base64 in HA storage, auto-restored on startup
- Self-heal: missing PNG clears only image metadata, not room/sensor assignments
- **Live-view parity fixed:** the dashboard alarm card (`secure-me-alarm-card.js`) was missing sensor pin markers entirely -- it only rendered room glow + opening fade, while the panel's own "Alene-tilstand live" preview had pins all along. Ported the pin renderer into the card and fixed two supporting bugs (`_loadDynamic()` never copied `fp.markers` into the card's state; the live sensor-watch list didn't track pin-only sensors). Verified with a functional Node smoke test, not just syntax checking.

### Control API (complete)
- `services.py`: the `secure_me.arm_away` / `arm_home` / `arm_night` / `arm_vacation` / `arm_home_alone` / `disarm` / `trigger` / `run_test` / `enable_module` / `disable_module` services are now actually registered with `hass.services.async_register()`. They had been documented in `services.yaml` since early versions with no backing handler -- calling any of them failed with "service not found".
- `services.yaml`: added the missing `arm_home_alone` entry and the `force` field on all five arm services (previously undocumented despite README and the coordinator already supporting it).
- `secure-me-alarm-card.js`: `arm_vacation` now goes through the standard `alarm_control_panel.alarm_arm_vacation` service (first-class HA feature since v1.4.3) instead of a websocket call. Only `arm_home_alone` remains websocket/custom-service-only, since HA's `alarm_control_panel` interface has no standard command for it.
- New `API.md`: formal, versioned documentation of the alarm entity's state mapping, attribute contract, and which arm/disarm modes use standard HA services vs. `secure_me.*` services vs. websocket.

### Alarm state fix
- `alarm_control_panel.py` now overrides `alarm_state` property (not `state`) instead of the default `state` property
- `armed_home_alone` initially mapped to `ARMED_CUSTOM_BYPASS` for HA compatibility, but this broke `secure_me_alarm_tab_card.js` (couldn't distinguish Home Alone from a real bypass) -- **reverted within this same cycle** to report the raw string `"armed_home_alone"` directly instead (see CHANGELOG.md's "Home Alone state collision (regression, reverted)" entry and `API.md` §2 for the full detail). The other five modes (disarmed/away/home/night/vacation) are unaffected and use HA's native enum throughout.
- `secure_me_mode` attribute always exposes the true coordinator state (identical to `entity.state` for home_alone since the revert)
- Panel reads `secure_me_mode` attribute -- fixes "Disarmed" shown when Home Alone was active

### Frontend UX
- Triggered sensor name shown in topbar pill (friendly name, max 22 chars)
- WS reconnect banner under topbar on connection loss, auto-hides on reconnect
- Skeleton shimmer loading state on first panel load
- Module tab render cache — skips re-render when modules + health data unchanged

### Architecture
- `websocket_api.py` split: `ws_sensors.py`, `ws_modules.py`, `ws_floorplan.py`, `ws_alarm.py`, `ws_helpers.py`
- `websocket_api.py` reduced to 172 lines (entry point only)
- Shared `_get_store()` / `_get_coordinator()` in `ws_helpers.py`

### Bug fixes found via CI / self-audit this cycle
- `zones.py`: `Zone.update_sensor_state()` returned whether the zone's *aggregate* `is_triggered` flag flipped rather than whether the *specific sensor's own* open/closed status changed. In a multi-sensor zone, once one sensor was already open, a second sensor opening was silently dropped before reaching debounce or Home Alone door-dispatch. Fixed to track per-sensor membership change. Caught by CI (`test_different_doors_debounced_independently`).
- `coordinator.py`: scheduled test runner imported `_run_test_internal` from the wrong module (`websocket_api` instead of `ws_modules`) -- every scheduled test run would have crashed with `ImportError`.
- `services.py`: `enable_module`/`disable_module` now normalize module config before calling `coordinator.update_module_config()`, matching `ws_save_module`'s existing behaviour -- otherwise the store's raw panel-object config would silently break a module's entity extraction.

### Startup robustness
- 3x retry with 2s delay on `async_config_entry_first_refresh` before `ConfigEntryNotReady`

### Sensor options
- `allow_open` flag: permanent bypass regardless of arm mode
- `force` parameter on all five arm websocket endpoints and now also on the `secure_me.*` services

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
| `custom_components/secure_me/services.py` | Real `hass.services.async_register()` handlers backing `services.yaml` |
| `custom_components/secure_me/auto_actions.py` | Auto Actions v2 engine |
| `custom_components/secure_me/floorplan/` | PNG storage directory (git-ignored) |
| `API.md` | Formal alarm entity API contract (state mapping, attributes, arm/disarm paths) |

### Modified files
| File | Key changes |
|------|-------------|
| `custom_components/secure_me/__init__.py` | 3x retry on first_refresh; registers/unregisters `services.py` |
| `custom_components/secure_me/websocket_api.py` | Reduced to 172-line entry point |
| `custom_components/secure_me/alarm_control_panel.py` | `alarm_state` property, `secure_me_mode` attribute |
| `custom_components/secure_me/store.py` | Floorplan rooms/openings, PNG backup, allow_open, fake_presence_v2, auto_actions |
| `custom_components/secure_me/coordinator.py` | Auto Actions v2, fake presence v2, force-arm, fixed `_run_test_internal` import |
| `custom_components/secure_me/zones.py` | `allow_open`, force-arm bypass, fixed per-sensor `update_sensor_state` bug |
| `custom_components/secure_me/const.py` | Floorplan constants, `ATTR_SENSOR_ALLOW_OPEN`, FP_* |
| `custom_components/secure_me/services.yaml` | Added `arm_home_alone` entry + `force` field on all arm services |
| `custom_components/secure_me/frontend/secure-me-panel.js` | All frontend features above |
| `custom_components/secure_me/frontend/secure-me-alarm-card.js` | Standard vacation arming, floorplan pin markers, live-watch fix |
| `README.md` | Link to `API.md` |
| `manifest.json` | version 1.5.0 |

---

## Test suite status

- **404 tests** as of 1.5.4 (384 + 20 new in `tests/test_services.py`)
- All passing on Python 3.13 (CI matrix; see `pytest.yaml`)
- GitHub Actions: HACS 7/8 (brands expected fail), Hassfest all pass
- `test_zones_edge_cases.py` rewritten this cycle to test the real `ZoneManager`/`Zone` classes instead of local mirror copies -- the mirror-class pattern had let the `zones.py` aggregate-vs-per-sensor bug above ship undetected, and had also drifted from real behaviour (asserted a notification fires for unavailable sensors, which hasn't been true since v1.4.2)

### Tests not yet written for 1.5.0 features
- Floorplan endpoints (`ws_get_floorplan`, `ws_save_floorplan_image`, `ws_save_floorplan_markers`)
- Floorplan sensor pin rendering in `secure-me-alarm-card.js` (covered so far only by an ad-hoc Node smoke test during development, not a committed test file)

~~`secure_me.*` services in `services.py`~~ -- **covered as of 1.5.4** by `tests/test_services.py` (20 tests: all ten services registered/unregistered, each arm service calling its matching coordinator method with the right arguments, disarm's required-code schema, run_test's test_type validation, enable_module/disable_module saving + normalizing + firing events, and graceful no-op when the coordinator/store isn't ready yet).

~~Auto Actions v2 timer logic~~ and ~~Fake Presence v2 selective blocking~~ -- **covered as of 1.5.4** by `tests/test_auto_actions.py` (17 tests: Secure Me user scoping, initial-presence startup check, Fake Presence re-check at execution time, and `_all_persons_away()` fail-safe behaviour). See the 1.5.4 section below.

---

## Ready to commit?

### Blockers
- None — all known bugs fixed, full test suite green in CI

### Recommended before tagging 1.5.0 (historical, all resolved as of 1.5.1)
- [x] Floorplan live view parity between panel preview and dashboard card (sensor pins, room glow, opening indicators) -- verified via functional smoke test
- [x] Verify `armed_home_alone` pill shows correctly after `alarm_control_panel.py` change
- [ ] Verify WS reconnect banner appears/disappears correctly on a live server
- [ ] Write tests for `services.py` and floorplan websocket endpoints (optional but good hygiene)
- [x] Update README feature list (linked `API.md`)
- [x] Decide on version bump timing now that floorplan etape 3 and the control-API audit are both complete — **shipped as 1.5.0 on 2026-07-19**
- [x] Delete `module_manager.py` manually (confirmed dead code, zero references -- see CHANGELOG)
- [x] Remove `Platform.SWITCH`/`Platform.SELECT` from `PLATFORMS` in `const.py` (2026-08-23) and delete `switch.py`/`select.py` manually -- confirmed gone from both the repo and the live server. Both had been empty "Phase 1" placeholders that never registered a single entity.

---

## Deployment order for 1.5.0

1. `ws_helpers.py` — new file (write)
2. `ws_sensors.py` — new file (write)
3. `ws_modules.py` — new file (write)
4. `ws_floorplan.py` — new file (write)
5. `ws_alarm.py` — new file (write)
6. `services.py` — new file (write)
7. `websocket_api.py` — replace existing
8. `alarm_control_panel.py` — replace existing
9. `__init__.py` — replace existing
10. `store.py` — replace existing (if updated)
11. `coordinator.py` — replace existing (if updated)
12. `zones.py` — replace existing
13. `services.yaml` — replace existing
14. `frontend/secure-me-panel.js` — replace existing
15. `frontend/secure-me-alarm-card.js` — replace existing
16. HA restart
