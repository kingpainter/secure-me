## [1.4.1] - 2026-04-19

### Fix: Presence auto-arm read wrong field name (critical)
- **Problem:** `PresenceMonitor` read user profiles using `tracker_entity` field, but the frontend has always saved the person entity under `person_entity`. Result: `tracked_users: 0` and auto-arm completely non-functional since v1.1.0, even though the Users-tab UI showed trackers correctly linked.
- **Symptom:** `binary_sensor.secure_me_alarm_system_anyone_home` reported `people_home: none`, `people_away: none`, `tracked_users: 0` despite `person.*` entities being `home`/`not_home`.
- **Loesning:** `coordinator.py` now reads `user.get("person_entity") or user.get("tracker_entity", "")` in both `PresenceMonitor.async_setup()` and `get_presence_status()`. `person_entity` takes precedence (canonical name), `tracker_entity` kept as fallback for any hypothetical legacy profiles. No migration required - existing data already uses `person_entity`.
- After update: **restart Home Assistant** (no need to edit user profiles - data was always correctly stored under `person_entity`).

---

## [1.4.0] - 2026-04-19

### Presence-based Auto-arm
- **`PresenceMonitor` klasse** i `coordinator.py` — overvager `tracker_entity` fra alle bruger-profiler
- Naar alle trackere er `not_home` startes en 15-minutters countdown (`AUTO_ARM_AWAY_DELAY = 900`)
- Naar countdown udloeber: laas alle konfigurerede laase, kaeld `arm_away(auto=True)`
- `auto=True` respekterer Fake Presence-blokeringen (eksisterende logik)
- Timer annulleres straks hvis nogen vender hjem inden countdown udloeber
- Push-notifikation sendes til alle brugere med `notify_service` EFTER handling med liste over hvad systemet gjorde
- `PresenceMonitor` starter i `async_load_store_config()` — dvs. efter store er indlaedt og `tracker_entity`-felterne er tilgaengelige
- Nedlukning via `async_teardown()` i `async_shutdown()`
- Nye konstanter: `AUTO_ARM_AWAY_DELAY`, `AUTO_ARM_PUSH_TITLE`, `AUTO_ARM_PUSH_MESSAGE`
- Ny funktion `send_auto_arm_notification()` i `notification_dispatcher.py`

### Presence Monitor Hardening (2026-04-19)
- **Kritisk fix:** manglende `import asyncio` i `coordinator.py` forhindrede hele auto-arm flowet - `asyncio.ensure_future()` kastede `NameError` der blev slugt af HA's event system, saa countdown aldrig startede
- **Fake Presence guards:** auto-arm flow blokeres nu korrekt naar Fake Presence er aktiv - (1) countdown starter ikke, (2) `_execute_auto_arm()` short-circuiter oeverst i sekvensen (ingen laasning, ingen arm, ingen notifikation), (3) aktivering af Fake Presence annullerer kaerende countdown
- **Live tracker refresh:** ny `PresenceMonitor.async_refresh()` metode + kald fra `ws_save_user` og `ws_delete_user` i `websocket_api.py` - aendringer af user tracker_entity virker nu uden HA restart
- **Idempotent setup:** `PresenceMonitor.async_setup()` rydder tidligere subscriptions foer ny registrering - forhindrer duplicate listeners ved re-invocation

### PIN UX Fix (2026-04-19)
- **Problem:** alarm-kortene armerede/disarmede automatisk saa snart fjerde PIN-ciffer blev tastet - let at aktivere utilsigtet
- **Loesning:** fjernet auto-submit i `secure-me-alarm-card.js` (fjernet `_callArm()` ved `length === 4`) og `secure_me_alarm_tab_card.js` (fjernet `setTimeout(_submit, 130)` ved `length === 4`)
- Bruger skal nu trykke **OK** eksplicit for at aktivere/deaktivere alarmen
- `info-alarm-card.js` krevede allerede OK og behoevede ingen aendring

### State-restore ved HA-genstart (kritisk fix)
- **Problem:** Alarmen disarmede sig selv ved HA-genstart fordi `AlarmStateMachine` altid startede i `disarmed` — ingen state persistence
- **Loesning:** `alarm_control_panel.py` arver nu fra `RestoreEntity` og kalder `async_get_last_state()` i `async_added_to_hass()`
- `coordinator.async_restore_state(state, armed_by)` satter state_machine direkte uden callbacks eller delays — stille restore
- `state_machine.restore_state(state)` satter `_current_state` direkte (ingen events, ingen timers)
- Zone-monitorering genstartes straks i korrekt arm-mode hvis restored state er armed
- Transiente states (`arming`, `pending`, `triggered`) resettes bevidst til `disarmed` ved restore — countdown-kontekst er tabt
- `EVENT_ALARM_ARMED` fyres IKKE ved restore — er en stille genoprettelse

