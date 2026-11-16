# Secure Me — Architecture & Design

**Version:** 2.2.0  
**Date:** 2026-11-16  
**Status:** Production Ready (v2.2.0)

---

## 1. Overview

Secure Me is a multi-zone Home Assistant alarm system designed around **pure state machines** and **engine-based architecture**. All state logic is decoupled from Home Assistant dependencies, enabling offline unit testing and maintainability.

Version 2.2.0 adds **NFC tag control** (each tag can optionally require a PIN) while keeping the engine pattern. Test counts are in CI.

### Core Design Principles

1. **State Machine as Source of Truth** — All state transitions (arm, disarm, trigger) are explicit, testable events
2. **Engine Pattern** — Extracted logic into standalone, injectable state machines (`BaseEngine`)
3. **Minimal HA Coupling** — Engines operate independently; only coordinators bridge to HA
4. **Testability First** — engine tests run without an HA instance (coverage: see CI)
5. **Async-Only I/O** — No blocking calls; full `asyncio` compliance
6. **Security by Default** — bcrypt PIN hashing, optional per-tag PIN, code lockout after repeated failures

---

## 2. Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Home Assistant Core                                         │
│ • Event Bus (state_changed, custom events, tag_scanned)   │
│ • Service Registry (arm_away, trigger, etc.)              │
│ • Entity Management (entity registry, device registry)    │
│ • Tag Scanning (NFC tag_scanned events)                   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ async callbacks
                            │
┌─────────────────────────────────────────────────────────────┐
│ Coordinator Layer (HA Bridge)                              │
│ • coordinator.py — Orchestration            │
│ • module_dispatch.py — Module instantiation   │
│ • Services entry point (hass.services.async_register)    │
│ • NFC event listener (async_listen_nfc_events)           │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ direct method calls
                            │
┌─────────────────────────────────────────────────────────────┐
│ State Machine Engine Layer (Pure Logic)                    │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ BaseEngine                               │  │
│ │ • async_start(), async_stop(), cleanup             │  │
│ │ • Task lifecycle management                         │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ AutoActionsEngine (offline copy)                      │  │
│ │ • Presence-based automation                         │  │
│ │ • Tracks person entities (home/away state)         │  │
│ │ • Manages lock/alarm/camera action delays          │  │
│ │ • Arrival confirmation + fake presence blocking    │  │
│ │ • Stale tracker timeout (30 min, configurable)     │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ FloorplanEngine                          │  │
│ │ • Room & opening state tracking                     │  │
│ │ • Live-view coordinates                             │  │
│ │ • No HA dependencies                                │  │
│ │ • Sensor pin markers (active/inactive states)       │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ NotificationEngine                       │  │
│ │ • Event routing rules                               │  │
│ │ • User preferences (quiet hours, channels)          │  │
│ │ • Dispatcher pattern for delivery                   │  │
│ │ • Multi-language support (DA/EN)                    │  │
│ └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ injected via __init__
                            │
┌─────────────────────────────────────────────────────────────┐
│ Infrastructure Layer                                        │
│ • StateMachine (alarm state enum, entry/exit delays)      │
│ • ZoneManager (sensor debouncing, grouping)               │
│ • Store v2 (bcrypt, NFC tags, data persistence)           │
│ • ModuleDispatcher (6 module factories + health scoring)  │
│ • NFC tags stored in Store (top-level nfc_tags)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Engine Architecture

### 3.1 BaseEngine Pattern

All engines inherit from `BaseEngine`, providing a consistent lifecycle:

```python
class BaseEngine:
    """Base class for all Secure Me state machines."""
    
    async def async_start(self) -> None:
        """Start the engine: initialize timers, listeners, state."""
        
    async def async_stop(self) -> None:
        """Stop the engine: cancel all tasks, cleanup."""
        
    async def async_cleanup(self) -> None:
        """Final cleanup before removal."""
```

**Benefits:**
- Uniform startup/shutdown across all engines
- Task tracking prevents orphaned coroutines
- Testable without HA instance
- Zero HA dependencies in engine implementation

### 3.2 Auto Actions

