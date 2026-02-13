# 🏗️ Secure Me - Project Structure

Complete technical documentation of the Secure Me integration architecture and file organization.

**Version:** 0.3.0  
**Last Updated:** 2026-02-13

---

## 📂 Directory Structure

```
custom_components/secure_me/
│
├── 📄 __init__.py                    # Integration entry point (6-7 KB)
├── 📄 manifest.json                  # Integration metadata
├── 📄 const.py                       # Constants and enums (3 KB)
├── 📄 config_flow.py                 # GUI configuration wizard
│
├── 🎛️ Core Components
├── 📄 alarm_control_panel.py         # Main alarm entity
├── 📄 coordinator.py                 # Data coordinator (18 KB)
├── 📄 state_machine.py               # State logic (10 KB)
├── 📄 zones.py                       # Zone manager (9 KB)
├── 📄 module_manager.py              # Module lifecycle manager
├── 📄 store.py                       # Persistent storage
├── 📄 websocket_api.py               # WebSocket API (~800 lines) ✨ NEW
│
├── 🧪 Testing & Monitoring (NEW in v0.3.0)
├── 📄 binary_sensor.py               # Module health sensors (~200 lines)
├── 📄 sensor.py                      # Battery level sensors (~250 lines)
│
├── 🔌 Modules
├── 📁 modules/
│   ├── 📄 __init__.py               # Module exports (426 bytes)
│   ├── 📄 base.py                   # Base module class
│   ├── 📄 camera.py                 # Camera control
│   ├── 📄 lock.py                   # Lock management
│   ├── 📄 lights.py                 # Light control
│   ├── 📄 climate.py                # Climate management
│   ├── 📄 siren.py                  # Siren control
│   └── 📄 tts.py                    # TTS announcements
│
├── 🎨 Frontend
├── 📁 frontend/
│   └── 📄 secure-me-panel.js        # Configuration dashboard (~3800 lines) ✨ EXPANDED
│
├── 🧪 Tests (NEW in v0.3.0)
├── 📁 tests/
│   ├── 📄 __init__.py               # Test package init
│   ├── 📄 conftest.py               # Pytest fixtures
│   ├── 📄 test_init.py              # Integration tests
│   ├── 📄 test_const.py             # Constants tests
│   ├── 📄 test_state_machine.py     # State machine tests
│   ├── 📄 test_modules.py           # Module tests
│   ├── 📄 test_sensors.py           # Sensor tests
│   ├── 📄 test_store.py             # Store tests
│   ├── 📄 test_files.py             # File structure tests
│   └── 📄 test_diagnostics.py       # Diagnostics tests
│
├── 🌍 Translations
├── 📁 translations/
│   ├── 📄 en.json                   # English
│   └── 📄 da.json                   # Danish
│
├── 🖼️ Assets
├── 📄 logo.png                       # Integration logo (256×256)
├── 📄 logo@2x.png                    # High-res logo (512×512)
├── 📄 icon.png                       # Integration icon (256×256)
├── 📄 icon@2x.png                    # High-res icon (512×512)
│
└── 📝 Platform Files
    ├── 📄 switch.py                  # Switch entities
    └── 📄 select.py                  # Select entities
```

---

