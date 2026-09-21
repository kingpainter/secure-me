# Secure Me - Architecture Overview

## v2.0.0: Modular Engine Architecture

### 📐 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│         Home Assistant Integration (Coordinator)            │
│  - Manages HA integration lifecycle                         │
│  - Orchestrates engines and zone manager                    │
│  - Handles WebSocket clients                                │
└────────────┬──────────────────────────────────────────────┬─┘
             │                                              │
     ┌───────▼──────────┐                         ┌─────────▼─────┐
     │ Zone Manager     │                         │ State Machine │
     │ - Zone logic     │                         │ - Alarm modes │
     │ - Triggers       │                         │ - Transitions │
     └──────────────────┘                         └───────────────┘
             │
    ┌────────┴──────────────────────────────────┐
    │         Engine Architecture (v2.0+)       │
    └────────┬──────────────────────────────────┘
             │
    ┌────────┴─────────────────────────────────────────────────────┐
    │                                                                │
    │  Each engine: Pure state machine, offline testable, minimal   │
    │  HA dependencies                                              │
    │                                                                │
┌───▼─────────────────┐  ┌─────────────────────┐  ┌──────────────┐
│  AutoActionsEngine  │  │ FloorplanEngine    │  │ Notification │
│                     │  │                    │  │ Engine       │
│ Presence-based      │  │ Room/opening       │  │              │
│ automation:         │  │ state tracking:    │  │ Routing:     │
│ - Person tracking   │  │ - Rooms            │  │ - User prefs │
│ - Lock actions      │  │ - Openings/doors   │  │ - Quiet hrs  │
│ - Alarm delays      │  │ - Markers          │  │ - Severity   │
│ - Camera triggers   │  │ - Summary status   │  │ - Event type │
│                     │  │                    │  │              │
│ Constructor:        │  │ Constructor:       │  │ Constructor: │
│ (hass, coord, store)│  │ (no HA deps)       │  │ (hass, ...)  │
└─────────────────────┘  └────────────────────┘  └──────────────┘
```

### 🏗️ Base Engine Pattern

All engines inherit from `BaseEngine` which provides:

```python
class BaseEngine:
    async def async_start(self) -> None:
        """Called after coordinator is ready."""
        self._running = True
    
    async def async_stop(self) -> None:
        """Called on integration unload."""
        await self._cleanup_tasks()
        self._running = False
    
    def register_cleanup(self, task: asyncio.Task) -> None:
        """Register task for cleanup on shutdown."""
    
    def is_running(self) -> bool:
        """Check if engine is running."""
```

### 📦 Module Structure

```
custom_components/secure_me/
├── __init__.py                      # Entry point
├── coordinator.py                   # Orchestrates engines and zones
├── state_machine.py                 # Alarm state machine (DISARMED, ARMED_AWAY, etc.)
├── zones.py                         # Zone logic and sensor management
├── auto_actions.py                  # DEPRECATED (logic now in engine/)
├── notification_dispatcher.py       # DEPRECATED (logic now in engine/)
│
├── engine/                          # v2.0+: Pure engines (offline testable)
│   ├── __init__.py                  # Exports: BaseEngine, *Engine classes
│   ├── base_engine.py               # Common lifecycle (91 lines)
│   ├── auto_actions_engine.py       # Presence automation (997 lines)
│   ├── floorplan_engine.py          # Room/opening state (208 lines)
│   └── notification_engine.py       # Event routing (769 lines)
│
├── modules/                         # Device type handlers
│   ├── base.py                      # Module base class
│   ├── lock.py                      # Lock module
│   ├── camera.py                    # Camera module
│   ├── lights.py                    # Light control
│   ├── climate.py                   # Climate/thermostat
│   ├── siren.py                     # Alarm siren
│   └── tts.py                       # Text-to-speech
│
├── services.py                      # Service handlers (arm, disarm, etc.)
├── websocket_api.py                 # WebSocket API
├── ws_alarm.py                      # Alarm WS handlers
├── ws_floorplan.py                  # Floorplan WS handlers
├── ws_modules.py                    # Module WS handlers
├── ws_sensors.py                    # Sensor data WS handlers
│
├── const.py                         # Constants and defaults
├── config_flow.py                   # Configuration UI
├── store.py                         # MigratableStore v2 for config persistence
├── system_health.py                 # System health reporting
└── quality_scale.yaml               # HACS quality tier documentation
```

### 🔄 Data Flow: Alarm Trigger Example

```
1. Sensor triggers (zone_triggered event)
   └─> coordinator._on_zone_triggered()
   
2. State machine evaluates transition
   └─> AlarmStateMachine.process_event()
   └─> Returns new state (e.g., ALARM_TRIGGERED)
   
3. Update coordinator state
   └─> self.data["alarm_state"] = "triggered"
   
4. Notify listeners
   └─> _async_refresh_alarm_entities()
   └─> WebSocket clients notified
   
5. Trigger actions (if enabled)
   └─> AutoActionsEngine._run_auto_action()
   └─> coordinator.dispatch_module_action()
   └─> modules/siren.py.async_siren_action()
   
6. Send notifications
   └─> NotificationEngine.route_notification()
   └─> _send_push() to admin users
```

### 🧪 Testing Strategy (v2.0+)

**Engine Tests** (offline, no HA instance needed):
```python
# test_auto_actions_engine.py
def test_all_persons_away_returns_true():
    engine = AutoActionsEngine(hass, coordinator, store)
    engine._tracker_states = {"person.alice": "not_home"}
    assert engine._all_persons_away() is True
```

**Integration Tests** (need HA instance):
```python
# test_coordinator.py
async def test_zone_trigger_updates_state(hass):
    coordinator = SecureMeCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    # Simulate zone trigger
```

### 📊 Type Safety (v2.0+)

All 34 files now have:
1. `from __future__ import annotations` (PEP 563)
2. Return type hints on all methods
3. Parameter type hints on all functions

Enforced by GitHub Actions CI:
- `ruff format --check` - Code formatting
- `ruff check` - Code quality rules
- `mypy --strict` - Static type checking

### 🚀 Performance Considerations

**State Machine Updates:**
- Coordinator refresh: ~100ms (includes zone check)
- Zone trigger processing: ~10ms
- Auto-action delay: Configurable (typically 30-180s)

**Memory Usage:**
- ~2MB base (coordinator + engines)
- ~5-10MB with floorplan data (depending on size)
- Task cleanup prevents memory leaks

### 🔐 Security Model

- No external API calls (self-contained)
- All data stored locally (MigratableStore)
- WebSocket clients require Home Assistant session
- Service calls validated via vol.Schema

### 🎯 Future Roadmap

**Phase 3 (Current - v2.0.0)**:
- ✅ Engine extraction and testability
- ✅ Type safety (PEP 563)
- ✅ CI quality gates
- ⏳ Unit test completion (80%+ coverage)

**Phase 4 (Post v2.0)**:
- Full translations (Lokalise)
- Device class integration
- HACS Gold-tier evaluation
- Performance profiling
- Advanced analytics

### 📚 Related Docs

- `CHANGELOG.md` - Version history and changes
- `quality_scale.yaml` - HACS quality tier requirements
- `.github/workflows/` - CI/CD automation
- `custom_components/secure_me/const.py` - Constants reference

---

**Architecture Version**: 2.0.0  
**Last Updated**: 2026-09-21  
**Status**: Silver-tier ready for HACS evaluation
