# Alarm Project "Secure Me" - Instructions for Claude 

# Project Name: Secure Me
**Final integration name:** Secure Me

## Project Overview
Home Assistant custom integration for alarm system management

**Current Version:** 0.0.1 (Phase 0 - Foundation Complete)  
**Developer:** KingPainter (GitHub Desktop user)  
**Status:** ✅ Basic integration working, ready for Phase 1  
**GitHub:** https://github.com/kingpainter/secure-me (to be published)

---

## Current Status (v0.0.1)

### ✅ What Works Now
- Integration loads successfully in Home Assistant
- GUI configuration flow (code + delays)
- Basic alarm control panel entity
- State changes: disarmed ↔ armed_away/home/night/vacation
- Options flow for changing settings
- Translations (English + Danish)
- Device registration
- No errors in logs

### 🚧 What's NOT Implemented Yet
- State machine with delays
- Code enforcement
- Zone management
- Sensor monitoring
- Trigger logic
- Module system (cameras, locks, lights, etc.)
- Testing framework
- Health monitoring

### 📋 Known Issues (FIXED)
1. ✅ Platform naming: alarm_control_panel.py (not alarm_panel.py) - FIXED
2. ✅ Options flow AttributeError - FIXED in v0.0.1

---

## Technology Stack

- **Platform:** Home Assistant custom integration
- **Language:** Python 3.11+
- **Framework:** Home Assistant Core 2025.1.1+
- **Quality Target:** Bronze minimum, aiming for Silver
- **Version Control:** Git via GitHub Desktop
- **License:** MIT

---

## Project Structure (Current)

```
custom_components/secure_me/
├── __init__.py                 # Integration entry point
├── manifest.json               # Metadata
├── const.py                    # Constants
├── config_flow.py             # GUI setup + options
├── alarm_control_panel.py     # Main alarm entity
├── binary_sensor.py           # Placeholder
├── sensor.py                  # Placeholder
├── switch.py                  # Placeholder
├── select.py                  # Placeholder
├── strings.json               # UI strings
└── translations/
    ├── en.json                # English
    └── da.json                # Danish
```

---

## Documentation Standard

### Required Files
```
├── CHANGELOG.md               # Version history
├── INSTALLATION.md            # Installation guide
├── README.md                  # Main documentation
├── FEATURES.md                # Feature description
├── STRUCTURE.md               # Project structure
├── QUICK_START.md             # Quick start guide
├── PROJECT_SUMMARY.md         # Delivery summary
├── GITHUB_DESKTOP_GUIDE.md    # GitHub Desktop guide
└── LICENSE                    # MIT License
```

All documentation files created and available in `/mnt/user-data/outputs/`

---

## Code Standards

### Version Consistency Rules

**CRITICAL:** Always update ALL of these when changing version:

1. **manifest.json** → `"version": "0.0.1"`
2. **const.py** → `VERSION = "0.0.1"` (constant)
3. **const.py** → `# VERSION = "0.0.1"` (comment at top)
4. **ALL .py files** → `# VERSION = "0.0.1"` (comment at top)
5. **CHANGELOG.md** → Add entry for version
6. **README.md** → Update if needed
7. **FEATURES.md** → Update if needed

### Semantic Versioning
```
MAJOR.MINOR.PATCH

0.0.1 - Phase 0 (Foundation)
0.1.0 - Phase 1 (Core - planned)
0.2.0 - Phase 2 (Modules - planned)
0.3.0 - Phase 3 (Testing - planned)
1.0.0 - Production release (planned)
```

---

## Home Assistant Compliance

### Required Patterns (v0.0.1)
- ✅ Config entry based (no YAML config)
- ✅ Config flow for setup
- ✅ Options flow for changes
- ✅ Device registration with DeviceInfo
- ✅ Modern entity naming (has_entity_name = True)
- ✅ Proper translations/ directory
- ✅ Platform files named correctly
- ✅ Async/await patterns throughout

### Planned for Phase 1+
- 🚧 DataUpdateCoordinator
- 🚧 State machine
- 🚧 Services
- 🚧 Events
- 🚧 Diagnostics
- 🚧 System health

---

## Development Workflow

### When Making Changes

1. **Always Ask First!**
   - ⚠️ Ask before major code changes
   - ⚠️ Ask before creating new files
   - ⚠️ Confirm approach with user