**Runtime:** `AutoActionsManager` in `auto_actions.py` is what the coordinator uses. `engine/auto_actions_engine.py` is a standalone copy of the same logic without HA dependencies, used for offline tests. The table below describes `AutoActionsManager`.

**Purpose:** Presence-based automation — arm/disarm/lock/camera actions triggered by person entity state changes.

**Key Components:**

| Method | Purpose |
|--------|---------|
| `_on_home_empty()` | Entry point: all persons went away |
| `_all_persons_away()` | Check if all tracked persons are `not_home` (fail-safe if tracker stale) |
| `_run_action_after_delay()` | Queue lock/alarm/camera actions with per-action delays |
| `_execute_action()` | Dispatch to `_do_lock()`, `_do_alarm()`, `_do_camera()` in `auto_actions.py` |
| `_cancel_all_action_tasks()` | User returns home: cancel all queued actions |
| `_send_summary_notification()` | Report action results to user |

**State:** `_tracker_entities`, `_action_tasks`, `_done_actions`, `_action_results`, `_tracker_stale_since`, `_all_away_since`

**Configuration Parameters:**
- `lock_delay` (int, seconds) — Delay before auto-locking (default: 120)
- `alarm_delay` (int, seconds) — Delay before auto-arming (default: 300)
- `camera_delay` (int, seconds) — Delay before activating cameras (default: 0)
- `stale_tracker_timeout` (int, seconds) — GPS tracker unavailability threshold (default: 1800)
- `arrival_confirmation_delay` (int, seconds) — Wait before confirming arrival (default: 60)

**Input Events:**
- `state_changed` (hass event bus): a tracker of a Secure Me user changed state
- `secure_me_disarmed` event: optional recheck (only when `recheck_on_disarm` is on)
- asyncio timers: per-action delays and the arrival confirmation window

**Output:**
- Coordinator call: `coordinator.async_arm_away(skip_delay=True)`. Lock goes through the lock module's retrying service call. Camera goes through `CameraModule.async_arm("away")`
- User notifications: one summary when all scheduled actions have settled
- HA events: `secure_me_home_empty`, `secure_me_person_home`, `secure_me_auto_action_done`

**Offline Testability:** the `engine/` copy has no HA dependencies. `AutoActionsManager` in `auto_actions.py` does import HA and is not offline-testable  
**Test Files:** 
- `test_auto_actions_engine.py` (2 tests)
- `test_auto_actions_engine_extended.py` (9 tests)
- `test_auto_actions_engine_full.py` (11 tests)
- `test_auto_actions_engine_timer_expansion.py` (25+ tests)
- `test_auto_actions_reliability.py` (17 tests)

---

### 3.3 FloorplanEngine

**Purpose:** Room & opening state tracking for live-view visualization.

**Key Components:**

| Component | Purpose |
|-----------|---------|
| `load_state(config)` | Load room/opening definitions from store |
| `update_opening_state(room_id, opening_id, is_open)` | Sensor update triggers opening state change |
| `get_room_status(room_id)` | Return room's current open/closed status |
| `get_state()` | Full floorplan state snapshot |
| `add_sensor_to_room()` | Link sensor to room for live glow |

**State:** `_rooms` dict, `_openings` dict, sensor→room mappings, PNG metadata

**Features:**
- PNG image storage (backed up in HA storage, auto-restored on startup)
- Room drawing (rectangles and polygons)
- Sensor pin markers with live state (red = active, green = inactive)
- Door/window opening indicators
- 20-step undo support

**Offline Testability:** ✅ Yes — zero HA dependencies  
**Test Files:** 
- `test_floorplan_engine.py` (3 tests)
- `test_floorplan_engine_full.py` (11 tests)
- `test_ws_floorplan.py` (70+ tests for WebSocket endpoints)

---

### 3.4 NotificationEngine

**Purpose:** Event routing rules + user preferences (quiet hours, do-not-disturb, channels).

**Key Components:**

| Component | Purpose |
|-----------|---------|
| `should_notify(event_type, user_id)` | Check quiet hours, preferences, criticality |
| `route_notification(event_type)` | Determine channel(s): mobile, email, dashboard, push |
| `get_notification_text(event_type, context)` | Format message (Danish preferred, fallback English) |
| `get_user_preferences(user_id)` | Return user's notification settings |
| `queue_notification()` | Enqueue message for delivery (prevents duplication) |

