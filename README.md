# Secure Me - Professional Home Alarm Manager

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/kingpainter/secure-me/releases)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.1.1+-green.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Ready-purple.svg)](https://hacs.xyz/)

A comprehensive Home Assistant custom integration for professional alarm system management with smart module control, testing framework, and health monitoring.

[!Secure Me Logo](https://raw.githubusercontent.com/kingpainter/secure-me/main/brands/secure_me/logo.png)

---

## 🎉 What's New in v0.3.0

### Testing & Monitoring System
- ✅ **Three-tier testing framework** (Quick, Standard, Full)
- ✅ **Module health monitoring** with binary sensors
- ✅ **Battery level tracking** with auto-discovery
- ✅ **WebSocket test API** for real-time execution
- ✅ **Frontend testing interface** in configuration panel
- ✅ **Health scoring system** (PASS/FAIL/UNKNOWN)
- ✅ **100 unit tests** with pytest framework

### Quality & Compliance
- ✅ Complete unit test suite
- ✅ Home Assistant compliance files
- ✅ HACS preparation materials
- ✅ Enhanced documentation
- ✅ Production-ready code quality

---

## 🚀 Features

### Core Alarm System
- **Multiple Arming Modes:** Away, Home, Night, Vacation
- **Zone Management:** Flexible sensor grouping with independent monitoring
- **Entry/Exit Delays:** Configurable countdown timers with visual feedback
- **Code Protection:** Secure PIN validation with lockout protection
- **State Machine:** Proper transitions with trigger detection
- **Real-time Monitoring:** Live status updates and sensor tracking

### Smart Module System (6 Modules)

#### 📷 Camera Module
- POE port control (smart delay optimization)
- Recording mode management
- Camera feed verification
- Integration with Vision network switch

#### 🔒 Lock Module
- Smart lock automation with retry logic
- Always-locked safety feature
- Status verification
- Failure recovery

#### 💡 Lights Module
- Automatic control on arm/disarm
- Emergency flash patterns
- Zone-based activation
- Brightness management

#### 🌡️ Climate Module
- Multi-zone temperature management
- Preset modes (Home, Away, Sleep)
- Energy optimization
- Smart scheduling

#### 🚨 Siren Module
- Multiple sound patterns
- Volume control
- Duration settings
- Emergency override

#### 🔊 TTS Module
- Danish voice support (Google TTS)
- Message templates
- Priority handling
- System notifications

### Testing Framework (NEW in v0.3.0)

#### Test Levels
- **Quick Test** (~30s): Basic configuration validation
- **Standard Test** (~60s): Full entity availability checks
- **Full Test** (~90s): Complete functionality verification + battery status

#### Health Monitoring
- Module health binary sensors (6 sensors)
- Real-time availability checking
- Configuration validation
- Status tracking in dashboard

#### Battery Tracking
- Auto-discovery of battery entities
- Battery level sensors
- Low battery warnings
- Dashboard integration
- Informational only (doesn't affect PASS/FAIL)

### Configuration Panel
- Modern responsive UI with sidebar navigation
- Real-time WebSocket communication
- Persistent configuration storage
- Six main sections:
  - **Sensors:** Overview and status
  - **Zones:** Configuration and management
  - **Users:** PIN code management
  - **Modules:** Smart module settings
  - **Automations:** Trigger templates
  - **Testing:** Health monitoring and test execution

---

## 📦 Installation

### Method 1: HACS (Recommended - Coming Soon)
1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click "+" and search for "Secure Me"
4. Click "Download"
5. Restart Home Assistant

### Method 2: Manual Installation

1. **Download the integration:**
   ```bash
   cd /config/custom_components/
   git clone https://github.com/kingpainter/secure-me.git secure_me
   ```

2. **Restart Home Assistant**

3. **Add integration:**
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"
   - Search for "Secure Me"
   - Follow the setup wizard

4. **Configure modules:**
   - Go to Settings → Devices & Services → Secure Me
   - Click "Configure"
   - Access the configuration panel
   - Set up your modules in the "Modules" tab

---

## 🔧 Configuration

### Initial Setup

**Required:**
- Alarm name
- PIN code (4-6 digits)
- Entry delay (seconds)
- Exit delay (seconds)

**Optional:**
- Module configuration
- Zone setup
- User management
- Automation templates

### Module Configuration

Each module can be individually:
- Enabled/disabled
- Configured with specific entities
- Customized for behavior
- Tested independently

**Example - Camera Module:**
```yaml
enabled: true
poe_port_1: switch.vision_poe_port_1
poe_port_5: switch.vision_poe_port_5
cameras:
  - camera.front_door
  - camera.back_yard
recording_mode: input_select.camera_recording
```

### Zone Configuration

Create flexible sensor groups:
```yaml
zones:
  - name: "Ground Floor"
    sensors:
      - binary_sensor.front_door
      - binary_sensor.kitchen_window
  - name: "Upstairs"
    sensors:
      - binary_sensor.bedroom_window
      - binary_sensor.bathroom_window
```

---

## 🧪 Testing

### Running Tests

**Via Configuration Panel:**
1. Open Secure Me panel
2. Go to "Testing" tab
3. Select test level (Quick/Standard/Full)
4. Click "Run Test"
5. View real-time results

**Via Command Line:**
```bash
# Run all tests
pytest custom_components/secure_me/tests/ -v

# Run specific test file
pytest custom_components/secure_me/tests/test_state_machine.py -v

# Run with coverage
pytest custom_components/secure_me/tests/ --cov=custom_components/secure_me
```

### Test Results

**Health Sensors:**
- `binary_sensor.secure_me_camera_health`
- `binary_sensor.secure_me_lock_health`
- `binary_sensor.secure_me_lights_health`
- `binary_sensor.secure_me_climate_health`
- `binary_sensor.secure_me_siren_health`
- `binary_sensor.secure_me_tts_health`

**Battery Sensors:**
- Auto-discovered from device_class "battery"
- Tracked separately (informational only)
- Low battery warnings available

---

## 📊 Dashboard Integration

### Example Lovelace Card

```yaml
type: vertical-stack
cards:
  - type: alarm-panel
    entity: alarm_control_panel.secure_me
    states:
      - arm_away
      - arm_home
      - arm_night
  
  - type: entities
    title: Module Health
    entities:
      - binary_sensor.secure_me_camera_health
      - binary_sensor.secure_me_lock_health
      - binary_sensor.secure_me_lights_health
      - binary_sensor.secure_me_climate_health
      - binary_sensor.secure_me_siren_health
      - binary_sensor.secure_me_tts_health
  
  - type: entities
    title: Battery Status
    entities:
      - sensor.secure_me_front_door_battery
      - sensor.secure_me_window_sensor_battery
      # More auto-discovered batteries...
```

---

## 🔍 Troubleshooting

### Common Issues

**Integration won't load:**
1. Check Home Assistant logs: Settings → System → Logs → Filter: `secure_me`
2. Verify all required entities exist
3. Run configuration check: Developer Tools → YAML → Check Configuration
4. Restart Home Assistant

**Module not working:**
1. Go to Testing tab in panel
2. Run test for specific module
3. Check health sensor status
4. Verify entity IDs in module configuration
5. Check entity availability

**Panel not accessible:**
1. Clear browser cache (Ctrl+Shift+R)
2. Verify panel registration in logs
3. Check WebSocket connection
4. Restart Home Assistant

**Tests failing:**
1. Check entity availability
2. Verify module configuration
3. Review test results in panel
4. Check logs for specific errors

### Debug Logging

Enable debug logging in `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.secure_me: debug
```

---

## 📚 Documentation

### Complete Guides
- [Installation Guide](INSTALLATION.md)
- [Quick Start Guide](QUICK_START.md)
- [Module Configuration Guide](MODULE_KONFIGURATION_GUIDE.md)
- [Zone Configuration Guide](ZONE_KONFIGURATION_GUIDE.md)
- [Panel Installation Guide](PANEL_INSTALL_GUIDE.md)
- [Testing Framework Guide](TESTING_FRAMEWORK_README.md)
- [Critical Fixes Guide](CRITICAL_FIXES_GUIDE.md)

### Development
- [Project Structure](STRUCTURE.md)
- [Feature List](FEATURES.md)
- [Changelog](CHANGELOG.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## 🛣️ Roadmap

### Phase 4 (v1.0.0) - Production Release
- [ ] Enhanced automation templates
- [ ] Complete diagnostics integration
- [ ] System health reporting
- [ ] HACS submission
- [ ] Brands repository merge
- [ ] Community testing
- [ ] Production documentation
- [ ] Final polish

### Future Features
- [ ] NFC tag integration
- [ ] Advanced parallel execution
- [ ] State backup/restore
- [ ] Cloud integration (optional)
- [ ] Mobile app companion
- [ ] Advanced analytics

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

### Development Setup

```bash
# Clone repository
git clone https://github.com/kingpainter/secure-me.git
cd secure-me

# Install development dependencies
pip install -r requirements_dev.txt

# Run tests
pytest tests/ -v

# Run linting
black custom_components/secure_me/
pylint custom_components/secure_me/
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Home Assistant community for excellent documentation
- All contributors and testers
- HACS for distribution platform
- Users providing feedback and bug reports

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/kingpainter/secure-me/issues)
- **Discussions:** [GitHub Discussions](https://github.com/kingpainter/secure-me/discussions)
- **Documentation:** [Full Documentation](https://github.com/kingpainter/secure-me/wiki)

---

## 📈 Statistics

- **Lines of Code:** ~8,000+
- **Test Coverage:** 100 test cases
- **Modules:** 6 smart modules
- **Platforms:** 5 (alarm, binary_sensor, sensor, switch, select)
- **Supported Languages:** English, Danish
- **Home Assistant Version:** 2025.1.1+

---

## ⭐ Show Your Support

If you find this integration useful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting features
- 📖 Improving documentation
- 🤝 Contributing code

---

**Made with ❤️ by [KingPainter](https://github.com/kingpainter)**

**Version:** 0.3.0  
**Last Updated:** February 13, 2026  
**Status:** Phase 3 Complete - Production Ready Next
