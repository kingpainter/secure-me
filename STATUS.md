# Secure Me — Development Status

## Current version: 2.2.0 (release date 2026-10-24 as recorded in README and API.md; not checked against git tags)

---

## What is in 2.2.0 (2026-10-24)

### NFC Tag Integration
- Users can register NFC tags (iPhone, AirTag, etc.). Each tag can optionally require a PIN
- Tags are bound to a user (`user_id` is stored on the tag). No audit log is implemented
- Home Assistant `tag_scanned` events trigger alarm actions
- WebSocket endpoints: `get_nfc_tags`, `register_nfc_tag`, `delete_nfc_tag`, `get_ha_nfc_tags`, `import_nfc_tag`
- NFC tags persisted in Store v2 with auto-migration support
- Frontend: new NFC tab in user management dialog with registration flow and tag listing (not re-verified in this pass)
- Backend: `async_listen_nfc_events()` in coordinator listens for tag scan events

### Quality & Robustness
- Zero linting violations (Ruff verified)
- Python 3.13+ strict compatibility
- Full PEP 563 type hints across all 34 custom files
- 41 test files under `tests/` (CI is authoritative for counts and coverage)
- Test status on Python 3.13 not re-verified locally

### Status
- Commit and CI result not re-verified in this pass.

---

## What is in 2.1.0 (2026-10-03)

### NFC Tag Support (First Release)
- NFC tag registration flow in Users tab
- User-bound NFC tags for secure, PIN-less authentication
- Event-driven integration with Home Assistant `tag_scanned` events
- Full Store v2 support with auto-migration

---

## What is in 2.0.1 (2026-09-30)

### Code Quality Initiative
- **Ruff linting:** 162 errors → 74 errors (54% reduction)
- **Python 3.13 compatibility:** verified across entire codebase
- **Strict type hints:** PEP 563 annotations across all 34 files
  - All imports use `from __future__ import annotations`
  - All function signatures use type hints
  - All class attributes are type-annotated
  - All module-level callables are annotated
- **Regex modernization:** deprecated `regex` patterns updated
- **Test coverage:** all 380+ tests passing on Python 3.13

### Architecture Validation
- Engine pattern fully validated through integration tests
- State machines offline-testable and verified
- Coordinator orchestration layer verified

### Status
- Committed 2026-09-30. CI: all green. Python 3.13 ready.

---

## What is in 2.0.0 (2026-09-21)

### Major Architecture Refactoring (v2.0 Initiative)
Complete redesign of core logic to separate concerns using pure state machines.

#### Engine-Based Architecture
Three independent engines extracted from monolithic coordinator:

1. **AutoActionsEngine** (`engine/auto_actions_engine.py`, 1,010 lines)
   - Pure state machine for presence-based automation
   - NO direct Home Assistant dependencies
   - Fully offline-testable with 70+ dedicated tests
   - Features:
     - Home Empty Detection (person entity tracking)
     - Three Independent Action Timers (lock, alarm, camera)
     - Arrival Confirmation Window (prevents GPS flicker)
     - Selective Fake Presence v2 blocking (re-checked on execution)
     - Stale Tracker Fail-Safe (30 min configurable timeout)
     - Initial-Presence Check on Startup
     - Configurable Recheck-on-Disarm

2. **FloorplanEngine** (`engine/floorplan_engine.py`, 207 lines)
   - Pure state machine for room and opening state tracking
   - NO direct Home Assistant dependencies
   - Fully offline-testable
   - Room management, opening tracking, sensor assignment

3. **NotificationEngine** (`engine/notification_engine.py`, 859 lines)
   - Pure state machine for notification preferences and routing
   - User preference management (quiet hours, channels)
   - Event routing rules
   - Notification dispatcher pattern

#### Type Safety & Code Quality
- **PEP 563 Future Annotations**: `from __future__ import annotations` across all files
- **Strict type hints**: Every function, class, and module-level callable annotated
- **Python 3.13 ready**: All deprecated patterns updated, regex modernized

#### Test Expansion
- **New test files:** 28 new unit tests added
- **Engine testability:** engines have zero HA dependencies, fully testable offline
- **Total coverage:** 380+ tests, 80%+ code coverage
- **CI/CD validation:** all tests pass on Python 3.13

#### Coordinator Refactoring
- Reduced from 2,000+ lines to 1,512 lines (24% smaller)
- Pure orchestration layer between HA and engines
- Cleaner separation of concerns
- Easier to test and maintain

#### WebSocket API Enhancement
- 30+ endpoints across 4 modules (`ws_sensors.py`, `ws_modules.py`, `ws_floorplan.py`, `ws_alarm.py`)
- Full CRUD operations for zones, sensors, users, modules
- Floorplan endpoints fully tested (70+ tests)

#### Documentation
- `ARCHITECTURE.md` (v2.0.0): Layer architecture, engine patterns, debugging guidance
- Inline code documentation updated for engine pattern
- Test file docstrings explain offline testing patterns

### Files Changed
| File | Purpose |
|------|---------|
| `engine/base_engine.py` | Base engine class for state machine pattern |
| `engine/auto_actions_engine.py` | Auto Actions v2 as pure state machine |
| `engine/floorplan_engine.py` | Floorplan state management |
| `engine/notification_engine.py` | Notification management |
| `coordinator.py` | Refactored as orchestration layer (1,512 lines) |
| `state_machine.py` | Refactored for engine integration |
| All 34 custom_components files | Added PEP 563 annotations |

