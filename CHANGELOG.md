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
