## [1.2.0] - 2026-03-21

### Security & Stability Release (Alarmo-Inspired)

#### Security
- **bcrypt user code hashing** — User PIN codes are now hashed with bcrypt (10 rounds, base64-encoded) instead of stored as plaintext. Existing users with plaintext codes are migrated transparently on next save. `authenticate_user()` uses `ThreadPoolExecutor` for non-blocking parallel code checks (max 4 workers).

#### Storage
- **Versioned MigratableStore** — `store.py` now uses `STORAGE_VERSION_MAJOR=2` with a `_MigratableStore` subclass that handles schema migration. v1 data is automatically upgraded: `sensor_groups` key added, per-sensor fields (`entry_delay`, `auto_bypass`, `arm_on_close`) backfilled with defaults, and legacy plaintext user codes flagged for re-hashing.

#### Sensor Features
- **Sensor groups (anti-masking)** — Sensor groups with `timeout` + `event_count`. Alarm only triggers if N sensors activate within a time window. Prevents false alarms from single sensor glitches. Full CRUD via WebSocket API (`get_sensor_groups`, `save_sensor_group`, `delete_sensor_group`). Groups automatically reload into `ZoneManager` when saved.
- **Per-sensor `entry_delay` override** — Each sensor can have its own entry delay (seconds) that overrides the zone default.
- **Per-sensor `auto_bypass`** — Open sensors at arm time are silently bypassed instead of blocking arming.
- **Per-sensor `arm_on_close`** — Sensor automatically triggers arming (away mode) when it transitions from open to closed (e.g. front door shut).

#### Integration
- **Mobile push notification actions** — Coordinator registers a `mobile_app_notification_action` event listener. Users can arm/disarm directly from HA Companion push notification action buttons using `SECURE_ME_ARM_AWAY`, `SECURE_ME_DISARM`, `SECURE_ME_FORCE_ARM`, etc.
- **Force-arm bypass** — `async_arm_away(force=True)` skips open sensor check (used by push `FORCE_ARM` action).

#### Tests
- **52 new unit tests** in `test_v1_2_0.py` covering bcrypt hashing, `SensorGroup` anti-masking logic, per-sensor helpers, sensor group CRUD, push notification constants, and v2 storage schema.
- `test_store.py` updated: `test_default_data_has_all_keys` includes `sensor_groups`.

---

## [1.1.0] - 2026-03-16

### Feature Release

#### Added
- **Environmental sensors** — Separate read-only section in Sensors tab. Smoke, gas, and moisture sensors are always active; notifications cannot be disabled. Each sensor has a Remove button to correct mis-classifications.
- **TTS multi-service support** — TTS dialog now has a service dropdown: `tts.cloud_say`, `tts.google_translate_say`, `tts.google_say`, `tts.piper`, `tts.voice_rss`, and a Custom free-text field for any other service.
- **Sensor hide/exclude** — Inactive sensors have a Hide button. Irrelevant device_trackers (UniFi, Samsung TV, DLNA, Sonos, etc.) are auto-hidden into a collapsible section. Sensors can be permanently excluded.
- **User → person tracker binding** — Add User dialog includes a person entity dropdown for automatic arm/disarm presence automation. Linked tracker is shown on the user card.
- **Fake Presence toggle** — Toggle on the Sensors tab blocks automatic arming when someone is home. State persists across restarts.
- **Home Alone Monitor** — Future tab now shows a real camera selector for the Home Alone Monitor feature instead of a placeholder.
- **Chevron SVG fix** — Fixed giant icon bug where unsized chevron SVG expanded to fill screen in module config panels.

#### Backend
- `store.py` — `excluded`, `env_unmarked`, `auto_hidden` flags; smart `device_tracker` filtering with irrelevance patterns.
- `websocket_api.py` — New commands: `hide_sensor`, `unmark_environmental`, `get_persons`. TTS normalization passes `tts_service`, `language`, `volume`, `messages` through to `TTSModule`.

#### Changed
- `secure-me-panel.js` — 4894 lines (was 4547). VERSION constant updated to 1.1.0.
- All version strings bumped to 1.1.0 across manifest.json, const.py, panel.py, and panel.js.

---

## [1.0.0] - 2026-03-15

### Production Release

#### Changed
- Version bumped to 1.0.0 across all files
- `secure-me-panel.js` VERSION comment corrected to 1.0.0
- `SECURE_ME_STATUS.md` updated to reflect production release status

#### Status
- HACS submission checklist completed
- End-to-end manual testing passed
- Frontend panel flickering issue resolved
- Logo/branding package submitted to HA brands repository
- Production release published on GitHub
- pytest 168/168 passing on Python 3.11 and 3.12
- GitHub Actions: HACS 7/8 (brands expected fail — OK), Hassfest all, Pytest all green

---

## [0.9.0] - 2026-02-21

### Pre-Release Testing

#### Added
- **68 new unit tests** covering all changes introduced in v0.4.0-v0.8.0:
  - `test_base_module.py` (12 tests) -- retry logic, exponential backoff, degraded state,
    recovery notifications, `async_call_service` single-attempt, state backup helpers,
    entity availability helpers, enable/disable degraded-state clearing
  - `test_zones_edge_cases.py` (28 tests) -- sensor deleted from HA (`new_state=None`),
    sensor unavailable/unknown while armed, `check_for_open_sensors()` skipping offline sensors,
    sensor recovery from unavailable, per-sensor debounce (500ms), disabled zone guards
  - `test_state_machine_v2.py` (28 tests) -- auto-reset after `trigger_time` (was TODO v0.1.0),
    `trigger_time=0` disables auto-reset, double-arm guard, disarm during arming/pending,
    exit delay arming-state guard (sensor open during exit delay ignored),
    already-triggered guard, 7 real `AlarmStateMachine` async tests including
    `_cancel_countdown()` safety, cleanup with active task, state-change callbacks

#### Changed
- Total unit test suite: **168 tests** (was 100)
- Version bumped to 0.9.0 across all files

#### Status
- pytest 168/168 passing on Python 3.11 and 3.12
- GitHub Actions: HACS 7/8 (brands expected fail -- OK), Hassfest all, Pytest all green

---