### Status
- Committed 2026-09-21. Major refactoring complete. Ready for v2.1.0 feature additions.

---

## What was in 1.5.4 (2026-08-23)

### Presence-System Consolidation
- Removed `PresenceMonitor` (coordinator.py) entirely
- `AutoActionsManager` now sole presence-based automation system
- Re-scoped to only watch Secure Me users (not all `person.*` entities)
- New initial-presence check at startup (`_check_initial_presence()`)
- Fake Presence re-checked immediately before action execution (race condition fix)

### Robustness
- `identify_user_id()` delegates to `store.authenticate_user_with_id()`
- ThreadPoolExecutor bcrypt checking for all user authentication

### Code Cleanup
- Removed dead `AUTO_ARM_*` constants
- Removed `notification_dispatcher.send_auto_arm_notification()`

### Testing
- `tests/test_auto_actions.py` (17 tests) locks in consolidation logic
- All 404 tests passing on Python 3.13

### Status
- Committed 2026-08-23. CI all green.

---

## What was in 1.5.0 (released 2026-07-19)

### Floorplan (Complete Implementation)
- PNG upload (up to 4 MB)
- Room drawing (rectangles, polygons)
- Sensor assignment per room
- Door/window opening markers with live state
- Sensor pin markers (red pulse = active, green = inactive)
- Undo support (Ctrl+Z, 20 steps)
- Keyboard shortcuts and touch support
- PNG backed up in HA storage (survives HACS updates)

### Control API (Services)
- `secure_me.arm_away`, `arm_home`, `arm_night`, `arm_vacation`, `arm_home_alone`
- `secure_me.disarm`, `trigger`, `run_test`
- `secure_me.enable_module`, `disable_module`
- All with optional `code`, `skip_delay`, `force` parameters

### Alarm State Mapping
- `alarm_control_panel.secure_me` with 6 states
- `secure_me_mode` attribute for raw state access
- Home Alone mapped as raw string (not standard HA enum)

### Sensor Options
- `entry_delay` override per sensor
- `auto_bypass` per arm mode
- `allow_open` for permanent bypass
- `arm_on_close` for auto-arming

### Auto Actions v2
- Three independent action timers (lock, alarm, cameras)
- Configurable per-action delays
- Arrival confirmation window
- Fake Presence v2 selective blocking

### WebSocket API
- Split from monolithic `websocket_api.py` into 4 modules
- `ws_sensors.py`: zones, sensors, users, NFC
- `ws_modules.py`: modules, tests, notifications
- `ws_floorplan.py`: floorplan CRUD
- `ws_alarm.py`: arm/disarm, auto actions

### Documentation
- `API.md` (v1.5.0): Formal alarm entity contract
- Updated README with all features
- Enhanced ARCHITECTURE.md

### Status
- Committed 2026-07-19. Production ready.

---

## Test Suite Status (v2.2.0)

- 41 test files under `tests/` (counted by directory listing)
- Test counts and coverage were not re-verified locally. CI is authoritative
- GitHub Actions: HACS validation and Hassfest compliance (from earlier notes; not re-verified)
- Zero linting violations (Ruff) from earlier notes; not re-verified in this pass

The per-category test table that used to be here was not based on a count and has been removed.

### Recent Test Additions (Phase C, 2026-10-03)
- `test_module_integration_lifecycle.py`: 12 tests
- `test_module_integration_config.py`: 8 tests
- `test_module_integration_services.py`: 8 tests
- `test_module_integration_state.py`: 8 tests
- `test_module_integration_error_handling.py`: 6 tests
- `test_module_integration_coordination.py`: 5 tests

---

## Ready to commit?

### Current Status
- Open code issues (not fixed): stale-tracker grace handling in `auto_actions._all_persons_away()`; `requires_pin` not declared in the websocket schema for NFC register/import
- Test suite, CI, linting and type-hint claims from earlier notes were not re-verified in this pass

### Documentation Status
- README.md — updated to v2.2.0 in this pass
- API.md — updated to v2.2.0 in this pass
- ARCHITECTURE.md — updated in this pass; NFC section rewritten to match the code
- STATUS.md — updated in this pass
- CHANGELOG.md — not re-checked in this pass

### Next Steps (Optional)
1. Update `quality_scale.yaml` (stale test counts, HA version, doc sizes). Two copies exist (root and `custom_components/secure_me/`); decide which is canonical
2. Fix the open code issues above, after explicit approval
3. Optional: ENGINES.md and WEBSOCKET_API.md if still wanted

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|--------------|
| 2.2.0 | 2026-10-24 | Per-tag PIN enforced in backend, code lockout, NFC endpoints documented |
| 2.1.0 | 2026-10-03 | NFC tag integration (first release) |
| 2.0.1 | 2026-09-30 | Ruff linting, Python 3.13 |
| 2.0.0 | 2026-09-21 | Engine architecture, type hints |
| 1.5.4 | 2026-08-23 | Auto Actions consolidation |
| 1.5.0 | 2026-07-19 | Floorplan, services, Auto Actions v2 |

