# Secure Me — Project Status

**Last updated:** 2026-03-22
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
| Pytest Python 3.12 | All passed |
| Version Consistency | Passed |

---

## Active Development (v1.2.0 — ongoing)

### TTS Module — Rebuilt
- System messages (armed/disarmed/triggered/countdown) removed from TTS module — now belongs to Notifications
- `media_players` is now optional — works without players if using custom TTS service
- Custom messages list with per-message: trigger, type (tts/media), text/URL, enabled toggle
- MP3/media file support via `media_player.play_media`
- New `announce_system()` method — called by notification dispatcher for TTS channel
- Test button per custom message

### Notification System — User-Routed
- **Channels per notification:** `push`, `tts`, or both
- **User-routed arm/disarm:** `armed_by_id` / `disarmed_by_id` tracked in coordinator. Armed → only the arming user gets confirmation. Disarmed → only the disarming user gets confirmation.
- **Broadcast triggers:** `triggered` and `pending` sent to all users with `receive_critical=True`. Smoke/water_leak always broadcast critical.
- **Low battery** sent to all users with `receive_alerts=True`
- **Test notifications** routed to admin users only (by `notify_service` on user). Falls back to notification service if no admins configured.
- **TTS quiet hours** per user — `tts_quiet_start` / `tts_quiet_end` (hour 0-23). TTS suppressed during quiet period.

### User Notification Settings (new fields on each user)
| Field | Type | Description |
|---|---|---|
| `notify_service` | str | Personal push service, e.g. `notify.mobile_app_flemming` |
| `receive_critical` | bool | Receives triggered/smoke/water/pending alerts |
| `receive_alerts` | bool | Receives low battery, arm failure alerts |
| `receive_own_actions` | bool | Receives own arm/disarm confirmations |
| `tts_quiet_start` | int | Hour to start TTS silence (0-23) |
| `tts_quiet_end` | int | Hour to end TTS silence (0-23) |

### Actions Tab — Redesigned
- **System Notifications** section — compact 3-column grid, no toggle (always-on), subtitle: "Always active — routed per user. Test sends to admin users only."
- **Custom Notifications** section — separate grid below with Add button
- Notification cards: name + channel badges + trigger badge only — no message text in card
- Add/Edit notification dialog with channel selector (push + TTS toggle)

### Frontend — User Dialog Extended
- Notification Settings section added to User dialog
- Push notify service dropdown (loads from HA)
- Checkboxes: receive critical / receive alerts / receive own actions
- TTS quiet hours (from/to hour inputs)
- User cards show badges: notify service name, Critical badge, quiet hours range

---

## Version History

### v1.2.0 — Security & Stability (2026-03-22)
**Backend security upgrades + notification system overhaul**

#### Security
- bcrypt user PIN hashing (10 rounds, base64). `authenticate_user()` with ThreadPoolExecutor.
- `MigratableStore` v2 — schema migration from v1, sensor_groups added, per-sensor fields backfilled.

#### Sensor features
- Sensor groups (anti-masking): N sensors must activate within timeout. Full CRUD WS API.
- Per-sensor `entry_delay`, `auto_bypass`, `arm_on_close`.

#### Integration
- Mobile push actions: `mobile_app_notification_action` handler for ARM/DISARM/FORCE_ARM.
- `identify_user()` / `identify_user_id()` — user name and ID resolved from bcrypt code on arm/disarm.
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
| `coordinator.py` | DataUpdateCoordinator, state machine, push handler, user identification |
| `state_machine.py` | Alarm states, entry/exit delays, auto-reset, race-safe async lock |
| `zones.py` | Zone management, sensor groups, auto_bypass, arm_on_close, debouncing |
| `store.py` | Versioned storage (v2), bcrypt, sensor groups CRUD, migration, user notification fields |
| `websocket_api.py` | 35+ WS endpoints incl. test_tts, sensor_groups |
| `module_manager.py` | Module lifecycle |
| `modules/tts.py` | Custom messages, MP3 support, optional media_players, announce_system() |
| `modules/` | Camera, Lock, Lights, Climate, Siren — retry + degraded state |
| `system_health.py` | Health metrics, severity-weighted scoring |
| `notification_dispatcher.py` | User-routed dispatch: armed→acting user, triggered→broadcast, quiet hours |

### Frontend (Vanilla JS, ~5400 lines)
| Tab | Status |
|---|---|
| Sensors | Done — 2-line layout, env section, hide/exclude |
| Zones | Done |
| Users | Done — person binding, notification settings, quiet hours |
| Modules | Done — 6 modules, all dialogs fixed, TTS rebuilt |
| Actions / Notifications | Done — system/custom split, 3-column grid, user-routed |
| Actions / Automations | Done |
| Test | Done — severity scoring, module + sensor tests |
| Future | In progress — Home Alone Monitor |

---

## Known Gaps (tracked for future versions)
| Feature | Priority | Target |
|---|---|---|
| Per-sensor `delay_on` debounce | Medium | v1.3.0 |
| 5 arm modes fully wired in UI (vacation) | Low | v1.3.0 |
| MQTT support | Low | v1.4.0 |

---

## Next Steps
- [ ] Manual test: User notification settings — arm as Flemming, verify only Flemming gets push
- [ ] Manual test: TTS quiet hours — set 22-07, verify TTS silent at night
- [ ] Manual test: Triggered → broadcast — verify all users with receive_critical get notified
- [ ] Manual test: TTS custom message — add "Politiet er tilkaldt", arm/trigger, verify playback
- [ ] Manual test: Test notification button → only admins receive
- [ ] HACS brands PR (separate repo)
- [ ] Version bump to v1.3.0 when above tests pass