2. **Version Update Checklist:**
   ```
   [ ] manifest.json "version"
   [ ] const.py VERSION constant
   [ ] const.py # VERSION comment
   [ ] All .py files # VERSION comments
   [ ] CHANGELOG.md entry
   [ ] README.md (if needed)
   [ ] FEATURES.md (if needed)
   ```

3. **Testing Checklist:**
   ```
   [ ] No errors in logs
   [ ] Integration loads
   [ ] Entity appears
   [ ] States change correctly
   [ ] Options flow works
   [ ] HA config check passes
   ```

4. **Git Workflow:**
   ```
   main:     Stable releases only
   dev:      Active development
   feature:  New features
   
   User commits via GitHub Desktop
   ```

---

## Communication Style

### User Profile
- Technical background
- 9 years Home Assistant admin experience
- Danish speaker (English for code)
- New to Git/GitHub
- Prefers clear, step-by-step instructions

### Guidelines
- ✅ Short and precise
- ✅ Step-by-step when needed
- ✅ Always ask before major changes
- ✅ Always ask before new code
- ✅ Provide clear examples
- ✅ Explain technical terms

---

## Project Goal

### Secure Me - Professional Home Alarm Manager

**Core Alarm System:**
- Multiple arming modes (away, home, night, vacation)
- Zone management (living room, kitchen, garage, etc.)
- Sensor monitoring (motion, door/window contacts)
- Code protection
- Entry/exit delays

**Module System (Plugins):**
- 📷 **Camera:** POE control, recording modes
- 🔒 **Lock:** Smart lock control with retry
- 💡 **Lights:** Auto control, emergency blinking
- 🌡️ **Climate:** Multi-zone heating
- 🪟 **Curtain:** Auto raise/lower
- 💧 **Water Leak:** Leak detection
- 🚨 **Siren:** Alarm sounds
- 🔊 **TTS:** Danish voice messages
- 🍳 **Appliances:** Monitoring

**Advanced Features:**
- Comprehensive testing framework
- Health monitoring
- Battery tracking (17+ batteries)
- POE optimization (saves 120s)
- Parallel execution
- NFC integration
- State backup/restore

---

## Development Phases

### Phase 0: Foundation ✅ COMPLETE
**Status:** v0.0.1 released  
**What's done:**
- Integration structure
- Config flow
- Basic alarm entity
- Translations
- Documentation
- GitHub workflows

### Phase 1: Core Logic 🚧 NEXT
**Target:** v0.1.0  
**Estimated time:** 1-2 weeks  
**Files to create:**
```
coordinator.py      # State coordinator (~150 lines)
state_machine.py    # Alarm logic (~200 lines)
zones.py           # Zone management (~100 lines)
```

**Features:**
- State machine with proper delays
- Entry/exit countdown
- Code validation
- Zone-based sensor groups
- Open sensor detection
- Basic testing

### Phase 2: Modules 📝 PLANNED
**Target:** v0.2.0  
**Estimated time:** 2-3 weeks  
**Files to create:**
```
modules/
├── base.py        # Module interface
├── camera.py      # Camera control
├── lock.py        # Lock control
├── lights.py      # Light control
├── climate.py     # Climate control
├── curtains.py    # Curtain control
├── water_leak.py  # Leak detection
├── siren.py       # Siren control
└── tts.py         # TTS (Danish)
```

### Phase 3: Polish & Testing 📝 PLANNED
**Target:** v0.3.0  
**Estimated time:** 1-2 weeks  
**Features:**
- Testing framework
- Test dashboard
- Health monitoring
- Battery tracking
- Complete translations
- HACS submission

### Phase 4: Production 🎯 GOAL
**Target:** v1.0.0  
**Requirements:**
- All features working
- Complete testing
- Documentation complete
- HACS approved
- User testing done

---

## Reference Documentation

### Home Assistant Developer Docs
- Core: https://developers.home-assistant.io/docs/architecture/core
- Integrations: https://developers.home-assistant.io/docs/architecture_components
- Style guidelines: https://developers.home-assistant.io/docs/development_guidelines
- File structure: https://developers.home-assistant.io/docs/creating_integration_file_structure
- Manifest: https://developers.home-assistant.io/docs/creating_integration_manifest
- Config Flow: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
- Options Flow: https://developers.home-assistant.io/docs/config_entries_options_flow_handler
- DataUpdateCoordinator: https://developers.home-assistant.io/docs/integration_fetching_data/
- Services: https://developers.home-assistant.io/docs/dev_101_services
- Events: https://developers.home-assistant.io/docs/integration_events
- Testing: https://developers.home-assistant.io/docs/development_testing
- Quality Scale: https://developers.home-assistant.io/docs/integration_quality_scale_index/
- Platforms: https://developers.home-assistant.io/docs/creating_platform_index