**Configuration Per User:**
- Quiet hours (start/end time)
- Do-not-disturb (full disable)
- Preferred channels (mobile, email, dashboard)
- Critical events always bypass quiet hours

**Offline Testability:** ✅ Yes (except HA service calls, which are injected)  
**Test Files:** 
- `test_notification_engine.py` (8 tests)
- Integration tests with coordinator

---

## 4. NFC Tag Integration

### 4.1 Flow

Secure Me listens on the Home Assistant event bus for `tag_scanned` (`coordinator.async_listen_nfc_events()`). For each event:

1. Look up `tag_id` in the top-level `nfc_tags` dict in the store. Unregistered tags are logged and ignored.
2. If the tag has `requires_pin`, the event must carry the PIN in `data.code`. A missing or wrong PIN rejects the scan. The check goes through `code_limiter`.
3. Run the tag's action. `disarm` calls `async_disarm(skip_code=True)`. `arm_away` calls `async_arm_away()`. Any other value is rejected.
4. Fire `secure_me_tag_scanned` with the outcome, whether it succeeded or not.

Secure Me does not prompt the user for a PIN and does not send a confirmation notification of its own.

### 4.2 Storage

Registered tags live at the top level of the store, keyed by `tag_id` (not nested under users). Illustrative shape:

```python
store["nfc_tags"] = {
    "04FA123456789ABC": {
        "user_id": "user_123",
        "action": "disarm",
        "name": "iPhone",
        "requires_pin": False,
        "created_at": 1761300000.0,  # Unix time
    }
}
```

### 4.3 Event

`secure_me_tag_scanned` carries `tag_id`, `tag_name`, `action`, `success`, `error`, `alarm_state`, `pin_required` and `pin_verified`. `pin_verified` is `null` when the tag does not require a PIN. The PIN itself is never put in the event or logged.

### 4.4 Security Notes

- A tag without a PIN is the credential. Disarming by tag skips the global code check (`skip_code=True`).
- Failed PIN checks count toward the code lockout in `code_attempts.py`. Tags without a PIN never reach that limiter.
- The following were described in earlier drafts of this document but are **not implemented** in the code: a PIN prompt with a 2-minute timeout, a per-user permission check, rate limiting of scans, an audit log of tag events, and a `secure_me_nfc_scanned` event.

---

## 5. Coordinator Integration

### 5.1 Coordinator's Role

`coordinator.py` is the **bridge** between engines and Home Assistant:

1. **Engine Instantiation** — Creates engine instances, passes config/store
2. **HA Event Routing** — Listens to `state_changed`, `tag_scanned`, converts to engine inputs
3. **Module Dispatch** — Calls ModuleDispatcher for siren/camera/lock/etc. execution
4. **State Machine** — Tracks alarm state (armed/disarmed/triggered)
5. **Health Scoring** — Aggregates module health into diagnostics
6. **NFC Listening** — Handles `tag_scanned` events and checks the PIN when a tag requires one

### 5.2 Startup Sequence

```
hass.setup_entry()
  → SecureMeCoordinator.__init__()    ← creates code_limiter, state_machine, zone_manager, module_dispatcher
  → coordinator.async_load_store_config(store)
    → modules, zones, sensors and sensor groups loaded from store
    → async_listen_nfc_events()        ← subscribes to tag_scanned
    → AutoActionsManager.async_start() ← subscribes to state_changed, then _check_initial_presence()
  → services registered (arm_away, disarm, trigger, ...)

(FloorplanEngine and NotificationEngine are not started by the coordinator; see section 3.)
```

### 5.3 Event Flow Example: "Person Goes Away"

```
Home Assistant Event Bus
  ↓
state_changed(entity_id="person.alice", new_state="not_home")
  ↓
coordinator._state_changed_listener()
  ↓
AutoActionsManager._handle_state_changed()
  ↓
_all_persons_away() → True (all tracked persons now away)
  ↓
_on_home_empty() ← schedules lock / alarm / camera timers, each with its own delay
  ↓
_run_action_after_delay("lock", delay)
  ↓
[delay passes, house still empty]
  ↓
_execute_action("lock")
  ↓
_do_lock() ← skips doors that are open and locks that are already locked
  ↓
lock module async_call_service_with_retry("lock", "lock", ...)
```

