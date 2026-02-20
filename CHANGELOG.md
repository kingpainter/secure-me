# Changelog - Secure Me

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.8.0] - 2026-02-20

### Documentation Overhaul

#### Added
- `README.md` — Complete rewrite with installation, configuration, automation examples, services reference, entities reference, events reference, and troubleshooting
- `info.md` — HACS store page rewritten to reflect current features
- `INSTALLATION.md` — Simplified installation guide for v0.8.0
- `CHANGELOG.md` — Entries added for v0.4.0 through v0.8.0

#### Changed
- Removed outdated v0.3.0.1 bugfix content from README and INSTALLATION
- All docs now reflect v0.8.0 feature set

---

## [0.7.0] - 2026-02-20

### UX Improvements

#### Added
- **Toast notification system** — Replaces all 38 `alert()` calls with styled in-panel toasts
  - Types: success (green), error (red), warning (yellow), info (blue)
  - Auto-dismiss after 4 seconds, manual close button
  - Animates in from right, fades out
- **In-panel confirm dialogs** — Replaces browser `confirm()` with styled overlay dialogs
  - Descriptive messages ("This zone and all its sensors will be removed")
  - Cancel + Delete buttons, click-outside to dismiss
- **Module health badges** — Modules tab shows OK/Warning/Error/Degraded badge per module
  - Uses existing health data — no extra API calls
  - Updates automatically when health event fires
- **Triggered state pulse** — Status pill in sidebar and mobile header pulses red during alarm
  - CSS `@keyframes` animation — no JavaScript polling
  - Pending state shown in yellow

#### Changed
- `stateClass` logic extended to handle `triggered` and `pending` states

---

## [0.6.0] - 2026-02-20

### Performance Optimization

#### Changed
- **Coordinator countdown**: `_countdown_updated()` no longer calls `async_request_refresh()` every second.
  Instead writes countdown to `self.data` in-place and calls `async_update_listeners()`.
  Full refresh only at `countdown=0` or every 5 seconds — ~80% reduction in coordinator work during delays.
- **Health event throttling**: `_async_update_data()` now throttles `secure_me_health_updated` event
  to maximum once per 5 seconds using `time.monotonic()`. Previously fired every second during countdowns.
- **Sensor debouncing**: `ZoneManager` now debounces per-sensor trigger callbacks to 500ms.
  Flapping sensors (on/off/on within 500ms) fire the callback only once.
- **Frontend render batching**: `_loadData()` and health subscription handler use `_queueRender()`
  (50ms debounce) instead of direct `_render()`. Parallel data loads merge into one DOM update.

---

## [0.5.0] - 2026-02-20

### Edge Case Handling

#### Fixed
- **Race condition on rapid arm/disarm**: `_cancel_countdown()` is now `async` and awaits task
  completion before proceeding. Prevents countdown leaking into next state cycle.
- **Auto-reset after trigger**: `_trigger_reset_timer()` implemented — alarm auto-resets to
  `disarmed` after `trigger_time` seconds. Previously a TODO since v0.1.0.
- **Transition lock**: `asyncio.Lock()` added to all arm/disarm methods — prevents simultaneous
  state transitions from race conditions.
- **Sensor deleted from HA while armed**: `new_state=None` handled gracefully in `ZoneManager`.
  Sensor treated as closed, user notified via `persistent_notification`.
- **Sensor goes unavailable while armed**: `unavailable`/`unknown` state treated as closed (not open).
  User notified, alarm not triggered. Prevents false alarms during WiFi outages.
- **`check_for_open_sensors()`**: Now skips unavailable/missing sensors. Arming no longer blocked
  by an offline sensor.
- **Sensor opens during exit delay**: Zone trigger now ignored while in `arming` state.
  User is still leaving — sensor will be monitored once fully armed.

#### Added
- `secure-me-panel.js`: `_healthUpdateUnsubscribe` bugfix — `subscribeEvents()` returns a Promise,
  must be `await`ed to get the actual unsubscribe function. `disconnectedCallback` now uses
  `typeof === 'function'` guard to prevent calling a pending Promise.

---

## [0.4.0] - 2026-02-20

### Enhanced Error Handling

#### Added
- **Centralized retry with exponential backoff** in `base.py`:
  - `async_call_service_with_retry(domain, service, data, target, action)`
  - Default: 3 retries, 2s → 4s → 8s backoff
  - Configurable per-module via `retry_max`, `retry_delay`, `retry_backoff` config keys