### Tablet-kort fixes (`secure_me_alarm_tab_card.js` → v1.2.0)
- **Arm virkede ikke:** `home`, `away` og `night` kaldte HA's standard `alarm_control_panel` service i stedet for Secure Me's egne websocket-kommandoer. Alle 5 tilstande korer nu konsekvent via `_ws()`
- **Countdown opdaterede ikke:** Ny `_manageCdTicker()` starter et `setInterval` paa 1 sekund under `arming`/`pending`, decrementerer `_countdown` lokalt og opdaterer label-teksten i realtid
- **6 prikker → 4:** Reduceret til 4 prikker, max PIN-laengde sat til 4 cifre
- **Forecast forsvandt:** Root-element manglede `height: 100%; min-height: 0`, `weather-side` havde fast `min-height: 300px` og `padding-bottom: 39px` der pressede forecast-raekken ud af viewport paa tabletten

---

### Unified TTS/Notification Engine

#### New: Speaker Profiles
- **Speaker profiles** defined once in Modules > TTS, referenced everywhere
- Per-profile: `entity_id`, `name`, `volume`, `tts_service`, `tts_entity`
- Replaces flat media_player list + global volume/service settings
- Legacy flat config still works as fallback if no profiles defined

#### New: Multi-speaker engine
- **Parallel playback** across speakers via `asyncio.gather()`
- **Queued per speaker** via `SpeakerQueue` — sequential on same speaker, never overlapping
- **Per-message speaker selection** — custom messages target specific profiles
- **Per-notification speaker selection** — TTS channel picks specific speakers

#### New: Home Alone quick messages
- Alarm card quick-message buttons now load dynamically from panel
- Create notifications with trigger `home_alone_action` in Actions tab
- Buttons automatically appear in alarm card — no Lovelace YAML needed
- Each message can target specific speakers

#### New: WS endpoints
- `secure_me/get_speaker_profiles` — list profiles with live state
- `secure_me/save_speaker_profiles` — save + hot-reload TTS module
- `secure_me/get_home_alone_messages` — alarm card quick messages
- `secure_me/test_tts` — now accepts `speaker_ids` parameter
- `secure_me/arm_vacation`, `secure_me/arm_home_alone`, `secure_me/disarm`

#### Notification dispatcher
- `tts_speakers` field on notifications — routes TTS to specific speakers
- `speaker_ids` parameter through entire TTS callchain
- Smoke/moisture alerts respect per-notification speaker routing

#### Store (v2 schema)
- New `speaker_profiles` key in default data
- `get_speaker_profiles()` / `async_save_speaker_profiles()` CRUD

#### Frontend
- TTS dialog redesigned: Speaker Profiles section with per-profile volume + service
- Custom messages: speaker checkboxes per message
- Notification dialog: speaker checkboxes when TTS channel selected
- `home_alone_action` trigger added to notification dialog
- Alarm card: dynamic TTS buttons from `get_home_alone_messages`

#### Bug fixes (from v1.3.0 audit)
- `alarm_control_panel`: `code_arm_required=True`, `code_format=None`, validate at arm
- `notification_dispatcher`: `store.async_load()` void fix, crash fix
- `modules/tts`: `armed_home_alone` in VALID_TRIGGERS, BCP-47 map extended
- `coordinator`: `asyncio.get_event_loop()` -> `hass.async_create_task()`
- `zones`: `asyncio.ensure_future()` -> `hass.async_create_task()`
- Alarm card: correct entity ID, WS routing for arm_home_alone/vacation
- Alarm card: TTS endpoint `test_tts_message` -> `test_tts`

---

## [1.3.0] - 2026-03-27

### UI/UX Polish Release

#### Frontend
- **Test tab 2-column layout** — Last Test Run | Test History on top, Sensor Status | Battery Overview on bottom. Both rows align correctly.
- **Test History collapsible** — Shows 3 most recent results, older results behind expandable section.
- **Sensor Status** — Shows 7 sensors visible, rest behind collapsible. Consistent with Battery Overview column height.
- **Battery Overview** — Shows 8 batteries sorted low-first, rest behind collapsible.
- **Countdown in sidebar** — Status pill shows live countdown during arming/pending: "Arming 28s", "Pending 15s" etc. Backend already sent countdown — frontend now stores and displays it.
- **Lights module: Steady white** — New section in Lights dialog: turn on lights at 100% white brightness on alarm (no flashing). Separate entity list from emergency flash lights.
- **Lights module: Multi-select picker** — Search field + checkbox list replaces native select dropdown for light entity selection.
- **Environmental sensors collapsible** — Folded by default in Sensors tab, shows sensor names as pills when collapsed.
- **Dark CSS fix for select elements** — All `<select>` and `<option>` elements now themed correctly in shadow DOM.
- **Module name fix** — "Tts" corrected to "TTS" in test result module rows.
- **Test type labels** — "quick" -> "Quick Test", "standard" -> "Standard Test" etc.
- **Person tracker** — Shows short name (strips `person.` prefix) on user cards.
- **Notification cards** — 3-column -> 2-column grid with more padding for breathing room.
- **System/Custom notifications divider** — Visual separator between sections in Actions tab.
- **Zone edit button** — Shows "Edit" text label instead of icon-only.
- **Add Automation** — Renamed from "Ny automation" to "Add Automation".

---

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