### 5.4 Event Flow Example: "NFC Tag Scan"

```
Home Assistant tag_scanned event (data: tag_id, optional code)
  ↓
handle_nfc_event() inside async_listen_nfc_events()
  ↓
store.get_nfc_tags()[tag_id] → action, requires_pin
  ↓
requires_pin == False → no PIN check
  ↓
async_disarm(skip_code=True)
  ↓
state_machine.disarm() → secure_me_disarmed fired by _state_changed()
  ↓
secure_me_tag_scanned fired with success=True, pin_verified=None
```

---

## 6. State Machine (Alarm States)

The `StateMachine` class manages the five alarm modes and automatic transitions:

```
                    ┌─────────────────────┐
                    │   DISARMED          │
                    └──────────┬──────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
        ┌────────────┐  ┌────────────┐  ┌────────────┐
        │ ARMED_AWAY │  │ ARMED_HOME │  │ARMED_NIGHT │
        └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
              │               │              │
              └───────────────┼──────────────┘
                              │
                    ┌─────────▼──────────┐
                    │ ARMED_VACATION    │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ ARMED_HOME_ALONE  │
                    └───────────────────┘
                    
        Any armed state
              ↓
        ┌──────────────┐
        │   TRIGGERED  │ (entry_delay countdown → alarm fires)
        └──────────────┘
              ↓
        ┌──────────────┐
        │  DISARMED    │ (manual disarm, or after trigger_time)
        └──────────────┘
```

**Key Transitions:**
- **Entry Delay** (armed_away): When sensor triggers, countdown starts (default 30s). User disarms within window → no alarm. Timeout → fire siren.
- **Exit Delay** (all modes): After arming, 30s grace period. Exit a sensor during this → no trigger (bypass until door closes).
- **Trigger time** (triggered): the alarm stays in `triggered` for `trigger_time` seconds (default 300, set in the config flow). What happens after that is defined in `state_machine.py`, which I did not re-verify in this pass.

---

## 7. Module System (6 Modules)

Each module is instantiated by `ModuleDispatcher` and follows a retry pattern:

| Module | Entity Type | Purpose | Retry Logic | Health Critical |
|--------|------------|---------|-------------|-----------------|
| **Camera** | `camera.*` | Snapshot on trigger | 2s→4s→8s | High |
| **Lock** | `lock.*` | Lock all doors on arm | 2s→4s→8s | Critical |
| **Lights** | `light.*` | Flash lights on trigger | 2s→4s→8s | Medium |
| **Climate** | `climate.*` | Set temp on mode change | 2s→4s→8s | Low |
| **Siren** | `siren.*` | Sound alarm on trigger | 2s→4s→8s | **CRITICAL** |
| **TTS** | `tts.*` | Voice alert on trigger | 2s→4s→8s | High |

**Retry Strategy:**
```python
async def async_trigger(self, context):
    for attempt in range(3):
        try:
            return await self._trigger_impl(context)
        except Exception as e:
            await asyncio.sleep(2 ** attempt)  # 2s, 4s, 8s
    # Graceful degradation: log but don't crash
    _LOGGER.warning(f"Module {self.name} failed after 3 retries")
```

---

## 8. Storage & Persistence

### 8.1 Store v2 (MigratableStore)

Handles auto-migration from v1→v2 on first load:

```
Store schema v2:
├── zones: {zone_id: {name, sensors: [...], entry_delay, ...}}
├── users: {user_id: {name, pin_hash (bcrypt), ...}}
├── nfc_tags: {tag_id: {user_id, action, name, requires_pin, created_at}}
├── modules: {module_name: {enabled, entity_ids, ...}}
├── floorplan: {rooms: [...], openings: [...], image_b64: ...}
├── auto_actions: {enabled, timers, fake_presence_v2, ...}
├── notifications: {user_prefs: {quiet_hours, channels, ...}}
└── [other config fields]
```

**NFC Tags in Store:** top-level `nfc_tags` dict keyed by `tag_id` (see section 4.2).

