# Secure Me v0.3.2

**Professional Alarm System Manager for Home Assistant**

A comprehensive custom integration delivering professional-grade alarm functionality with multi-zone support, smart module integration, health monitoring, and an intuitive configuration panel.

[![Version](https://img.shields.io/badge/version-0.3.2-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.1.1+-blue.svg)](https://www.home-assistant.io/)

---

## Key Features

### Core Alarm System
- **Multiple Arming Modes** - Away, Home, Night, Vacation with customizable delays
- **Zone Management** - Group sensors into logical zones with individual settings
- **Entry/Exit Delays** - Countdown timers with visual feedback
- **Code Protection** - Secure your alarm with PIN codes
- **State Machine** - Robust state transitions with proper error handling
- **Trigger Detection** - Intelligent alarm activation based on zone configuration

### Smart Module System (6 Modules)
- **Camera Module** - POE port control, recording mode management
- **Lock Module** - Smart lock automation with retry logic and always-locked safety
- **Lights Module** - Automatic control with emergency flash patterns
- **Climate Module** - Multi-zone temperature management
- **Siren Module** - Alarm sounds with multiple pattern support
- **TTS Module** - Danish voice notifications via Google TTS

### Testing & Monitoring
- **Three-Tier Testing** - Quick (30s), Standard (60s), Full (90s) test levels
- **Health Monitoring** - Binary sensors for each module showing health status
- **Battery Tracking** - Auto-discovered battery sensors with low battery warnings
- **System Health Integration** - 10 health metrics visible in Developer Tools
- **Enhanced Diagnostics** - 6 diagnostic sections for troubleshooting
- **Real-Time Updates** - WebSocket API for instant status changes

### Configuration Panel
- **Modern Interface** - Alarmo-style sidebar navigation
- **Dynamic Cards** - Module cards that adapt to configuration
- **Zone Configuration** - Visual interface for sensor grouping
- **User Management** - Easy user and code administration
- **Automation Templates** - Ready-to-use automation examples
- **Testing Dashboard** - Integrated test execution and results

---

## Screenshots

### Main Panel
Modern sidebar navigation with real-time status updates

### Zone Configuration
Visual interface for creating and managing sensor zones

### Module Settings
Configure all 6 smart modules from one interface

### Testing Dashboard
Execute tests and view detailed results with pass/fail breakdown

---

## Installation

### Method 1: Manual Installation

1. Download the latest release from GitHub
2. Copy the `secure_me` folder to your Home Assistant `custom_components` directory:
   ```
   /config/custom_components/secure_me/
   ```
3. Restart Home Assistant
4. Go to Settings → Devices & Services → Add Integration
5. Search for "Secure Me" and follow the setup wizard

### Method 2: HACS (Planned for v1.0.0)

HACS support is planned for the v1.0.0 production release.

---

## Quick Start Guide

### Initial Setup

1. **Add the Integration**
   - Settings → Devices & Services → Add Integration
   - Search for "Secure Me"
   - Follow the configuration wizard

2. **Configure Zones**
   - Open the Secure Me panel from the sidebar
   - Navigate to the "Zones" tab
   - Create zones and add your sensors

3. **Set Up Modules**
   - Navigate to the "Modules" tab
   - Enable desired modules (Camera, Lock, Lights, etc.)
   - Configure module-specific entities

4. **Add Users**
   - Navigate to the "Users" tab
   - Create users with PIN codes
   - Set user permissions

5. **Test Your System**
   - Navigate to the "Testing" tab
   - Run a Standard Test to verify configuration
   - Check that all modules are healthy

### Basic Usage

**Arming the Alarm:**
```yaml
service: alarm_control_panel.alarm_arm_away
target:
  entity_id: alarm_control_panel.secure_me
data:
  code: "1234"
```

**Disarming:**
```yaml
service: alarm_control_panel.alarm_disarm
target:
  entity_id: alarm_control_panel.secure_me
data:
  code: "1234"
```

---

## System Requirements

- **Home Assistant:** 2025.1.1 or newer
- **Python:** 3.11 or newer
- **Dependencies:** 
  - `aiofiles` - Async file operations
  - Standard Home Assistant components

---

## Module Configuration

### Camera Module
Controls POE cameras with power management and recording modes.

**Required Entities:**
- POE port switch (optional)
- Camera recording switch (optional)

**Features:**
- Power on/off control
- Recording mode switching (arm/disarm/trigger)
- Health monitoring

### Lock Module
Manages smart locks with automatic locking and retry logic.

**Required Entities:**
- Lock entity (required)

**Features:**
- Auto-lock on arm
- Auto-unlock on disarm
- Retry logic for failed operations
- Always-locked safety option

### Lights Module
Controls lighting with automatic patterns and emergency modes.

**Required Entities:**
- Light groups or individual lights

**Features:**
- Auto on/off on arm/disarm
- Emergency flash patterns on trigger
- Customizable brightness and colors

### Climate Module
Manages heating/cooling across multiple zones.

**Required Entities:**
- Climate entities (thermostats)

**Features:**
- Multi-zone support
- Temperature setpoint adjustment
- Auto mode switching
- Energy saving on arm

### Siren Module
Provides alarm sounds with pattern support.

**Required Entities:**
- Siren entity (required)

**Features:**
- Multiple sound patterns
- Volume control
- Duration settings
- Immediate activation on trigger

### TTS Module
Delivers voice notifications in Danish.

**Required Entities:**
- Media player with TTS support

**Features:**
- Danish language support
- Google TTS integration
- Status announcements
- Customizable messages

---

## Health Monitoring

### System Health Integration (v0.3.1)

Access comprehensive health metrics through Developer Tools → Info → System Health:

**10 Monitored Metrics:**
1. Integration status and version
2. Entity counts (total, enabled, disabled, per-platform)
3. Module health (enabled count, unhealthy modules)
4. Zone configuration (total zones, enabled zones)
5. User configuration (total users)
6. Battery sensor count
7. Test results (status, level, duration, pass/fail counts)
8. Store functionality (zones, users, modules, notifications, automations)
9. WebSocket API status (registered commands)
10. Coordinator status (last update, data availability)

### Binary Sensors

Six health sensors are automatically created:

- `binary_sensor.secure_me_camera_health`
- `binary_sensor.secure_me_lock_health`
- `binary_sensor.secure_me_lights_health`
- `binary_sensor.secure_me_climate_health`
- `binary_sensor.secure_me_siren_health`
- `binary_sensor.secure_me_tts_health`

**States:**
- `on` - Module healthy (all configured entities available)
- `off` - Module unhealthy (missing or unavailable entities)

### Battery Sensors

Automatically discovered battery entities are tracked with dedicated sensors showing:
- Current battery level (%)
- Device name
- Low battery warnings

---

## Testing Framework

### Test Levels

**Quick Test (30 seconds):**
- Module configuration validation
- Basic entity checks
- Ideal for quick verification

**Standard Test (60 seconds):**
- All Quick Test checks
- Entity availability verification
- Module health status
- Recommended for regular testing

**Full Test (90 seconds):**
- All Standard Test checks
- Complete module functionality
- Integration health verification
- Battery status tracking
- Most comprehensive testing

### Running Tests

**Via Panel:**
1. Open Secure Me panel
2. Navigate to "Testing" tab
3. Select test level (Quick/Standard/Full)
4. Click "Run Test"
5. View detailed results with pass/fail breakdown

**Via Service Call:**
```yaml
service: secure_me.run_test
data:
  level: "standard"
```

### Test Results

Tests are scored as:
- **PASS** - All critical checks successful
- **FAIL** - One or more critical failures
- **UNKNOWN** - Tests not run or incomplete

**Note:** Battery status is tracked separately and does NOT affect PASS/FAIL determination.

---

## Enhanced Diagnostics (v0.3.1)

Download comprehensive diagnostics via:
Devices & Services → Secure Me → 3-dot menu → Download Diagnostics

**6 Diagnostic Sections:**
1. **Configuration Summary** - Entry data, version, setup timestamp
2. **Performance Metrics** - Update status, timestamps, intervals
3. **Test Results** - Latest test status, level, duration, pass/fail details
4. **Entity Details** - Total count, enabled/disabled breakdown, per-platform counts
5. **WebSocket API Status** - Registered commands list
6. **Users Configuration** - User count and names (redacted data)

---

## API & Automations

### WebSocket API

The panel uses a comprehensive WebSocket API for real-time communication:

**Available Commands:**
- `secure_me/zones/list` - Get all zones
- `secure_me/zones/create` - Create new zone
- `secure_me/zones/update` - Update zone configuration
- `secure_me/zones/delete` - Remove zone
- `secure_me/users/list` - Get all users
- `secure_me/users/create` - Create new user
- `secure_me/users/update` - Update user settings
- `secure_me/users/delete` - Remove user
- `secure_me/modules/status` - Get module health status
- `secure_me/modules/update` - Update module configuration
- `secure_me/test/run` - Execute test framework
- `secure_me/test/results` - Get latest test results

### Service Calls

**Run Testing Framework:**
```yaml
service: secure_me.run_test
data:
  level: "standard"  # quick, standard, or full
```

**Arm Alarm:**
```yaml
service: alarm_control_panel.alarm_arm_away
target:
  entity_id: alarm_control_panel.secure_me
data:
  code: "1234"
```

**Trigger Alarm Manually:**
```yaml
service: alarm_control_panel.alarm_trigger
target:
  entity_id: alarm_control_panel.secure_me
```

### Automation Templates

Ready-to-use automation templates are available in the Automations tab of the panel.

**Example: Auto-Arm When Everyone Leaves**
```yaml
automation:
  - alias: "Auto-Arm Alarm When Away"
    trigger:
      - platform: state
        entity_id: group.all_persons
        to: 'not_home'
        for: '00:05:00'
    action:
      - service: alarm_control_panel.alarm_arm_away
        target:
          entity_id: alarm_control_panel.secure_me
        data:
          code: "1234"
```

---

## Troubleshooting

### Panel Not Showing in Sidebar

1. Verify integration is loaded:
   ```
   Settings → Devices & Services → Search for "Secure Me"
   ```

2. Check logs for panel registration:
   ```
   Settings → System → Logs → Filter: "secure_me"
   ```

3. Clear browser cache and hard refresh:
   - Chrome/Edge: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Firefox: `Ctrl+F5` (Windows) or `Cmd+Shift+R` (Mac)

4. Restart Home Assistant

### Alarm Not Triggering

1. Check zone configuration:
   - Zones must have sensors added
   - Zones must be enabled

2. Verify sensors are reporting correctly:
   - Check sensor states in Developer Tools → States

3. Run Standard Test to identify issues:
   - Panel → Testing tab → Run Standard Test

4. Check coordinator logs:
   ```bash
   grep "secure_me.coordinator" /config/home-assistant.log
   ```

### Module Health Shows Unhealthy

1. Verify all configured entities exist and are available
2. Check entity IDs are correct in module configuration
3. View diagnostics to see which entities are missing
4. Update module configuration to remove unavailable entities

### Configuration Not Persisting

1. Check `.storage` directory permissions:
   ```bash
   ls -la /config/.storage/secure_me_*
   ```

2. Verify disk space is available
3. Check logs for storage errors
4. Try recreating the configuration through the panel

---

## Development

### Project Structure

```
custom_components/secure_me/
├── __init__.py                 # Integration entry point
├── panel.py                    # Panel registration (Alarmo-style)
├── manifest.json               # Metadata (v0.3.1)
├── const.py                    # Constants + module definitions
├── config_flow.py             # GUI setup + options
├── coordinator.py              # DataUpdateCoordinator
├── state_machine.py           # Alarm state logic
├── zones.py                   # Zone management
├── module_manager.py          # Module lifecycle
├── store.py                   # Persistent storage
├── websocket_api.py           # WebSocket API
├── system_health.py           # System health monitoring
├── diagnostics.py             # Enhanced diagnostics
├── alarm_control_panel.py     # Main alarm entity
├── binary_sensor.py           # Module health sensors
├── sensor.py                  # Battery level sensors
├── modules/                   # Smart modules
│   ├── base.py
│   ├── camera.py
│   ├── lock.py
│   ├── lights.py
│   ├── climate.py
│   ├── siren.py
│   └── tts.py
├── frontend/
│   └── secure-me-panel.js     # Configuration panel
└── tests/                     # Unit test suite
    ├── test_const.py
    ├── test_state_machine.py
    ├── test_modules.py
    ├── test_sensors.py
    ├── test_store.py
    ├── test_files.py
    └── test_diagnostics.py
```

### Testing

Run unit tests:
```bash
pytest custom_components/secure_me/tests/ -v
```

Run specific test file:
```bash
pytest custom_components/secure_me/tests/test_state_machine.py -v
```

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

### Code Quality

- **UTF-8 Encoding:** All files use UTF-8 encoding
- **No Emojis:** Emojis are banned from code files to prevent corruption
- **Type Hints:** Python code uses type hints
- **Async/Await:** Modern async patterns throughout
- **Testing:** Comprehensive unit test coverage

---

## Version History

### v0.3.2 (Current - 2026-02-14)
**Documentation & Polish**

**Documentation Improvements:**
- Comprehensive README.md rewrite for production readiness
- Professional feature showcase with complete module descriptions
- Improved documentation structure and clarity
- Enhanced troubleshooting section with common issues and solutions
- Complete API and automation examples
- Clear roadmap to v1.0.0
- Technical architecture details
- Security features documentation

### v0.3.1 (2026-02-14)
**Phase 3 Complete - System Health & Panel**

**New Features:**
- System health integration with 10 health metrics
- Enhanced diagnostics with 6 diagnostic sections
- Panel registration via panel.py module (Alarmo-style)
- panel_custom dependency in manifest.json

**Improvements:**
- All emojis removed from codebase (UTF-8 safety)
- Improved module health detection
- Better entity availability checking
- Enhanced configuration validation

**Bug Fixes:**
- F1: Dropdown text readability (improved contrast)
- F2: TTS media player configuration persistence
- F3/F4: Module icons clickable when disabled
- F5: Camera health correct configuration display

### v0.3.0 (2026-02-12)
**Phase 3 - Testing Framework & Monitoring**
- Three-tier testing framework (Quick/Standard/Full)
- Module health monitoring via binary sensors
- Battery level tracking with auto-discovery
- Complete unit test suite (100 test cases)
- WebSocket test API
- Frontend testing interface

### v0.2.0 (2026-02-10)
**Phase 2 - Module System**
- All 6 smart modules implemented
- Module manager with lifecycle coordination
- Individual module configuration
- Base module class with common functionality
- Module health checking

### v0.1.0 (2026-02-08)
**Phase 1 - Core Logic**
- DataUpdateCoordinator implementation
- State machine with entry/exit delays
- Zone manager with trigger callbacks
- Code validation
- State tracking

### v0.0.1 (2026-02-05)
**Phase 0 - Foundation**
- Initial project structure
- Config flow implementation
- Basic alarm entity
- HACS compliance

*Full version history: See [CHANGELOG.md](CHANGELOG.md)*

---

## Roadmap

### Phase 4: Production Polish (Next - v1.0.0)
**Timeline:** 2-3 weeks

**Planned Features:**
- 10 ready-to-use automation templates
- Enhanced error handling improvements
- Edge case testing scenarios
- Production documentation updates
- HACS submission preparation
- Brands repository submission
- Community testing
- Final polish

**Requirements for v1.0.0:**
- All features complete and tested
- Full documentation
- HACS submission approved
- Brands repository merged
- User testing completed
- Community feedback integrated

---

## Support

### Documentation

- **Installation Guide:** [INSTALLATION.md](INSTALLATION.md)
- **Features Overview:** [FEATURES.md](FEATURES.md)
- **Project Structure:** [STRUCTURE.md](STRUCTURE.md)
- **Module Configuration:** Module-specific guides
- **Panel Guide:** [SECURE_ME_PANEL_GUIDE.md](SECURE_ME_PANEL_GUIDE.md)
- **Testing Guide:** [TESTING_FRAMEWORK_README.md](TESTING_FRAMEWORK_README.md)

### Getting Help

1. Check the [documentation](#documentation) first
2. Review [troubleshooting section](#troubleshooting)
3. Search existing GitHub issues
4. Create a new issue with:
   - Home Assistant version
   - Secure Me version
   - Diagnostic file (if possible)
   - Detailed description of the problem

### Reporting Bugs

Please include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Relevant log entries
- Diagnostic download (Devices & Services → Secure Me → Download Diagnostics)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Home Assistant Community** - For the amazing platform
- **Alarmo Integration** - Inspiration for panel implementation
- **Contributors** - Everyone who has helped improve Secure Me

---

## Technical Details

### Architecture

**DataUpdateCoordinator Pattern:**
- Central data management
- Efficient polling of entities
- Automatic retry logic
- State caching

**State Machine:**
- Robust state transitions
- Entry/exit delay handling
- Error recovery
- Event logging

**Module System:**
- Base class for common functionality
- Individual module lifecycle
- Health monitoring
- Dynamic enable/disable

**Storage:**
- JSON-based persistence
- Atomic writes
- Backup support
- Migration support

### Security

- **Code Protection:** PIN codes for arming/disarming
- **User Management:** Individual user permissions
- **Audit Trail:** All state changes logged with user attribution
- **Secure Storage:** Configuration encrypted at rest (Home Assistant feature)

---

**Project:** Secure Me - Professional Alarm System Manager  
**Developer:** KingPainter  
**GitHub:** https://github.com/kingpainter/secure-me  
**Version:** 0.3.2  
**Status:** Phase 3 Complete - Production Polish Next  
**License:** MIT

**Last Updated:** 2026-02-14
