# 📁 Project Structure - Secure Me

Complete overview of the Secure Me project structure.

**Version:** 0.0.1  
**Updated:** 2026-02-01

---

## 📂 Repository Layout

```
secure-me/
├── .github/
│   └── workflows/
│       ├── validate.yaml       # HACS + Hassfest validation
│       └── pytest.yaml         # Automated testing
│
├── custom_components/
│   └── secure_me/
│       ├── __init__.py         # Integration entry point
│       ├── manifest.json       # Integration metadata
│       ├── const.py           # Constants & config
│       ├── config_flow.py     # GUI setup wizard
│       │
│       ├── alarm_panel.py     # Main alarm entity
│       ├── binary_sensor.py   # Binary sensors (placeholder)
│       ├── sensor.py          # Sensors (placeholder)
│       ├── switch.py          # Switches (placeholder)
│       ├── select.py          # Selects (placeholder)
│       │
│       ├── strings.json       # UI strings
│       └── translations/
│           ├── en.json        # English
│           └── da.json        # Danish
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration
│   └── test_init.py          # Basic tests (placeholder)
│
├── docs/                     # Future documentation
│
├── .gitignore               # Git ignore rules
├── hacs.json                # HACS configuration
├── requirements_dev.txt     # Development dependencies
│
├── README.md                # Main documentation
├── CHANGELOG.md             # Version history
├── INSTALLATION.md          # Installation guide
├── FEATURES.md              # Feature overview
├── LICENSE                  # MIT License
└── STRUCTURE.md            # This file
```

---

## 🔧 Core Files

### manifest.json
**Purpose:** Integration metadata for Home Assistant

**Contents:**
- Domain: `secure_me`
- Name: `Secure Me`
- Version: `0.0.1`
- Dependencies: None
- Config flow: Enabled

---

### const.py
**Purpose:** Constants and configuration defaults

**Defines:**
- Domain name
- Platform types
- Default values
- State constants
- Service names
- Event types

---

### __init__.py
**Purpose:** Integration setup and teardown

**Functions:**
- `async_setup_entry()`: Setup integration
- `async_unload_entry()`: Cleanup
- `async_reload_entry()`: Reload

---

### config_flow.py
**Purpose:** GUI configuration wizard

**Classes:**
- `SecureMeConfigFlow`: Initial setup
- `SecureMeOptionsFlow`: Settings changes

**Features:**
- Code validation
- Delay configuration
- Error handling

---

## 🎯 Platform Files

### alarm_panel.py
**Purpose:** Main alarm control panel entity

**Features:**
- Multiple arming modes
- Code validation
- State management
- Device integration

**Status:** ✅ Basic implementation

---

### binary_sensor.py
**Purpose:** Zone sensors, system status

**Planned:**
- Zone open/closed
- System armed
- Trigger status

**Status:** 🚧 Placeholder

---

### sensor.py
**Purpose:** Health, battery, statistics

**Planned:**
- Health score
- Battery levels
- Last test time

**Status:** 🚧 Placeholder

---

### switch.py
**Purpose:** Module controls

**Planned:**
- Camera control
- Light control
- Module enable/disable

**Status:** 🚧 Placeholder

---

### select.py
**Purpose:** Mode selectors

**Planned:**
- Test mode selection
- Camera recording mode
- Module configuration

**Status:** 🚧 Placeholder

---

## 🌍 Translation Files

### strings.json
**Purpose:** Base UI strings (English)

**Contains:**
- Config flow text
- Error messages
- Option flow text

---

### en.json
**Purpose:** English translations

**Status:** ✅ Complete

---

### da.json
**Purpose:** Danish translations

**Status:** ✅ Complete

---

## 🧪 Test Files

### conftest.py
**Purpose:** Pytest configuration

**Features:**
- HA test fixture setup
- Custom integration enabling

---

### test_init.py
**Purpose:** Basic integration tests

**Status:** 🚧 Placeholder

---

## 📚 Documentation Files

### README.md
**Purpose:** Main project documentation

**Sections:**
- Features overview
- Installation
- Quick start
- Roadmap

---

### CHANGELOG.md
**Purpose:** Version history

**Format:** Keep a Changelog standard

---

### INSTALLATION.md
**Purpose:** Detailed installation guide

**Sections:**
- Prerequisites
- Installation methods
- Verification
- Troubleshooting

---

### FEATURES.md
**Purpose:** Complete feature documentation

**Sections:**
- Core features
- Modules
- Testing
- Comparison with Alarmo

---

## 🔨 Development Files

### .gitignore
**Purpose:** Git ignore rules

**Ignores:**
- Python cache
- Virtual environments
- IDE files
- Test artifacts

---

### hacs.json
**Purpose:** HACS integration config

**Settings:**
- Name
- Domains
- HA version requirement

---

### requirements_dev.txt
**Purpose:** Development dependencies

**Includes:**
- pytest
- Home Assistant
- Code quality tools

---

## 🚀 GitHub Workflows

### validate.yaml
**Purpose:** HACS and Hassfest validation

**Runs on:** Push, Pull Request

**Jobs:**
- HACS validation
- Hassfest validation

---

### pytest.yaml
**Purpose:** Automated testing

**Runs on:** Push, Pull Request

**Matrix:**
- Python 3.11
- Python 3.12

---

## 📦 Future Structure (Planned)

### Phase 1 (Week 2)
```
secure_me/
├── coordinator.py         # State coordinator
├── state_machine.py       # Alarm state logic
└── zones.py              # Zone management
```

---

### Phase 2 (Week 3)
```
secure_me/
└── modules/
    ├── base.py           # Module interface
    ├── camera.py         # Camera module
    ├── lock.py           # Lock module
    ├── lights.py         # Lights module
    ├── climate.py        # Climate module
    ├── curtains.py       # Curtains module
    ├── water_leak.py     # Water leak module
    ├── siren.py          # Siren module
    └── tts.py            # TTS module
```

---

### Phase 3 (Week 4)
```
secure_me/
├── testing.py            # Test framework
└── health.py            # Health monitoring

tests/
├── test_state_machine.py
├── test_zones.py
├── test_modules.py
└── test_coordinator.py
```

---

## 📊 File Statistics

| Category | Files | Lines |
|----------|-------|-------|
| Core | 9 | ~500 |
| Tests | 3 | ~50 |
| Docs | 5 | ~1500 |
| Config | 4 | ~100 |
| **Total** | **21** | **~2150** |

---

## 🔄 Version Control

### Branches
- `main`: Stable releases
- `dev`: Development
- `feature/*`: Feature branches

### Commit Convention
```
type(scope): description

Types: feat, fix, docs, test, refactor, chore
Scope: core, module, test, docs
```

**Examples:**
```
feat(core): add state machine
fix(alarm): code validation
docs(readme): update roadmap
test(zones): add zone tests
```

---

## 📝 File Naming

### Python Files
- `snake_case.py`
- Descriptive names
- Platform suffix for platforms

### Documentation
- `UPPERCASE.md` for main docs
- `lowercase.md` for subdocs

### Tests
- `test_*.py` pattern
- Mirror source structure

---

**Structure is ready for development!** 🎉

Next: Begin Phase 1 implementation.