### 8.2 Security: bcrypt PIN Hashing

The code sample below is illustrative only. See `store.py` for the real implementation.

- **Algorithm:** bcrypt with 10 rounds
- **Code lockout:** `code_attempts.py` (`CodeAttemptLimiter`) counts failed code checks. 5 failures within 10 minutes refuse all code checks for 10 minutes. The limiter is global, not per user. NFC tags that skip the code check never reach it. Which call sites use it was not re-verified in this pass
- **Threading:** `ThreadPoolExecutor` for parallel user authentication
- **Validation:** code checks that go through the limiter, and NFC tags that require a PIN

```python
async def authenticate_user(self, user_id, pin):
    """Validate user PIN (non-blocking, parallel bcrypt)."""
    loop = asyncio.get_event_loop()
    stored_hash = self._users[user_id]["pin_hash"]
    
    return await loop.run_in_executor(
        self._bcrypt_executor,
        bcrypt.checkpw,
        pin.encode(), stored_hash.encode()
    )
```

---

## 9. WebSocket API (Coordinator ↔ Frontend)

The frontend (`secure-me-panel.js`) communicates with the backend over WebSocket.

### 9.1 API Structure

```
Request:  { "id": 1, "type": "secure_me/<command>", ...command fields }
Response: { "id": 1, "type": "result", "success": true, "result": {...} }
Error:    { "id": 1, "type": "result", "success": false, "error": {"code": "...", "message": "..."} }
```

### 9.2 Endpoints (command names; see `websocket_api.py` for the full list)

The panel-config API is internal to `secure-me-panel.js`. API.md documents only the NFC endpoints and the arm/disarm commands.

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| **ws_sensors.py** | `secure_me/get_sensors`, `save_sensors`, `hide_sensor`, `unmark_environmental`, `get_zones`, `save_zone`, `delete_zone`, `get_users`, `save_user`, `delete_user`, `get_nfc_tags`, `register_nfc_tag`, `delete_nfc_tag`, `get_ha_nfc_tags`, `import_nfc_tag`, `get_persons`, `get_alarm_state`, sensor-group commands | Sensors, zones, users, NFC |
| **ws_modules.py** | `secure_me/get_modules`, `save_module`, `get_module_entities`, `run_test`, `get_health_summary`, notification, automation, scheduled test and home alone camera commands | Modules, tests, notifications |
| **ws_alarm.py** | `secure_me/arm_away`, `arm_home`, `arm_night`, `arm_vacation`, `arm_home_alone`, `disarm`, `skip_delay`, `get_auto_actions`, `save_auto_actions`, `get_fake_presence_v2`, `save_fake_presence_v2`, speaker profile commands | Alarm control, Auto Actions, Fake Presence v2 |
| **ws_floorplan.py** | `secure_me/get_floorplan`, `save_floorplan_image`, `save_floorplan_markers`, `delete_floorplan` | Floorplan |
| **ws_helpers.py** | Shared `_get_coordinator()`, `_get_store()` | Helper utilities |

---

## 10. Testing Strategy

### 10.1 Test Categories

The numbers below are estimates and were not re-verified in this pass. CI is authoritative.

| Category | Files | Tests | Coverage |
|----------|-------|-------|----------|
| **Engine Tests** | 10 | 100+ | 90%+ |
| **Integration Tests** | 12 | 150+ | 85%+ |
| **Service Tests** | 1 | 20 | 95%+ |
| **Module Tests** | 7 | 50+ | 85%+ |
| **State Machine Tests** | 2 | 20 | 90%+ |
| **WebSocket Tests** | 3 | 60+ | 80%+ |
| **Other** | 2 | 10+ | 75%+ |
| **TOTAL** | **37+** | **400+** | **80%+** |

### 10.2 Offline Test Example

```python
# Illustrative only: method names differ from the real tests. See tests/test_auto_actions_engine.py
@pytest.mark.asyncio
async def test_auto_actions_all_persons_away():
    """AutoActionsEngine starts timers when all persons leave."""
    engine = AutoActionsEngine(
        store=MockStore(...),
        coordinator=MockCoordinator(),
        config={"lock_delay": 120, "enabled": True}
    )
    
    await engine.async_start()
    
    # Simulate person going away
    await engine._on_person_state_changed("person.alice", "not_home")
    
    # Assert lock action scheduled
    assert "lock" in engine._action_tasks
    assert engine._action_tasks["lock"].get_coro() is not None
```