### Project Resources
- GitHub: https://github.com/kingpainter/secure-me (to be published)
- HACS: (to be submitted)
- Code owner: kingpainter
- License: MIT
- Documentation: In /mnt/user-data/outputs/

---

## Language Guidelines

### Code & Documentation
- **Default:** English
- **Code comments:** English
- **Documentation:** English
- **Git commits:** English
- **Variable names:** English

### User-Facing Text
- **UI strings:** English (primary) + Danish (translation)
- **TTS messages:** Danish (Google products used)
- **Error messages:** English + Danish
- **Notifications:** Bilingual support

---

## Old Package System Reference

### Location
Old YAML-based package files available in `/mnt/project/` for reference:
```
alarm_system_core.yaml              # Helpers, timers, scripts
alarm_system_automations.yaml       # Automation logic
alarm_system_testing_v3_0_3.yaml   # Test framework
Security_Master.yaml                # NFC, parallel execution
dashboard_v3_0_3.yaml              # Dashboard
```

### Purpose
**Keep these files for Phase 1-3 development:**
- Reference for state machine logic
- Test framework patterns
- Module functionality examples
- NFC event handling
- Parallel execution patterns

**Delete after Phase 3 complete** (estimated 3-4 weeks)

---

## Session History

### Previous Development Session
**Date:** 2026-02-01  
**Transcript:** `/mnt/transcripts/2026-02-01-17-33-04-secure-me-ha-integration-phase0.txt`

**What was completed:**
- Complete Phase 0 foundation (29 files)
- Basic integration working in HA
- Fixed platform naming bug
- Fixed options flow bug
- Successful installation and testing
- All documentation created

**Current state:**
- v0.0.1 working and stable
- Integration loads without errors
- Arm/disarm works
- Options flow works
- Ready for Phase 1 development

---

## Quick Reference

### File Locations
```
Code:        /mnt/user-data/outputs/secure_me/
Tests:       /mnt/user-data/outputs/tests/
Workflows:   /mnt/user-data/outputs/.github/workflows/
Docs:        /mnt/user-data/outputs/*.md
Old files:   /mnt/project/ (YAML packages)
Transcript:  /mnt/transcripts/2026-02-01-17-33-04-*.txt
```

### Key Commands
```bash
# In Home Assistant:
Settings → Devices & Services → Secure Me
Settings → System → Logs (filter: secure_me)
Settings → System → Restart

# Check config:
Developer Tools → YAML → Check Configuration
```

### Common Tasks
```
Add integration:     Settings → Devices & Services → Add
Change settings:     Settings → Devices & Services → Secure Me → Configure
View logs:          Settings → System → Logs → Filter: secure_me
Restart:            Settings → System → Restart
```

---

## Version History Summary

### v0.0.1 (2026-02-01) - Phase 0 Complete ✅
- Initial release
- Basic integration structure
- Config flow + options flow
- Simple alarm entity
- Translations (EN + DA)
- Documentation complete
- Known bugs fixed

### v0.1.0 (Planned) - Phase 1
- State machine
- Zone management
- Entry/exit delays
- Code validation

### v0.2.0 (Planned) - Phase 2
- Module system
- All plugins

### v0.3.0 (Planned) - Phase 3
- Testing framework
- Health monitoring
- HACS ready

### v1.0.0 (Planned) - Production
- Full feature set
- Complete testing
- HACS approved

---

## Important Notes

### Critical Rules
1. ⚠️ **Always ask before making code changes**
2. ⚠️ **Always update ALL version numbers together**
3. ⚠️ **Test before committing to GitHub**
4. ⚠️ **Keep old YAML files for reference**
5. ⚠️ **Platform files must match Platform enum exactly**

### Success Criteria
- ✅ No errors in HA logs
- ✅ Integration loads on restart
- ✅ Entity appears and works
- ✅ Config/options flow works
- ✅ All version numbers match

### Next Steps
1. Fix alarm_control_panel.py + config_flow.py in HA
2. Test that everything works
3. Commit v0.0.1 to GitHub
4. Plan Phase 1 development
5. Start coordinator.py implementation

---

**Last Updated:** 2026-02-01  
**Version:** 0.0.1  
**Status:** Phase 0 Complete - Ready for Phase 1  
**Developer:** KingPainter  
**Project:** Secure Me - Home Alarm Manager