## 🏛️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant Core                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   Secure Me Integration                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Integration Entry (__init__.py)         │   │
│  │  • Setup & Initialization                           │   │
│  │  • Config Entry Management                          │   │
│  │  • Device Registration                              │   │
│  └──────────────────┬──────────────────────────────────┘   │
│                     │                                        │
│                     ↓                                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Coordinator (coordinator.py)             │   │
│  │  • State Management                                 │   │
│  │  • Module Coordination                              │   │
│  │  • Event Handling                                   │   │
│  │  • Health Monitoring ✨ NEW                         │   │
│  └──────┬──────────────┬─────────────┬─────────────────┘   │
│         │              │             │                      │
│    ┌────┴───┐    ┌────┴───┐    ┌───┴────┐                │
│    │ State  │    │  Zone  │    │ Module │                │
│    │Machine │    │Manager │    │Manager │                │
│    └────┬───┘    └────┬───┘    └───┬────┘                │
│         │              │            │                      │
│         ↓              ↓            ↓                      │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         Alarm Control Panel Entity                  │  │
│  │  • States: disarmed, arming, armed_*, pending...   │  │
│  │  • Attributes: zones, sensors, modules, health     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │        Testing & Monitoring ✨ NEW v0.3.0           │  │
│  │  ┌──────────────┐ ┌──────────────┐                 │  │
│  │  │Module Health │ │ Battery      │                 │  │
│  │  │Binary Sensors│ │ Sensors      │                 │  │
│  │  │(6 sensors)   │ │(Auto-discover)│                │  │
│  │  └──────────────┘ └──────────────┘                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Smart Modules (6 total)                │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │  │
│  │  │Camera│ │ Lock │ │Lights│ │Climate│ │Siren │ ...│  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │  │
│  │  Each module includes health monitoring            │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │          Frontend Panel (secure-me-panel.js)        │  │
│  │  • 7 tabs for configuration                        │  │
│  │  • Testing tab with test execution ✨ NEW          │  │
│  │  • WebSocket API integration                       │  │
│  │  • Real-time updates                               │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Persistent Storage (store.py)             │  │
│  │  • Configuration data                               │  │
│  │  • User preferences                                 │  │
│  │  • Test results ✨ NEW                              │  │
│  │  • Audit logs                                       │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 📋 Core Components

### __init__.py (Integration Entry)

**Purpose:** Integration lifecycle management

**Key Functions:**
```python
async def async_setup_entry(hass, entry):
    """Set up Secure Me from config entry."""
    # 1. Initialize store
    # 2. Initialize coordinator
    # 3. Register WebSocket API
    # 4. Register frontend panel
    # 5. Setup platforms (including health & battery sensors)
    
async def async_unload_entry(hass, entry):
    """Unload config entry."""
    # 1. Shutdown coordinator
    # 2. Cleanup modules
    # 3. Remove listeners
    # 4. Unload platforms
```

**Data Structure:**
```python
hass.data[DOMAIN] = {
    "store": <Store>,                    # Global
    "_websocket_registered": True,       # Global
    "_panel_registered": True,           # Global
    "entry_id_1": {                     # Per-entry
        COORDINATOR: <coordinator>,
        UNDO_UPDATE_LISTENER: <listener>,
    }
}
```

---

### coordinator.py (State Coordinator)

**Purpose:** Central state management and module coordination

**Class:** `SecureMeCoordinator(DataUpdateCoordinator)`

**Responsibilities:**
- State machine management
- Zone coordination
- Module lifecycle
- Event handling
- Data updates
- Health monitoring ✨ NEW

**Key Methods:**
```python
async def async_arm(self, mode, code=None):
    """Arm the alarm."""
    
async def async_disarm(self, code):
    """Disarm the alarm."""
    
async def _initialize_modules(self):
    """Initialize all enabled modules."""
    
async def _handle_state_change(self, old_state, new_state):
    """Handle state transitions."""
    
async def get_module_health(self, module_name):
    """Get health status for module."""  # ✨ NEW
```

**Module Initialization:**
```python
self.modules = {}
self.modules[MODULE_CAMERA] = CameraModule(hass, config.get(MODULE_CAMERA, {}))
self.modules[MODULE_LOCK] = LockModule(hass, config.get(MODULE_LOCK, {}))
# ... etc for all 6 modules
```

---

### state_machine.py (State Logic)

**Purpose:** Alarm state transitions and validation

**States:**
```python
STATE_DISARMED = "disarmed"
STATE_ARMING = "arming"
STATE_ARMED_AWAY = "armed_away"
STATE_ARMED_HOME = "armed_home"
STATE_ARMED_NIGHT = "armed_night"
STATE_ARMED_VACATION = "armed_vacation"
STATE_PENDING = "pending"
STATE_TRIGGERED = "triggered"
```