- **Graceful degradation**: One module failure does not stop other modules
- **Degraded state tracking**: `module.degraded` property, `_consecutive_errors` counter
- **User notifications**: `persistent_notification` created on module failure or recovery
- **Recovery notifications**: User notified when degraded module recovers after retry

#### Changed
- `coordinator.py`: Unified `_execute_modules(action, call)` replaces 5 separate execute methods
- `lock.py`: Removed custom `_lock_with_retry()` — now uses base class retry (20 lines removed)
- `camera.py`, `lights.py`, `climate.py`, `siren.py`, `tts.py`: All migrated to base retry
- Total of 20 retry-protected service calls across all 6 modules

#### Retry coverage by module
| Module | Retry calls |
|--------|-------------|
| Lock | 3 (lock on arm, unlock on disarm, test) |
| Camera | 4 (POE on/off, recording on/off) |
| Lights | 3 (off on arm, off/restore on disarm, on trigger) |
| Climate | 5 (away preset/temp, home preset, restore) |
| Siren | 3 (play, stop, gateway light off) |
| TTS | 2 (volume set, announcement) |

---

## [0.3.6] - 2026-02-20

### Phase 3b Complete - Version Consistency

#### Added
- `validate_version.py` — checks version consistency across all 26 files
- GitHub Actions: `Version Consistency` job in `validate.yaml`
- Auto-fix mode: `python3 validate_version.py --fix`

#### Fixed
- Version mismatch: all 26 files now consistently at `0.3.6`

---

## [0.3.5] - 2026-02-20

### Test Logic Accuracy

#### Fixed
- Enabled modules with 0 entities now report `warning` instead of `pass`
- Battery discovery now runs during test execution (was missing entirely)

#### Changed
- Test summary includes `warned` count
- Overall: `fail` > `warning` > `pass` — warning never blocks pass

---

## [0.3.4] - 2026-02-20

### Visual Consistency

#### Added
- 5 new SVG icons: `ok`, `warn`, `fail`, `close`, `circle`
- `dots` icon for mobile More button

#### Fixed
- All HTML entities replaced with SVG icons
- Corrupted bullet/POE label characters fixed

---

## [0.3.3] - 2026-02-20

### Mobile Navigation

#### Added
- Mobile bottom navigation bar (≤768px) with 5 primary tabs + More drawer
- Mobile top header with logo and alarm status pill
- iOS safe-area support

#### Fixed
- F1: `_get_module_entity_ids()` checks all attribute names
- F2: Health status sync between panel and binary sensors
- F5: Camera module config structure fallback
- F6: TTS module included in health checks

---

## [0.3.2] - 2026-02-14

### Phase 3 Complete — Test Suite Fixed

#### Fixed
- `test_init_.py` removed
- Version checks updated in all test files
- `hacs.json` path fixed in `test_files.py`
- `conftest.py` fixtures completed

#### Status
- 100/100 unit tests passing
- GitHub Actions: HACS 7/8, Hassfest all, Pytest 3.11+3.12 all green

---

## [0.3.1] - 2026-02-13

### System Health, Diagnostics & Panel

#### Added
- System health integration (10 metrics)
- Enhanced diagnostics (6 sections)
- Panel registration via `panel.py` (Alarmo-style)

#### Fixed
- All emojis removed from frontend and backend (UTF-8 safety)

---

## [0.3.0] - 2026-02-13

### Phase 3 — Testing & Health Monitoring

#### Added
- Three-tier testing: Quick / Standard / Full
- Module health binary sensors
- Battery tracking with auto-discovery
- WebSocket test API
- Test result persistence (last 10)

---

## [0.2.0] - 2026-02-04

### Phase 2 — 6 Smart Modules

#### Added
- Camera, Lock, Lights, Climate, Siren, TTS modules
- Module manager and base class

---

## [0.1.0] - 2026-02-03

### Phase 1 — Core Logic

#### Added
- DataUpdateCoordinator
- State machine with delays
- Zone manager
- Code validation

---

## [0.0.1] - 2026-02-01

### Phase 0 — Foundation

#### Added
- Integration framework, config flow
- Manifest, constants, translations (EN + DA)
- GitHub Actions CI/CD
- MIT License
