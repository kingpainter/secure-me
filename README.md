# Secure Me

**Professional Home Alarm Manager for Home Assistant**

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Version](https://img.shields.io/badge/version-0.3.6-blue.svg)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/tests-100%2F100-brightgreen.svg)](tests/)
[![HA](https://img.shields.io/badge/Home%20Assistant-2025.1%2B-brightgreen.svg)](https://www.home-assistant.io)

---

## Overview

Secure Me is a custom Home Assistant integration that turns your smart home into a complete alarm system. It combines zone management, multiple arming modes, and 6 smart modules — all controlled from a professional configuration panel with real-time monitoring.

---

## Features

### Alarm System
- **4 arming modes** — Away, Home, Night, Vacation
- **Zone management** — group sensors by area
- **Entry/exit delays** — configurable countdown timers
- **Code protection** — PIN validation
- **State tracking** — who armed, disarmed, or triggered

### 6 Smart Modules
| Module | Function |
|--------|----------|
| Camera | POE port control, recording management |
| Lock | Smart lock automation with retry logic |
| Lights | Auto control, emergency flash patterns |
| Climate | Multi-zone heating/cooling |
| Siren | Alarm sounds with multiple patterns |
| TTS | Danish voice notifications |

### Configuration Panel
- Modern sidebar navigation (Alarmo-style)
- Mobile-optimised with bottom navigation bar
- 7 tabs: Sensors, Zones, Users, Modules, Actions, Test, Future
- Real-time status via WebSocket

### Testing & Monitoring
- Three-tier test framework (Quick / Standard / Full)
- Module health monitoring (6 binary sensors)
- Battery auto-discovery with low/critical warnings
- System health integration (10 metrics)
- Enhanced diagnostics (6 sections)

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → Custom repositories
2. Add `https://github.com/kingpainter/secure-me` as Integration
3. Install **Secure Me**
4. Restart Home Assistant

### Manual

1. Copy `custom_components/secure_me/` to your HA `config/custom_components/`
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration → Secure Me

---

## Requirements

- Home Assistant 2025.1.1+
- Python 3.11+

---

## Usage

### Setup
1. Add integration via Settings → Devices & Services
2. Open **Secure Me** in the sidebar
3. Configure sensors, zones, users and modules
4. Run a Quick Test to verify everything works

### Panel Access
Sidebar → Secure Me

### System Health
Developer Tools → Info → System Health → secure_me

### Diagnostics
Settings → Devices & Services → Secure Me → Download Diagnostics

---

## Development

### Run tests
```bash
pytest tests/ -v
```

### Validate version consistency
```bash
python3 validate_version.py
```

### Validate encoding (no emojis)
```bash
python3 validate_encoding.py custom_components/secure_me/frontend/secure-me-panel.js
```

---

## Version History

See [CHANGELOG.md](CHANGELOG.md) for full history.

**Current:** v0.3.6 — Phase 3b complete (all 9 bugs fixed)  
**Next:** v0.4.0 — Enhanced error handling

---

## License

MIT — see [LICENSE](LICENSE)

---

*Secure Me by KingPainter*
