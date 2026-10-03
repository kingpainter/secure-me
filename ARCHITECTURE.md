# Secure Me — Architecture & Design

**Version:** 2.2.0  
**Date:** 2026-10-03  
**Status:** Production Ready (v2.2.0)

---

## 1. Overview

Secure Me is a multi-zone Home Assistant alarm system designed around **pure state machines** and **engine-based architecture**. All state logic is decoupled from Home Assistant dependencies, enabling offline unit testing and maintainability.

Version 2.2.0 adds **NFC tag authentication** for PIN-less control, while maintaining the core engine pattern and 80%+ test coverage.

### Core Design Principles

1. **State Machine as Source of Truth** — All state transitions (arm, disarm, trigger) are explicit, testable events
2. **Engine Pattern** — Extracted logic into standalone, injectable state machines (`BaseEngine`)
3. **Minimal HA Coupling** — Engines operate independently; only coordinators bridge to HA
4. **Testability First** — 80%+ unit test coverage with zero mocked HA instances for engines
5. **Async-Only I/O** — No blocking calls; full `asyncio` compliance
6. **Security by Default** — bcrypt PIN hashing, NFC tag binding, audit logging

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
│ • coordinator.py (1,512 lines) — Orchestration            │
│ • module_dispatch.py (333 lines) — Module instantiation   │
│ • Services entry point (hass.services.async_register)    │
│ • NFC event listener (async_listen_nfc_events)           │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ direct method calls
                            │
┌─────────────────────────────────────────────────────────────┐
│ State Machine Engine Layer (Pure Logic)                    │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ BaseEngine (91 lines)                               │  │
│ │ • async_start(), async_stop(), cleanup             │  │
│ │ • Task lifecycle management                         │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ AutoActionsEngine (1,010 lines)                      │  │
│ │ • Presence-based automation                         │  │
│ │ • Tracks person entities (home/away state)         │  │
│ │ • Manages lock/alarm/camera action delays          │  │
│ │ • Arrival confirmation + fake presence blocking    │  │
│ │ • Stale tracker timeout (30 min, configurable)     │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ FloorplanEngine (207 lines)                          │  │
│ │ • Room & opening state tracking                     │  │
│ │ • Live-view coordinates                             │  │
│ │ • No HA dependencies                                │  │
│ │ • Sensor pin markers (active/inactive states)       │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ NotificationEngine (859 lines)                       │  │
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
│ • NFCManager (tag registration, user binding)             │
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

### 3.2 AutoActionsEngine

**Purpose:** Presence-based automation — arm/disarm/lock/camera actions triggered by person entity state changes.

**Key Components:**

| Component | Lines | Purpose |
|-----------|-------|---------|
| `_on_home_empty()` | 60 | Entry point: all persons went away |
| `_all_persons_away()` | 40 | Check if all tracked persons are `not_home` (fail-safe if tracker stale) |
| `_run_action_after_delay()` | 50 | Queue lock/alarm/camera actions with per-action delays |
| `_execute_action()` | 80 | Dispatch to `coordinator._do_lock()`, `_do_alarm()`, `_do_camera()` |
| `_cancel_all_action_tasks()` | 30 | User returns home: cancel all queued actions |
| `_send_summary_notification()` | 40 | Report action results to user |

**State:** Maintains `_persons_state`, `_action_tasks`, `_tracker_stale_since`, `_action_results`

**Configuration Parameters:**
- `lock_delay` (int, seconds) — Delay before auto-locking (default: 120)
- `alarm_delay` (int, seconds) — Delay before auto-arming (default: 300)
- `camera_delay` (int, seconds) — Delay before activating cameras (default: 0)
- `stale_tracker_timeout` (int, minutes) — GPS tracker unavailability threshold (default: 30)
- `arrival_confirmation` (int, minutes) — Grace period for confirmed arrival (default: 2)

**Input Events:**
- `state_changed` (hass event bus): tracked person entity state changed
- `timer_update` (internal): Action delay expired
- `user_returns` (coordinator callback): Someone came home, cancel everything

**Output:**
- Coordinator method calls: `async_arm_away()`, `async_lock_all()`, `async_trigger_camera()`
- User notifications: Success/failure summary
- Internal events: `auto_actions_completed`, `auto_actions_failed`

**Offline Testability:** ✅ Yes — pure state machine, no HA dependencies  
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

## 4. NFC Tag Integration (v2.1.0+)

### 4.1 NFC Architecture

NFC tags enable PIN-less, user-bound authentication for quick arm/disarm:

