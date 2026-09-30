# Secure Me — Architecture & Design

**Version:** 2.0.0  
**Date:** 2026-09-21  
**Status:** Complete (Phase 2)

---

## 1. Overview

Secure Me is a multi-zone Home Assistant alarm system designed around **pure state machines** and **engine-based architecture**. All state logic is decoupled from Home Assistant dependencies, enabling offline unit testing and maintainability.

### Core Design Principles

1. **State Machine as Source of Truth** — All state transitions (arm, disarm, trigger) are explicit, testable events
2. **Engine Pattern** — Extracted logic into standalone, injectable state machines (`BaseEngine`)
3. **Minimal HA Coupling** — Engines operate independently; only coordinators bridge to HA
4. **Testability First** — 80%+ unit test coverage with zero mocked HA instances for engines
5. **Async-Only I/O** — No blocking calls; full `asyncio` compliance

---

## 2. Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Home Assistant Core                                         │
│ • Event Bus (state_changed, custom events)                │
│ • Service Registry (arm_away, trigger, etc.)              │
│ • Entity Management (entity registry, device registry)    │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ async callbacks
                            │
┌─────────────────────────────────────────────────────────────┐
│ Coordinator Layer (HA Bridge)                              │
│ • coordinator.py (1,323 lines) — Orchestration            │
│ • module_dispatch.py (300+ lines) — Module instantiation  │
│ • Services entry point (hass.services.async_register)    │
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
│ │ AutoActionsEngine (997 lines)                        │  │
│ │ • Presence-based automation                         │  │
│ │ • Tracks person entities (home/away state)         │  │
│ │ • Manages lock/alarm/camera action delays          │  │
│ │ • Arrival confirmation window + fake presence      │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ FloorplanEngine (208 lines)                          │  │
│ │ • Room & opening state tracking                     │  │
│ │ • Live-view coordinates                             │  │
│ │ • No HA dependencies                                │  │
│ └──────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ NotificationEngine (769 lines)                       │  │
│ │ • Event routing rules                               │  │
│ │ • User preferences (quiet hours, channels)          │  │
│ │ • Dispatcher pattern                                │  │
│ └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ injected via __init__
                            │
┌─────────────────────────────────────────────────────────────┐
│ Infrastructure Layer                                        │
│ • StateMachine (alarm state enum, entry/exit delays)      │
│ • ZoneManager (sensor debouncing, grouping)               │
│ • Store v2 (bcrypt, data persistence, migrations)         │
│ • ModuleDispatcher (6 module factories + health scoring)  │
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

**Input Events:**
- `state_changed` (hass event bus): tracked person entity state changed
- `timer_update` (internal): Action delay expired
- `user_returns` (coordinator callback): Someone came home, cancel everything

**Output:**
- Coordinator method calls: `async_arm_away()`, `async_lock_all()`, `async_trigger_camera()`
- User notifications: Success/failure summary
- Internal events: `auto_actions_completed`, `auto_actions_failed`

**Offline Testability:** ✅ Yes — pure state machine, no HA dependencies
**Test File:** `tests/test_auto_actions_engine.py` (16 tests), `tests/test_auto_actions_engine_extended.py` (9 tests), `tests/test_auto_actions_reliability.py` (reliability edge cases)

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

**State:** `_rooms` dict, `_openings` dict, sensor→room mappings

**Offline Testability:** ✅ Yes — zero HA dependencies
**Test File:** `tests/test_floorplan_engine.py` (11 tests), `tests/test_floorplan_engine_full.py` (full integration)

---

### 3.4 NotificationEngine

**Purpose:** Event routing rules + user preferences (quiet hours, do-not-disturb).

**Key Components:**

| Component | Purpose |
|-----------|---------|
| `should_notify(event_type, user_id)` | Check quiet hours, preferences, criticality |
| `route_notification(event_type)` | Determine channel(s): mobile, email, dashboard |
| `get_notification_text(event_type, context)` | Format message (Danish preferred, fallback English) |

