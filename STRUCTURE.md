# 🏗️ Secure Me - Project Structure

Complete technical documentation of the Secure Me integration architecture and file organization.

**Version:** 0.2.0  
**Last Updated:** 2026-02-06

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
├── 📄 store.py                       # Persistent storage
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
│   └── 📄 secure-me-panel.js        # Configuration dashboard (45-50 KB)
│
├── 🌐 API
├── 📄 websocket_api.py               # WebSocket commands
│
├── 🌍 Translations
├── 📁 translations/
│   ├── 📄 en.json                   # English
│   └── 📄 da.json                   # Danish
│
├── 🖼️ Assets
├── 📄 logo.png                       # Integration logo (1024×1024)
│
└── 📝 Platform Files (Placeholders for Phase 3)
    ├── 📄 binary_sensor.py
    ├── 📄 sensor.py
    ├── 📄 switch.py
    └── 📄 select.py
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
│  │  • Attributes: zones, sensors, modules             │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Smart Modules (6 total)                │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │  │
│  │  │Camera│ │ Lock │ │Lights│ │Climate│ │Siren │ ...│  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │          Frontend Panel (secure-me-panel.js)        │  │
│  │  • 7 tabs for configuration                        │  │
│  │  • WebSocket API integration                       │  │
│  │  • Real-time updates                               │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Persistent Storage (store.py)             │  │
│  │  • Configuration data                               │  │
│  │  • User preferences                                 │  │
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
    # 1. Initialize coordinator
    # 2. Register device
    # 3. Setup platforms
    # 4. Register WebSocket API
    # 5. Register frontend panel
    
async def async_unload_entry(hass, entry):
    """Unload config entry."""
    # 1. Cleanup modules
    # 2. Remove listeners
    # 3. Unload platforms
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
            await self._set_recording_mode("continuous")
        else:
            # 2. Turn on POE
            await self._turn_on_poe()
            # 3. Wait for boot
            await asyncio.sleep(self._poe_delay)
            # 4. Set recording
            await self._set_recording_mode("continuous")
```

---

## 🎨 Frontend Architecture

### secure-me-panel.js

**Single-File Component** (45-50 KB)

**Structure:**
```javascript
class SecureMePanel extends HTMLElement {
    // Properties
    _hass = null;
    _activeTab = "sensors";
    _config = {};
    
    // Lifecycle
    connectedCallback() { ... }
    setConfig(config) { ... }
    set hass(hass) { ... }
    
    // WebSocket API
    async _callWS(command, data) { ... }
    
    // Rendering
    _render() { ... }
    _renderTab() { ... }
    _renderSensors() { ... }
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
6. **Testing** - System tests
7. **Advanced** - Diagnostics

---

## 🌐 WebSocket API

### websocket_api.py

**Commands:**
```python
# Get configuration
@websocket_command("secure_me/get_config")
async def websocket_get_config(hass, connection, msg):
    """Return current configuration."""

# Update zone
@websocket_command("secure_me/update_zone")
async def websocket_update_zone(hass, connection, msg):
    """Update zone configuration."""

# Test module
@websocket_command("secure_me/test_module")
async def websocket_test_module(hass, connection, msg):
    """Test module functionality."""
```

**Message Format:**
```javascript
// Request
{
    type: "secure_me/get_config",
    id: 123
}

// Response
{
    id: 123,
    type: "result",
    success: true,
    result: { ... }
}
```

---

## 💾 Data Storage

### store.py (Persistent Storage)

**Purpose:** Save configuration across restarts

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
        "settings": { ... }
    }
}
```

**Methods:**
```python
async def async_save(data):
    """Save data to storage."""
    
async def async_load():
    """Load data from storage."""
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
Coordinator updates state
        ↓
Frontend receives state update
        ↓
UI shows "Armed Away" status
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
  "version": "0.2.0",
  "iot_class": "local_polling"
}
```

### Python Requirements

- Python 3.11+
- Home Assistant 2025.1.1+
- No external libraries needed

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

---

## 🧪 Testing Structure

### Test Organization (Phase 3)

```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures
├── test_coordinator.py         # Coordinator tests
├── test_state_machine.py       # State logic tests
├── test_zones.py              # Zone manager tests
├── modules/
│   ├── test_camera.py         # Camera module tests
│   ├── test_lock.py           # Lock module tests
│   └── ...
└── integration/
    ├── test_arm_disarm.py     # Full arm/disarm tests
    └── test_triggers.py       # Sensor trigger tests
```

---

## 📈 Performance Metrics

### File Sizes

| Component | Size | Lines |
|-----------|------|-------|
| __init__.py | 6-7 KB | ~200 |
| coordinator.py | 18 KB | ~500 |
| state_machine.py | 10 KB | ~300 |
| zones.py | 9 KB | ~250 |
| secure-me-panel.js | 45-50 KB | ~1500 |
| base.py | 3 KB | ~100 |
| camera.py | 8 KB | ~250 |

**Total Integration Size:** ~150 KB

### Startup Performance

| Phase | Time | Activity |
|-------|------|----------|
| Load | <1s | Import modules |
| Init | 2-3s | Initialize coordinator |
| Setup | 1-2s | Setup platforms |
| Ready | <5s | Integration ready |

---

## 🔧 Extension Points

### Adding New Modules

1. Create `modules/my_module.py`
2. Inherit from `BaseModule`
3. Implement async_arm/disarm/triggered
4. Add to `modules/__init__.py`
5. Import in `coordinator.py`
6. Add configuration schema

### Adding New Platforms

1. Create `my_platform.py`
2. Implement `async_setup_entry`
3. Add platform to `__init__.py` setup
4. Create entities
5. Register with coordinator

---

**Documentation Version:** 0.2.0  
**Last Updated:** 2026-02-06  
**Architecture:** Modular, event-driven, async