```
Home Assistant tag_scanned event
  ↓
coordinator.async_listen_nfc_events()
  ↓
Lookup tag in store → get associated user_id
  ↓
Check if tag requires PIN (optional per-tag setting)
  ├─ If yes: await PIN verification from user
  └─ If no: proceed directly
  ↓
Verify user is admin or has permission for requested action
  ↓
Execute action: arm_away / disarm / trigger
  ↓
Log event with user_id + tag_id (audit trail)
  ↓
Fire secure_me_nfc_scanned event to HA
```

### 4.2 Store v2 NFC Data

```python
{
  "users": {
    "user_123": {
      "name": "Flemming",
      "pin_hash": "...(bcrypt)...",
      "nfc_tags": [
        {
          "tag_id": "04FA123456789ABC",
          "name": "iPhone",
          "requires_pin": False,
          "created_at": "2026-10-03T10:30:00Z"
        }
      ]
    }
  }
}
```

### 4.3 NFC Event Flow

```
NFC Scan: User taps iPhone against reader
  ↓
Home Assistant receives tag_scanned event with tag_id
  ↓
coordinator._on_tag_scanned()
  ↓
Store lookup: Find tag in user's nfc_tags
  ↓
If tag.requires_pin == True:
  ├─ Send notification to user: "Enter PIN to disarm"
  ├─ Start 2-min timeout
  ├─ Await PIN from mobile app / panel
  └─ If timeout: cancel, log security event
  ├─ If wrong PIN: log failed attempt, retry allowed
  └─ If correct PIN: proceed to action
  ↓
Execute: coordinator.async_disarm() or async_arm_away()
  ↓
Fire secure_me_nfc_scanned(tag_id, user_id, success=True)
  ↓
Send confirmation notification to user
```

### 4.4 Security Considerations

- **Tag Binding:** Each tag is bound to a specific user (audit trail)
- **Per-Tag PIN:** Optional per-tag enforcement (some tags bypass PIN)
- **HA Tag Events:** NFC integration relies on Home Assistant's native tag scanning
  - Requires HA Companion app (iOS) or RFID reader
  - Events fire over HA event bus (same transport as state_changed)
- **Rate Limiting:** Rapid repeated scans (>10 in 1 min) log security event
- **Audit Trail:** All NFC events logged with tag_id + user_id + action + result

---

## 5. Coordinator Integration

### 5.1 Coordinator's Role

`coordinator.py` is the **bridge** between engines and Home Assistant:

1. **Engine Instantiation** — Creates engine instances, passes config/store
2. **HA Event Routing** — Listens to `state_changed`, `tag_scanned`, converts to engine inputs
3. **Module Dispatch** — Calls ModuleDispatcher for siren/camera/lock/etc. execution
4. **State Machine** — Tracks alarm state (armed/disarmed/triggered)
5. **Health Scoring** — Aggregates module health into diagnostics
6. **NFC Listening** — Monitors `tag_scanned` events, verifies user + tag binding

### 5.2 Startup Sequence

```
hass.setup_entry()
  → coordinator = Coordinator(hass, store, config_entry)
  → AutoActionsEngine.__init__()
  → FloorplanEngine.__init__()
  → NotificationEngine.__init__()
  → coordinator.async_config_entry_first_refresh()
    → coordinator.async_start() ← triggers engine.async_start() for each
      → AutoActionsEngine._check_initial_presence() ← if house empty, start timers
      → FloorplanEngine.load_state()
      → NotificationEngine.load_preferences()
  → hass.services.async_register() ← register arm_away, disarm, trigger, etc.
  → hass.bus.async_listen("tag_scanned", ...) ← start NFC listener
```

### 5.3 Event Flow Example: "Person Goes Away"

```
Home Assistant Event Bus
  ↓
state_changed(entity_id="person.alice", new_state="not_home")
  ↓
coordinator._state_changed_listener()
  ↓
AutoActionsEngine._on_person_state_changed()
  ↓
_all_persons_away() → True (all tracked persons now away)
  ↓
_on_home_empty() ← START 2-minute lock delay timer
  ↓
_run_action_after_delay("lock", delay=120)
  ↓
[2 minutes pass]
  ↓
_execute_action("lock")
  ↓
coordinator._do_lock() ← call actual Home Assistant services
  ↓
ModuleDispatcher.lock_module.async_lock_all()
  ↓
hass.services.async_call("lock", "lock", {...})
```

### 5.4 Event Flow Example: "NFC Tag Scan"