**State:** User preferences, quiet hour rules, notification history (for deduplication)

**Offline Testability:** ✅ Yes (except HA service calls, which are injected)
**Test File:** `tests/test_notification_engine.py` (8 tests), `tests/test_notification_engine_full.py` (full integration)

---

## 4. Coordinator Integration

### 4.1 Coordinator's Role

`coordinator.py` is the **bridge** between engines and Home Assistant:

1. **Engine Instantiation** — Creates engine instances, passes config/store
2. **HA Event Routing** — Listens to `state_changed`, converts to engine inputs
3. **Module Dispatch** — Calls ModuleDispatcher for siren/camera/lock/etc. execution
4. **State Machine** — Tracks alarm state (armed/disarmed/triggered)
5. **Health Scoring** — Aggregates module health into diagnostics

### 4.2 Startup Sequence

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
```

### 4.3 Event Flow Example: "Person Goes Away"

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

---

## 5. State Machine (Alarm States)

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

## 6. Module System (6 Modules)

Each module is instantiated by `ModuleDispatcher` and follows a retry pattern:

| Module | Entity Type | Purpose | Health Critical |
|--------|------------|---------|-----------------|
| **Camera** | `camera.*` | Snapshot on trigger | High |
| **Lock** | `lock.*` | Lock all doors on arm | Critical |
| **Lights** | `light.*` | Flash lights on trigger | Medium |
| **Climate** | `climate.*` | Set temp on mode change | Low |
| **Siren** | `siren.*` | Sound alarm on trigger | **CRITICAL** |
| **TTS** | `tts.*` | Voice alert on trigger | High |

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

## 7. Storage & Persistence

### 7.1 Store v2 (MigratableStore)

Handles auto-migration from v1→v2 on first load:

```
Store schema v2:
├── zones: {zone_id: {name, sensors: [...], entry_delay, ...}}
├── users: {user_id: {name, pin_hash (bcrypt), nfc_tags, ...}}
├── modules: {module_name: {enabled, entity_ids, ...}}
├── floorplan: {rooms: [...], openings: [...], image_b64: ...}
├── auto_actions: {enabled, timers, fake_presence_v2, ...}
└── [other config fields]
```

### 7.2 Security: bcrypt PIN Hashing

- **Algorithm:** bcrypt with 10 rounds (NIST recommended)
- **Threading:** `ThreadPoolExecutor` for parallel user authentication
- **Validation:** Called on every NFC/code entry attempt

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

## 8. WebSocket API (Coordinator ↔ Frontend)

The frontend (`secure-me-panel.js`) communicates with the backend over WebSocket.

### 8.1 API Structure

```
Request:  { id, type, payload: {...} }
Response: { id, success, result: {...} or error }
```

### 8.2 Endpoints (5 modules)

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| **ws_sensors.py** | `ws_get_sensors`, `ws_save_sensor`, `ws_delete_sensor` | Sensor configuration |
| **ws_modules.py** | `ws_get_modules`, `ws_enable_module`, `ws_test_module` | Module management |
| **ws_alarm.py** | `ws_arm_away`, `ws_disarm`, `ws_save_auto_actions` | Alarm control |
| **ws_floorplan.py** | `ws_get_floorplan`, `ws_save_floorplan_image`, `ws_save_floorplan_markers` | Floorplan CRUD |
| **ws_helpers.py** | Shared `_get_coordinator()`, `_get_store()` | Helper utilities |

---

## 9. Testing Strategy

### 9.1 Test Categories

| Category | Files | Lines | Focus |
|----------|-------|-------|-------|
| **Engine Tests** | 4 | ~1,200 | Pure state machine logic (no HA instance) |
| **Integration Tests** | 12 | ~4,500 | Engine + coordinator interaction |
| **Service Tests** | 1 | ~800 | hass.services handlers |
| **Module Tests** | 2 | ~1,500 | Module retry + degradation |
| **State Machine Tests** | 2 | ~1,000 | Alarm state transitions |
| **Other** | 9 | ~10,454 | Config flow, diagnostics, zones, etc. |
| **TOTAL** | **30** | **~19,454** | **404 tests, 80%+ coverage** |

### 9.2 Offline Test Example

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

## 10. Type Safety & Code Quality

### 10.1 PEP 563 + Type Hints

```python
from __future__ import annotations

