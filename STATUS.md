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
| Pytest Python 3.11 | 235/235 passed |
| Pytest Python 3.12 | 235/235 passed |
| Version Consistency | Passed |

---

## Version History

### v1.2.0 — Security & Stability (2026-03-22)
**Alarmo-inspired backend upgrades + dialog fixes**

#### Backend
- **bcrypt user code hashing** — PIN codes hashed with bcrypt (10 rounds, base64). Legacy plaintext migrated transparently on next save. ThreadPoolExecutor for parallel code checks.
- **MigratableStore v2** — Versioned storage with `STORAGE_VERSION_MAJOR=2`. Auto-migration from v1: `sensor_groups` added, per-sensor fields backfilled, legacy codes flagged for re-hash.
- **Sensor groups (anti-masking)** — Alarm only triggers if N sensors activate within a time window. Prevents false alarms from single sensor glitch. Full CRUD via WebSocket API.
- **Per-sensor `entry_delay`** — Override zone default delay per sensor.
- **Per-sensor `auto_bypass`** — Open sensors silently bypassed at arm time instead of blocking.
- **Per-sensor `arm_on_close`** — Auto-arm (away mode) when sensor closes (e.g. front door shut).
- **Mobile push notification actions** — `mobile_app_notification_action` handler: ARM_AWAY, ARM_HOME, ARM_NIGHT, ARM_VACATION, DISARM, FORCE_ARM, RETRY_ARM directly from HA Companion push buttons.
- **`bcrypt>=4.0.0`** added to `manifest.json` requirements and `requirements.txt`.

#### Frontend
- **Cancel fixed in all 6 module dialogs** — Root cause: `_cancelDialog` required a confirm dialog that was blocked by inline `z-index:99999` overlays on Lock, Climate and Lights. Now closes directly without confirmation.
- **Lock, Climate, Lights dialogs standardized** — Converted from inline `position:fixed` styles to `config-dialog-overlay` CSS class. All 6 module dialogs now use the same structure.
- **Close-X buttons fixed** — 3 empty `<button>` elements now have `${icon("close")}`.
- **Sensor list readability** — 2-line row layout: name + badge + checkbox on line 1, entity_id truncated on line 2. Replaces cramped single-line grid layout.
- **Encoding artifacts removed** — `Â\xa0` and `Â ` UTF-8 corruption cleaned from all dialog HTML.

#### Tests
- 52 new tests in `test_v1_2_0.py`
- `test_store.py` updated for v2 schema (`sensor_groups` key)
- Total: **287 tests** passing on Python 3.11 + 3.12

---

### v1.1.0 — Features (2026-03-16)
- Environmental sensors section (smoke/gas/moisture, always-on, orange badge)
- TTS multi-service support (dropdown: cloud_say, google_translate_say, piper, etc.)
- Sensor hide/exclude functionality
- User → person tracker binding
- Fake Presence toggle (blocks auto-arm)
- Home Alone Monitor camera selector
- Edit User dialog with pre-populated fields
- Dialog blink-on-render bug fixed (`data-currentDialog` tracking)
- SVG icon sizing fixed (all 24 icons explicit dimensions)

---

### v1.0.0 — Production Release (2026-03-15)
- HACS submission checklist completed
- End-to-end manual testing passed
- Frontend panel flickering resolved
- Logo/branding submitted to HA brands repository
- 235 unit tests passing

---

## Architecture Overview

### Backend (Python)
| File | Role |
|---|---|
| `coordinator.py` | DataUpdateCoordinator, state machine orchestration, push notification handler |
| `state_machine.py` | Alarm states, entry/exit delays, auto-reset, race-safe async lock |
| `zones.py` | Zone management, sensor groups, auto_bypass, arm_on_close, debouncing |
| `store.py` | Versioned storage (v2), bcrypt, sensor groups CRUD, migration |
| `websocket_api.py` | 35+ WS endpoints for all frontend operations |
| `module_manager.py` | Module lifecycle |
| `modules/` | Camera, Lock, Lights, Climate, Siren, TTS — retry + degraded state |
| `system_health.py` | 10 health metrics, severity-weighted scoring |
| `notification_dispatcher.py` | Alarm event → notify service dispatcher |

### Frontend (Vanilla JS)
| Feature | Status |
|---|---|
| Sensors tab | Done — 2-line layout, env section, hide/exclude |
| Zones tab | Done |
| Users tab | Done — person binding, bcrypt-aware |
| Modules tab | Done — 6 modules, all dialogs fixed |
| Actions tab | Done — notifications + automations |
| More tab | Done — testing dashboard, fake presence, home alone |

---

## Known Gaps vs Alarmo (tracked for future versions)
| Feature | Priority | Target |
|---|---|---|
| Per-sensor `delay_on` (debounce at sensor level) | Medium | v1.3.0 |
| MQTT support | Low | v1.4.0 |
| 5 arm modes (vacation fully wired in UI) | Low | v1.3.0 |

---

## Next Steps
- [ ] Commit sensor readability patch + dialog fixes to GitHub
- [ ] Commit v1.2.0 backend to GitHub  
- [ ] Manual test: Cancel in all 6 module dialogs
- [ ] Manual test: bcrypt — create user, restart HA, verify code still works
- [ ] Manual test: Sensor group — add 2 sensors to group, verify single trigger does not alarm
- [ ] HACS brands PR (separate repo)
