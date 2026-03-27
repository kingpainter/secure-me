# Secure Me — Project Status

**Last updated:** 2026-03-27 (session 2)
**Developer:** KingPainter
**Repository:** https://github.com/kingpainter/secure-me

---

## Current Version: v1.2.0

### GitHub Actions
| Workflow | Status |
|---|---|
| HACS Validation | 7/8 (brands PR pending — expected) |
| Hassfest | All passed |
| Pytest Python 3.11 | All passed |
| Pytest Python 3.12 | All passed (cancelled when 3.11 fails) |
| Version Consistency | Passed |

---

## Active Development (v1.3.0 — in progress)

### Completed today (2026-03-27)
- [x] Environmental sensors section: collapsible — foldet som standard, viser sensor-navne som pills
- [x] Lights module: ny "Steady white lights" sektion — tænder hvidt 100% brightness, ingen flash
- [x] Lights module: multi-select light picker — soegefelt + checkboxes + "Add selected"
- [x] All select dropdowns: mork CSS fix (`select` + `option` global regel i shadow DOM)
- [x] Light picker event binding: flyttet til `_attachDialogListeners` (var fejlagtigt i `_attachTabListeners`)

### Next Steps
- [ ] Manuel test: TTS play button fires only once
- [ ] Manuel test: User notification routing — arm as Flemming, verify only Flemming gets push
- [ ] Manuel test: TTS quiet hours — set 22-07, verify TTS silent at night
- [ ] Manuel test: Triggered broadcast — verify all users with receive_critical get notified
- [ ] Manuel test: Test notification button — only admins receive
- [ ] HACS brands PR (separate repo)
- [ ] Version bump to v1.3.0 when ready

### Known Gaps (tracked for future versions)
| Feature | Priority | Target |
|---|---|---|
| Per-sensor `delay_on` debounce | Medium | v1.3.0 |
| 5 arm modes fully wired in UI (vacation) | Low | v1.3.0 |
| MQTT support | Low | v1.4.0 |
| Health subscription fires 2x (two panel mounts) | Low | v1.3.0 |

---

## v1.2.0 — Completed Features

### TTS Module — Multi-service + Volume Control
- Supports `tts.*` (cloud_say etc.), `notify.*`, and `script.*` (e.g. `script.ultra_tts` / House Voice)
- `script.*` path: sets Alexa volume to configured level → calls `tts.speak` directly (bypasses ultra_tts ducking) → restores original volume
- `tts.cloud_say`: auto-maps short language codes to BCP-47 (`da` → `da-DK`)
- `tts_entity` field: configurable TTS entity (default: `tts.home_assistant_cloud`)
- `_warned_incompatible_service` flag: unknown service types warn once then skip silently
- Single-attempt (`async_call_service`) for TTS speak calls — retry would cause double playback
- Custom messages + test play button per message

### Notification System — User-Routed
- **Channels per notification:** `push`, `tts`, or both
- **User-routed arm/disarm:** `armed_by_id` / `disarmed_by_id` tracked. Armed → only arming user gets confirmation.
- **Broadcast triggers:** `triggered` / `pending` → all users with `receive_critical=True`. Smoke/water always broadcast critical.
- **Low battery** → all users with `receive_alerts=True`
- **Test notifications** → admin users only
- **TTS quiet hours** per user — `tts_quiet_start` / `tts_quiet_end` (hour 0-23)

### User Notification Settings
| Field | Type | Description |
|---|---|---|
| `notify_service` | str | Personal push service, e.g. `notify.mobile_app_flemming` |
| `receive_critical` | bool | Receives triggered/smoke/water/pending alerts |
| `receive_alerts` | bool | Receives low battery, arm failure alerts |
| `receive_own_actions` | bool | Receives own arm/disarm confirmations |
| `tts_quiet_start` | int | Hour to start TTS silence (0-23) |
| `tts_quiet_end` | int | Hour to end TTS silence (0-23) |

### Actions Tab — Redesigned
- System Notifications: compact 3-column grid, always-on (no toggle)
- Custom Notifications: separate section with Add button
- Notification cards: name + channel badges + trigger badge only

### Frontend — Dialog System Rebuilt
- `_attachDialogListeners()` — separate method, called once per dialog build, never from `_attachTabListeners()`
- `_rebuildDialog()` — forces dialog rebuild with fresh listeners (used by add/remove/toggle)
- All `_open*Config()` functions reset `currentDialog` before render — ensures listeners are always fresh
- `_ttsTestRunning` guard — prevents duplicate WS calls from play button
- Module save toast: now says "Active immediately." (was incorrectly "Restart HA to activate")
- Health subscription: moved from `set hass` (called per state-update = 169×) to `_loadData` (called once)
- `_healthSubscribePending` race condition guard added