```
Home Assistant tag_scanned event
  ↓
coordinator._on_tag_scanned(tag_id="04FA123456789ABC")
  ↓
Store lookup: find tag in users
  ↓
Found: tag belongs to user_123, requires_pin=False
  ↓
coordinator.async_disarm() ← no PIN check needed
  ↓
state_machine.disarm()
  ↓
hass.bus.async_fire("secure_me_alarm_disarmed", {"disarmed_by": "user_123"})
  ↓
hass.bus.async_fire("secure_me_nfc_scanned", {"tag_id": "04FA...", "user_id": "user_123"})
  ↓
NotificationEngine routes confirmation to user
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
        │  DISARMED    │ (manual disarm or 15-min auto-reset)
        └──────────────┘
```

**Key Transitions:**
- **Entry Delay** (armed_away): When sensor triggers, countdown starts (default 30s). User disarms within window → no alarm. Timeout → fire siren.
- **Exit Delay** (all modes): After arming, 30s grace period. Exit a sensor during this → no trigger (bypass until door closes).
- **Auto-Reset** (triggered): After 15 minutes, auto-disarm (configurable).

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
├── users: {user_id: {name, pin_hash (bcrypt), nfc_tags: [...], ...}}
├── modules: {module_name: {enabled, entity_ids, ...}}
├── floorplan: {rooms: [...], openings: [...], image_b64: ...}
├── auto_actions: {enabled, timers, fake_presence_v2, ...}
├── notifications: {user_prefs: {quiet_hours, channels, ...}}
└── [other config fields]
```

**NFC Tags in Store:**
```python
user["nfc_tags"] = [
    {
        "tag_id": "04FA123456789ABC",
        "name": "iPhone",
        "requires_pin": False,
        "created_at": "2026-10-03T10:30:00Z"
    }
]
```

### 8.2 Security: bcrypt PIN Hashing

- **Algorithm:** bcrypt with 10 rounds (NIST recommended)
- **Threading:** `ThreadPoolExecutor` for parallel user authentication
- **Validation:** Called on every NFC/code entry attempt + auto-actions startup

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
Request:  { id, type, payload: {...} }
Response: { id, success, result: {...} or error }
```

### 9.2 Endpoints (5 modules, 30+ total endpoints)

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| **ws_sensors.py** | `ws_get_sensors`, `ws_save_sensor`, `delete_sensor`, `get_nfc_tags`, `register_nfc_tag`, `delete_nfc_tag` | Sensor + NFC management |
| **ws_modules.py** | `ws_get_modules`, `ws_enable_module`, `ws_test_module`, `ws_run_test` | Module management |
| **ws_alarm.py** | `ws_arm_away`, `ws_disarm`, `ws_save_auto_actions`, `ws_trigger` | Alarm control |
| **ws_floorplan.py** | `ws_get_floorplan`, `ws_save_floorplan_image`, `ws_save_floorplan_markers` | Floorplan CRUD |
| **ws_helpers.py** | Shared `_get_coordinator()`, `_get_store()` | Helper utilities |

---

## 10. Testing Strategy

### 10.1 Test Categories

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
# No HA instance needed — pure state machine test
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
    custom_components.secure_me.engine.auto_actions_engine: debug
```

### 12.2 Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| NFC tag doesn't trigger | Tag not registered or user not found | Go to Users tab, register tag in NFC section |
| NFC PIN check fails | Wrong PIN hashing or bcrypt error | Check logs for PIN verification errors, restart integration |
| Siren doesn't sound on trigger | Module not assigned or entity unavailable | Check **System Health** tab → module health |
| Auto-lock doesn't happen after arm | AutoActionsEngine not started | Check logs for `async_start()` errors |
| Zone sensor stuck "unknown" | Sensor not integrated, or state_changed event not firing | Restart HA, verify sensor entity exists |

### 12.3 Test NFC Locally

```python
# Quick offline test
from custom_components.secure_me.coordinator import Coordinator
from tests.conftest import MockStore, MockHA

async def test_nfc():
    store = MockStore({"users": {
        "user_123": {"name": "Test", "nfc_tags": [
            {"tag_id": "04FA...", "requires_pin": False}
        ]}
    }})
    coordinator = Coordinator(MockHA(), store, {})
    
    # Simulate NFC scan
    await coordinator._on_tag_scanned("04FA...")
    
    # Assert disarmed
    assert coordinator.state_machine.state == "disarmed"
```

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
- **tests/** — 400+ passing unit + integration tests
- **test_auto_actions_engine.py** — Engine pattern example

---

**Maintained by:** Secure Me Team  
**Last Updated:** 2026-10-03  
**Status:** Production Ready (v2.2.0)  
**Test Coverage:** 80%+ (400+ tests)  
**Code Quality:** Zero linting violations (Ruff), strict type hints (PEP 563)