---

## 11. Performance Characteristics

The figures below are estimates, not measurements.

### 11.1 Latency (Typical)

| Operation | Latency | Note |
|-----------|---------|------|
| Sensor trigger → siren | <100ms | Direct module dispatch |
| NFC scan → arm/disarm | <500ms | Includes PIN verification (if required) |
| Presence change → lock | 5-120s | Configurable per-action delay |
| HA service call | 50-200ms | Depends on module, retries 3x |
| WebSocket message round-trip | <50ms | Local HA instance |
| bcrypt PIN check | 50-100ms | ThreadPoolExecutor parallelized |

### 11.2 Memory Usage

| Component | Size | Note |
|-----------|------|------|
| Store (at rest) | ~2 MB | 500 zones + users + NFC tags + configs |
| AutoActionsEngine | ~50 KB | Tracked persons, timers, caches |
| Frontend (JS) | ~367 KB | secure-me-panel.js, uncompressed |
| NFC tags cache | ~5 KB | Per 100 users |
| Total resident | ~2.5 MB | Typical home setup |

### 11.3 CPU Usage

- **Idle (no events):** <0.1% (engines sleep)
- **Active arming:** <1% (state transitions, module dispatch)
- **NFC scan:** <2% (bcrypt verification + event dispatch)
- **Auto-actions running:** <1.5% (timers, presence checks)

---

## 12. Troubleshooting & Debugging

### 12.1 Enable Debug Logging

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.secure_me: debug
    custom_components.secure_me.coordinator: debug
    custom_components.secure_me.auto_actions: debug
```

### 12.2 Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| NFC tag doesn't trigger | Tag not registered or user not found | Go to Users tab, register tag in NFC section |
| NFC PIN check fails | Wrong PIN hashing or bcrypt error | Check logs for PIN verification errors, restart integration |
| Siren doesn't sound on trigger | Module not assigned or entity unavailable | Check **System Health** tab → module health |
| Auto-lock doesn't happen after arm | AutoActionsManager not started, or house not marked empty | Check logs for `AutoActionsManager started` |
| Zone sensor stuck "unknown" | Sensor not integrated, or state_changed event not firing | Restart HA, verify sensor entity exists |

### 12.3 Test NFC Locally

The example that used to be here called methods that do not exist. See `tests/test_nfc_tag_handling.py` for the real NFC tests.

The real NFC tests are in `tests/test_nfc_tag_handling.py`. The old snippet was removed because it called a method and a state attribute that do not exist in the code.

---

## 13. Future Roadmap

### Gold Tier (Planned)

- [ ] Full translations (DA/EN/SV/DE/NL)
- [ ] Device class integration (DeviceInfo with manufacturer, model)
- [ ] Circuit breaker pattern for module retries
- [ ] WebSocket message compression
- [ ] Rate limiting on rapid state changes
- [ ] NFC tag export/import (backup/restore)

### Platinum Tier (Long-term)

- [ ] Redis-backed session store (for multi-instance HA)
- [ ] Event replay & audit log
- [ ] Advanced encryption (AES-256 for PIN storage)
- [ ] GraphQL API (alongside REST/WebSocket)
- [ ] Machine learning for anomaly detection
- [ ] RFID reader integration (besides HA native tag scanning)

---

## 14. References

- **README.md** — User-facing feature list and setup guide
- **API.md** — Alarm entity state/attribute contract, NFC endpoints
- **STATUS.md** — Version history & release notes
- **CHANGELOG.md** — Detailed changelog
- **quality_scale.yaml** — HACS Silver/Gold tier requirements
- **tests/** — 41 test files (CI is authoritative for counts)
- **test_auto_actions_engine.py** — Engine pattern example

---

**Maintained by:** Secure Me Team  
**Last Updated:** 2026-11-16  
**Status:** Production Ready (v2.2.0)  
**Test Coverage:** see CI (not re-verified locally)  
**Code Quality:** Zero linting violations (Ruff), strict type hints (PEP 563)