### Scheduled Tests
- Backend: `async_track_time_interval` checks every minute. Supports `weekly`, `interval`, `daily` modes.
- Frontend: Add/Edit dialog in `shell-dialog-mount`, `_schedSaving` double-submit guard
- `vol.Optional("test_id", default="")` — empty string for new entries

---

## Version History

### v1.2.0 — Security & Stability (2026-03-22)
**Backend security upgrades + notification system overhaul + TTS multi-service**

#### Security
- bcrypt user PIN hashing (10 rounds, base64). `authenticate_user()` with ThreadPoolExecutor.
- `MigratableStore` v2 — schema migration from v1, sensor_groups added, per-sensor fields backfilled.

#### Sensor features
- Sensor groups (anti-masking): N sensors must activate within timeout. Full CRUD WS API.
- Per-sensor `entry_delay`, `auto_bypass`, `arm_on_close`.

#### Integration
- Mobile push actions: `mobile_app_notification_action` handler for ARM/DISARM/FORCE_ARM.
- `identify_user()` / `identify_user_id()` — user name and ID resolved from bcrypt code.
- `armed_by_id` / `disarmed_by_id` passed in alarm events.

#### Frontend
- Cancel fixed in all 6 module dialogs.
- Sensor list: 2-line layout.
- All `.py` files version-bumped to 1.2.0.

#### Tests
- 52 new tests in `test_v1_2_0.py`
- Total: **287 tests** passing on Python 3.11 + 3.12

---

### v1.1.0 — Features (2026-03-16)
- Environmental sensors section (smoke/gas/moisture, always-on, orange badge)
- TTS multi-service support
- Sensor hide/exclude
- User → person tracker binding
- Fake Presence toggle
- Home Alone Monitor camera selector
- Edit User dialog with pre-populated fields

### v1.0.0 — Production Release (2026-03-15)
- HACS submission checklist completed
- End-to-end manual testing passed
- 235 unit tests passing

---

## Architecture Overview

### Backend (Python)
| File | Role |
|---|---|
| `coordinator.py` | DataUpdateCoordinator, state machine, push handler, user identification, scheduled tests |
| `state_machine.py` | Alarm states, entry/exit delays, auto-reset, race-safe async lock |
| `zones.py` | Zone management, sensor groups, auto_bypass, arm_on_close, debouncing |
| `store.py` | Versioned storage (v2), bcrypt, sensor groups CRUD, migration, user notification fields, scheduled tests |
| `websocket_api.py` | 35+ WS endpoints incl. test_tts, sensor_groups, scheduled_tests |
| `module_manager.py` | Module lifecycle |
| `modules/tts.py` | Custom messages, MP3, tts.*/notify.*/script.* service support, volume control, announce_system() |
| `modules/base.py` | Retry + degraded state, exponential backoff, direct persistent_notification import |
| `modules/` | Camera, Lock, Lights, Climate, Siren — retry + degraded state |
| `system_health.py` | Health metrics, severity-weighted scoring |
| `notification_dispatcher.py` | User-routed dispatch: armed→acting user, triggered→broadcast, quiet hours |

### Frontend (Vanilla JS, ~5900 lines)
| Tab | Status |
|---|---|
| Sensors | Done — 2-line layout, env section collapsible, hide/exclude |
| Zones | Done |
| Users | Done — person binding, notification settings, quiet hours |
| Modules | Done — 6 modules, Lights: steady white + multi-select picker, all dialogs fixed |
| Actions / Notifications | Done — system/custom split, 3-column grid, user-routed |
| Actions / Automations | Done |
| Test | Done — severity scoring, module + sensor tests, scheduled tests |
| Future | In progress — Home Alone Monitor |

### Dialog Architecture
- `shell-dialog-mount` is the single mount point for all dialogs
- `data-currentDialog` tracks what's open — dialog only rebuilds when type changes
- `_attachDialogListeners()` called once per build — no listener accumulation
- `_rebuildDialog()` used when dialog content changes (e.g. adding a TTS message)

---

## Known Issues (v1.2.0)
| Issue | Status |
|---|---|
| TTS double playback via `script.ultra_tts` | Fixed — single-attempt tts.speak |
| Health subscription fires 169x at startup | Fixed — moved to `_loadData`, 2x remaining (two panel mounts) |
| Dialog buttons dead after re-open | Fixed — `currentDialog` reset on every `_open*Config()` call |
| Module save said "Restart HA" | Fixed — now says "Active immediately" |