**Transition Rules:**
```
disarmed → arming → armed_*
armed_* → pending → (triggered | disarmed)
triggered → disarmed
```

**Key Methods:**
```python
def can_transition(current_state, new_state):
    """Check if transition is valid."""
    
async def handle_sensor_trigger(sensor, zone):
    """Handle sensor trigger based on current state."""
```

---

### zones.py (Zone Manager)

**Purpose:** Multi-zone management and sensor grouping

**Class:** `ZoneManager`

**Features:**
- Zone creation/deletion
- Sensor assignment
- Mode-based activation
- Status tracking
- Trigger callbacks

**Data Structure:**
```python
{
    "living_room": {
        "name": "Living Room",
        "sensors": ["binary_sensor.motion_1", ...],
        "modes": ["armed_away", "armed_night"],
        "priority": 1
    },
    "kitchen": { ... }
}
```

**Key Methods:**
```python
def add_zone(self, zone_id, zone_data):
    """Add new zone."""
    
def is_zone_ready(self, zone_id):
    """Check if all sensors in zone are ready."""
    
def register_trigger_callback(self, callback):
    """Register callback for zone triggers."""
```

---

## 🧪 Testing & Monitoring (NEW in v0.3.0)

### binary_sensor.py (Module Health Sensors)

**Purpose:** Monitor health status of all 6 modules

**Sensors Created:**
```python
binary_sensor.secure_me_camera_health
binary_sensor.secure_me_lock_health
binary_sensor.secure_me_lights_health
binary_sensor.secure_me_climate_health
binary_sensor.secure_me_siren_health
binary_sensor.secure_me_tts_health
```

**Sensor States:**
- **ON:** Module healthy, all entities available
- **OFF:** Module unhealthy, issues detected
- **UNKNOWN:** Module disabled or not configured

**Health Checks:**
```python
class SecureMeHealthSensor(BinarySensorEntity):
    """Binary sensor for module health monitoring."""
    
    @property
    def is_on(self):
        """Return true if module is healthy."""
        # Check entity availability
        # Validate configuration
        # Verify module status
```

---

### sensor.py (Battery Level Sensors)

**Purpose:** Monitor battery levels for all battery-powered devices

**Auto-Discovery:**
```python
# Automatically finds all entities with device_class="battery"
sensor.secure_me_front_door_battery
sensor.secure_me_window_sensor_1_battery
sensor.secure_me_motion_detector_battery
# ... etc
```

