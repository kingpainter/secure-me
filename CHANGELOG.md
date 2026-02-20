# Changelog - Secure Me

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.3.6] - 2026-02-20

### Phase 3b Complete - Version Consistency & CI/CD

#### Added
- `validate_version.py` — version consistency checker for all 26 files
- GitHub Actions: new `Version Consistency` job in `validate.yaml`
- Auto-fix mode: `python3 validate_version.py --fix`

#### Fixed
- F9: Version mismatch across all files — all 26 files now consistently at 0.3.6
- `const.py` VERSION constant was 0.3.2 (now 0.3.6)
- `panel.py` VERSION constant was 0.3.2 (now 0.3.6)

---

## [0.3.5] - 2026-02-20

### Sprint 3 - Test Logic Accuracy

#### Fixed
- F7: Enabled modules with 0 entities now report `warning` instead of `pass`
  - Warning message: "Module is enabled but has no entities configured"
  - Overall test result becomes `warning`, not `fail` — system still works
- F8: Battery discovery now actually runs during test execution (was missing entirely)
  - Batteries shown in test results as informational section
  - Explicit note: battery status never affects PASS/FAIL
  - Low/critical battery counts displayed in test results

#### Changed
- Test summary now includes `warned` count alongside passed/failed/skipped
- `_renderTestResult` frontend shows `WARN` status in orange with actionable message
- Overall test result: `fail` > `warning` > `pass` (warning never blocks pass)

---

## [0.3.4] - 2026-02-20

### Sprint 2 - Visual Consistency & SVG Icons

#### Added
- 5 new SVG icons: `ok`, `warn`, `fail`, `close`, `circle`
- `dots` icon for mobile More button
- CSS for proper inline SVG icon sizing across all contexts

#### Fixed
- F3: All HTML entities replaced with proper SVG icons
  - `&#128737;` → `icon('shield')`
  - `&#128100;` → `icon('user')`
  - `&#9989;/&#9888;/&#10060;` → `icon('ok'/'warn'/'fail')`
  - `&#10005;` → `icon('close')` with hover styling
  - `&#10003;/&#10007;` → `icon('check'/'fail')`
- F4: Corrupted bullet characters (`â€¢` × 7) replaced with `icon('chevron')`
- Corrupted POE label (`Â¢ POE:`) fixed to plain `POE:`
- Dialog close buttons now use SVG with proper CSS hover state
- `_renderPlaceholder` converted from emoji parameter to icon name
- Badge text "aktive" → "active"

#### Changed
- `placeholder-icon` CSS uses SVG sizing instead of font-size

---

## [0.3.3] - 2026-02-20

### Sprint 1 - Mobile Navigation & Critical Sync Fixes

#### Added
- Mobile Bottom Navigation Bar (≤768px)
  - Fixed bottom bar with 5 primary tabs: Sensors, Zones, Users, Modules, Actions
  - "More" button opens slide-up drawer for Test and Future tabs
  - Active tab indicator: green accent line + icon scale
  - iOS safe-area support (`env(safe-area-inset-bottom)`)
- Mobile top header with logo and alarm status pill
- `dots` SVG icon for More button

#### Fixed
- F1: `_get_module_entity_ids()` now checks all attribute names correctly
  (`poe_switches`, `cameras`, `locks`, `lights`, `climates`, `media_players`)
- F2: Health status sync between panel WebSocket and binary sensors
- F5: Camera module config structure — checks `entities` key as fallback
- F6: TTS module now included in system health checks

#### Changed
- Desktop sidebar completely unchanged
- Mobile: sidebar hidden, replaced by top header + bottom nav

---

## [0.3.2] - 2026-02-14

### Phase 3 Complete - Test Suite Fixed

#### Fixed
- `test_init_.py` removed (deprecated tests)
- Version checks updated to 0.3.2 in all test files
- `hacs.json` path fixed in `test_files.py` (repo root, not integration dir)
- `conftest.py` fixtures completed

#### Status
- 100/100 unit tests passing
- GitHub Actions: HACS 7/8, Hassfest all, Pytest 3.11+3.12 all green

---

## [0.3.1] - 2026-02-13

### System Health, Diagnostics & Panel Registration

#### Added
- System health integration (10 health metrics)
- Enhanced diagnostics (6 sections)
- Panel registration via `panel.py` module (Alarmo-style)
- `panel_custom` dependency in `manifest.json`

#### Fixed
- All emojis removed from frontend and backend (UTF-8 safety)
- 5 critical bugs (F1-F5) applied

---

## [0.3.0] - 2026-02-13

### Phase 3 - Testing Framework & Health Monitoring

#### Added
- Three-tier testing framework (Quick ~30s / Standard ~60s / Full ~90s)
- Module health monitoring with binary sensors
- Battery level tracking with auto-discovery
- Testing tab in configuration panel
- WebSocket test API (`run_test`, `get_test_results`)
- Test result persistence (last 10 results)
- Health scoring system

---

## [0.2.0] - 2026-02-04

### Phase 2 - All 6 Smart Modules

#### Added
- Camera module — POE control, recording management
- Lock module — smart lock with retry logic
- Lights module — auto control, emergency flash patterns
- Climate module — multi-zone heating/cooling
- Siren module — alarm sounds with patterns
- TTS module — Danish voice notifications
- Module manager for coordination
- Base module class

---

## [0.1.0] - 2026-02-03

### Phase 1 - Core Logic

#### Added
- DataUpdateCoordinator
- State machine with entry/exit delays
- Zone manager with trigger callbacks
- Code validation
- State tracking (armed_by, disarmed_by, triggered_by)
- Sensor monitoring infrastructure

---

## [0.0.1] - 2026-02-01

### Phase 0 - Foundation

#### Added
- Integration framework
- Config flow setup
- Manifest, constants, translations (EN + DA)
- GitHub Actions CI/CD
- MIT License