async def async_arm_away(
    self, 
    force: bool = False, 
    skip_delay: bool = False
) -> tuple[bool, str]:
    """Arm the alarm in away mode.
    
    Args:
        force: Bypass open sensor check
        skip_delay: Arm immediately (test only)
    
    Returns:
        (success, reason_if_failed)
    """
```

- All 34 files use PEP 563 forward references
- Return types: 95%+ coverage
- Parameter types: 95%+ coverage
- Docstrings: 100% on public methods

### 10.2 Code Quality Gates (CI)

```yaml
# .github/workflows/pytest.yaml
- ruff format --check    # Code formatting
- ruff check             # Linting
- mypy --strict          # Type checking
- pytest tests/          # Unit tests
```

**Status:** ✅ All passing (CI: 100% green rate)

---

## 11. Performance Characteristics

### 11.1 Latency (Typical)

| Operation | Latency | Note |
|-----------|---------|------|
| Sensor trigger → siren | <100ms | Direct module dispatch |
| Presence change → lock | 5-120s | Configurable per-action delay |
| HA service call | 50-200ms | Depends on module, retries 3x |
| WebSocket message round-trip | <50ms | Local HA instance |

### 11.2 Memory Usage

- **Store (at rest):** ~2 MB (500 zones + users + configs)
- **AutoActionsEngine:** ~50 KB (tracked persons, timers, caches)
- **Frontend:** ~367 KB (secure-me-panel.js, uncompressed)

---

## 12. Future Roadmap

### Gold Tier (Planned)

- [ ] Full translations (DA/EN/SV/DE/NL)
- [ ] Device class integration (DeviceInfo with manufacturer, model)
- [ ] Circuit breaker pattern for module retries
- [ ] WebSocket message compression
- [ ] Rate limiting on rapid state changes

### Platinum Tier (Long-term)

- [ ] Redis-backed session store (for multi-instance HA)
- [ ] Event replay & audit log
- [ ] Advanced encryption (AES-256 for PIN storage)
- [ ] GraphQL API (alongside REST/WebSocket)
- [ ] Machine learning for anomaly detection

---

## 13. Debugging & Troubleshooting

### 13.1 Enable Debug Logging

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.secure_me: debug
    custom_components.secure_me.coordinator: debug
    custom_components.secure_me.auto_actions: debug
```

### 13.2 Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Siren doesn't sound on trigger | Module not assigned or entity unavailable | Check **System Health** tab → module health |
| Auto-lock doesn't happen after arm | AutoActionsEngine not started | Check logs for `async_start()` errors |
| Zone sensor stuck "unknown" | Sensor not integrated, or state_changed event not firing | Restart HA, verify sensor entity exists |
| Diagnostics download crashes | zones_detail loop bug (fixed in v1.5.5) | Update to 1.5.5+ |

### 13.3 Test a Module Locally

```python
# Quick offline test
from custom_components.secure_me.engine.auto_actions_engine import AutoActionsEngine
from tests.conftest import MockStore, MockCoordinator

async def test():
    engine = AutoActionsEngine(
        store=MockStore({"auto_actions": {...}}),
        coordinator=MockCoordinator(),
        config={"enabled": True}
    )
    await engine.async_start()
    await engine._on_person_state_changed("person.alice", "not_home")
    # Assert state...
```

---

## 14. References

- **README.md** — User-facing feature list
- **API.md** — Alarm entity state/attribute contract
- **CHANGELOG.md** — Version history & what's new
- **quality_scale.yaml** — HACS Silver tier requirements
- **tests/** — 404 passing unit + integration tests

---

**Maintained by:** Secure Me Team  
**Last Updated:** 2026-09-21  
**Status:** Complete (Phase 2 implementation)