**Features:**
- Auto-discovery of battery entities
- Battery level monitoring
- Low battery warnings (< 20%)
- Dashboard integration
- Informational tracking (doesn't affect test PASS/FAIL)

**Sensor Class:**
```python
class SecureMeBatterySensor(SensorEntity):
    """Battery level sensor."""
    
    @property
    def native_value(self):
        """Return battery percentage."""
        
    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT
```

---

## 🔌 Module System

### Base Module (modules/base.py)

**Abstract Base Class** for all modules

**Interface:**
```python
class BaseModule:
    def __init__(self, hass, config):
        self.hass = hass
        self.config = config
        self._enabled = config.get("enabled", False)
    
    async def async_arm(self, mode):
        """Called when alarm is armed."""
        
    async def async_disarm(self):
        """Called when alarm is disarmed."""
        
    async def async_triggered(self):
        """Called when alarm is triggered."""
        
    async def async_shutdown(self):
        """Cleanup on shutdown."""
        
    async def async_health_check(self):
        """Check module health status."""  # ✨ NEW
```

### Module Implementation Pattern

**Example: Camera Module**
```python
class CameraModule(BaseModule):
    def __init__(self, hass, config):
        super().__init__(hass, config)
        self._poe_switches = config.get("poe_switches", [])
        self._cameras = config.get("cameras", [])
        self._poe_delay = config.get("poe_delay", 120)
    
    async def async_arm(self, mode):
        # 1. Check if POE already on
        if all_poe_on:
            _LOGGER.info("POE already on - skip delay")
        else:
            # 2. Turn on POE ports
            await self._turn_on_poe()
            # 3. Wait for boot
            await asyncio.sleep(self._poe_delay)
            # 4. Set recording
            await self._set_recording_mode("continuous")
    
    async def async_health_check(self):
        """Check camera module health."""  # ✨ NEW
        # Check entity availability
        # Verify POE switch status
        # Validate camera feeds
        return {"healthy": True, "details": "..."}
```

---

## 🎨 Frontend Architecture

### secure-me-panel.js

**Single-File Component** (~3800 lines, expanded from ~1300)

**Structure:**
```javascript
class SecureMePanel extends HTMLElement {
    // Properties
    _hass = null;
    _activeTab = "sensors";
    _config = {};
    _testResults = {};  // ✨ NEW
    
    // Lifecycle
    connectedCallback() { ... }
    setConfig(config) { ... }
    set hass(hass) { ... }
    
    // WebSocket API
    async _callWS(command, data) { ... }
    
    // Testing Methods ✨ NEW
    async _runTest(level) { ... }
    async _getHealthStatus() { ... }
    async _getBatteryStatus() { ... }
    
    // Rendering
    _render() { ... }
    _renderTab() { ... }
    _renderSensors() { ... }
    _renderTestingTab() { ... }  // ✨ NEW
    // ... render methods for each tab
}

customElements.define("secure-me-panel", SecureMePanel);
```

**Tabs:**
1. **Sensors** - Sensor management
2. **Zones** - Zone configuration
3. **Users** - User & NFC management
4. **Modules** - Module configuration
5. **Automations** - Custom automations
6. **Settings** - System configuration
7. **Testing** - Health monitoring & test execution ✨ NEW

---

## 🌐 WebSocket API

### websocket_api.py (~800 lines, expanded from ~600)

**Commands:**
```python
# Configuration commands
@websocket_command("secure_me/get_config")
async def websocket_get_config(hass, connection, msg):
    """Return current configuration."""

@websocket_command("secure_me/update_zone")
async def websocket_update_zone(hass, connection, msg):
    """Update zone configuration."""

# Testing commands ✨ NEW
@websocket_command("secure_me/run_test")
async def websocket_run_test(hass, connection, msg):
    """Run system test with specified level."""

@websocket_command("secure_me/get_test_results")
async def websocket_get_test_results(hass, connection, msg):
    """Get last test results."""

@websocket_command("secure_me/get_health_status")
async def websocket_get_health_status(hass, connection, msg):
    """Get module health status."""

@websocket_command("secure_me/get_battery_status")
async def websocket_get_battery_status(hass, connection, msg):
    """Get battery status for all sensors."""
```

**Message Format:**
```javascript
// Request
{
    type: "secure_me/run_test",
    id: 123,
    level: "standard"  // quick, standard, full
}

// Response
{
    id: 123,
    type: "result",
    success: true,
    result: {
        status: "PASS",
        duration: 58,
        modules: { ... },
        batteries: { ... }
    }
}
```

---

## 💾 Data Storage

### store.py (Persistent Storage)

**Purpose:** Save configuration and test results across restarts

**Storage Location:**
```
/config/.storage/secure_me.panel_config
```

**Data Structure:**
```json
{
    "version": 1,
    "key": "secure_me.panel_config",
    "data": {
        "zones": { ... },
        "users": { ... },
        "automations": { ... },
        "settings": { ... },
        "test_results": {
            "last_test": "2026-02-13T14:30:00",
            "last_result": "PASS",
            "history": [ ... ]
        }
    }
}
```

**Methods:**
```python
async def async_save(data):
    """Save data to storage."""
    
async def async_load():
    """Load data from storage."""
    
async def async_save_test_results(results):
    """Save test results."""  # ✨ NEW
```

---

## 🔄 Data Flow

### Arming Sequence

```
User clicks "Arm Away"
        ↓
Frontend sends WebSocket command
        ↓
Coordinator receives arm request
        ↓
State Machine validates transition
        ↓
Coordinator starts exit delay (30s)
        ↓
TTS announces countdown
        ↓
Exit delay expires
        ↓
State changes to "armed_away"
        ↓
Zone Manager activates zones
        ↓
Module Manager arms modules (parallel):
        ├─→ Camera: POE on + recording
        ├─→ Lock: Lock doors
        ├─→ Lights: Turn off
        ├─→ Climate: Eco mode
        ├─→ Siren: Ready
        └─→ TTS: "Armed Away"
        ↓
Health sensors update ✨ NEW
        ↓
Coordinator updates state
        ↓
Frontend receives state update
        ↓
UI shows "Armed Away" status
```

### Test Execution Sequence ✨ NEW

```
User clicks "Run Test" (Standard)
        ↓
Frontend sends test command via WebSocket
        ↓
Coordinator receives test request
        ↓
Test framework initializes
        ↓
Quick checks (configuration validation)
        ├─→ Module config structure
        ├─→ Required fields present
        └─→ Entity ID format
        ↓
Standard checks (entity availability)
        ├─→ Check all module entities exist
        ├─→ Verify entities are responsive
        └─→ Test entity state accessibility
        ↓
Health status updated for all modules
        ↓
Results compiled with scoring
        ↓
Test results saved to store
        ↓
Frontend receives results
        ↓
UI displays:
        ├─→ Overall result (PASS/FAIL)
        ├─→ Module health status
        ├─→ Duration and timestamp
        └─→ Detailed error messages (if any)
```

### Sensor Trigger Sequence

```
Sensor detects motion
        ↓
HA fires state change event
        ↓
Zone Manager checks sensor zone
        ↓
Zone Manager calls trigger callback
        ↓
Coordinator checks if zone is active
        ↓
State Machine transitions to "pending"
        ↓
Coordinator starts entry delay (30s)
        ↓
TTS announces countdown
        ↓
User has 30s to disarm
        ├─→ Disarm code entered → Disarmed
        └─→ Timeout → State = "triggered"
                ↓
        Module Manager triggers modules:
                ├─→ Siren: Sound alarm
                ├─→ Lights: Emergency blink
                ├─→ TTS: "Alarm triggered!"
                └─→ Notify: Send notifications
```

---

## 📦 Dependencies

### Home Assistant Requirements

```json
{
  "requirements": [],  // No external dependencies!
  "dependencies": [
    "frontend",
    "http",
    "websocket_api"
  ],
  "version": "0.3.0",
  "iot_class": "local_polling"
}
```

### Python Requirements

- Python 3.11+
- Home Assistant 2025.1.1+
- No external libraries needed

### Testing Requirements

```python
# requirements_dev.txt
pytest>=7.4.0
pytest-homeassistant-custom-component>=0.13.0
pytest-asyncio>=0.21.0
```

---

## 🔒 Security Considerations

### Code Storage
- PIN codes hashed (not stored in plain text)
- Stored in `.storage/core.config_entries`
- Encrypted at rest

### WebSocket Security
- Authenticated connections only
- Commands require active HA session
- Rate limiting on API calls

### Module Security
- Modules run with HA permissions
- Entity access controlled by HA
- No external network access

### Health Data Privacy
- Health status stored locally only
- Test results not transmitted externally
- Battery levels informational only

---

## 🧪 Testing Structure

### Test Organization (v0.3.0)

```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures with mocks
├── test_init.py                # Integration setup tests (8 tests) ✨ NEW
├── test_const.py               # Constants tests ✨ NEW
├── test_state_machine.py       # State logic tests ✨ NEW
├── test_modules.py             # Module tests ✨ NEW
├── test_sensors.py             # Sensor platform tests ✨ NEW
├── test_store.py               # Store tests ✨ NEW
├── test_files.py               # File structure tests ✨ NEW
└── test_diagnostics.py         # Diagnostics tests ✨ NEW
```

**Test Coverage:**
- 100 test cases total
- 8 integration tests
- Module-specific tests
- Platform tests
- Health monitoring tests
- Battery sensor tests

**Running Tests:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_init.py -v

# Run with coverage
pytest tests/ --cov=custom_components/secure_me
```

---

## 📈 Performance Metrics

### File Sizes (v0.3.0)

| Component | Size | Lines | Status |
|-----------|------|-------|--------|
| __init__.py | 6-7 KB | ~200 | ✅ Stable |
| coordinator.py | 18 KB | ~500 | ✅ Stable |
| state_machine.py | 10 KB | ~300 | ✅ Stable |
| zones.py | 9 KB | ~250 | ✅ Stable |
| websocket_api.py | 24 KB | ~800 | ✨ Expanded |
| secure-me-panel.js | 120 KB | ~3800 | ✨ Expanded |
| binary_sensor.py | 6 KB | ~200 | ✨ NEW |
| sensor.py | 8 KB | ~250 | ✨ NEW |
| base.py | 3 KB | ~100 | ✅ Stable |
| camera.py | 8 KB | ~250 | ✅ Stable |
| **Tests/** | 30 KB | ~1000 | ✨ NEW |

**Total Integration Size:** ~250 KB (up from ~150 KB)
**Test Suite Size:** ~30 KB
**Total Project Size:** ~280 KB

### Startup Performance

| Phase | Time | Activity |
|-------|------|----------|
| Load | <1s | Import modules |
| Init | 2-3s | Initialize coordinator |
| Setup | 1-2s | Setup platforms |
| Health Check | <1s | Initial health scan ✨ NEW |
| Ready | <6s | Integration ready |

### Test Execution Performance

| Test Level | Time | Checks Performed |
|------------|------|------------------|
| Quick | ~30s | Configuration validation |
| Standard | ~60s | + Entity availability |
| Full | ~90s | + Battery discovery |

---

## 🔧 Extension Points

### Adding New Modules

1. Create `modules/my_module.py`
2. Inherit from `BaseModule`
3. Implement async_arm/disarm/triggered
4. Implement async_health_check ✨ NEW
5. Add to `modules/__init__.py`
6. Import in `coordinator.py`
7. Add configuration schema
8. Add health sensor in binary_sensor.py

### Adding New Platforms

1. Create `my_platform.py`
2. Implement `async_setup_entry`
3. Add platform to `__init__.py` setup
4. Create entities
5. Register with coordinator
6. Add tests in `tests/test_my_platform.py`

### Adding New Tests

1. Create test file in `tests/`
2. Import fixtures from `conftest.py`
3. Use `@pytest.mark.asyncio` for async tests
4. Mock Home Assistant components
5. Assert expected behavior
6. Run with `pytest tests/test_*.py -v`

---

## 🎯 Quality Metrics (v0.3.0)

### Code Quality
- ✅ Type hints (partial coverage)
- ✅ Docstrings (all public methods)
- ✅ Error handling (comprehensive)
- ✅ Logging (debug/info/error levels)
- ✅ Async/await patterns throughout

### Test Coverage
- ✅ 100 test cases
- ✅ Integration tests
- ✅ Platform tests
- ✅ Module tests
- ✅ Health monitoring tests
- ✅ Mock fixtures for all components

### Documentation
- ✅ README.md (comprehensive)
- ✅ CHANGELOG.md (detailed)
- ✅ FEATURES.md (complete)
- ✅ STRUCTURE.md (this file)
- ✅ Installation guides
- ✅ Testing documentation
- ✅ API documentation

### Home Assistant Compliance
- ✅ Config entry based
- ✅ Modern entity naming
- ✅ Device registration
- ✅ DataUpdateCoordinator pattern
- ✅ Async/await throughout
- ✅ Unit test coverage
- ✅ No external dependencies

---

**Documentation Version:** 0.3.0  
**Last Updated:** 2026-02-13  
**Architecture:** Modular, event-driven, async, tested  
**Status:** Phase 3 Complete - Production Ready
