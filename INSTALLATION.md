# 📦 Installation Guide - Secure Me

Complete installation instructions for Secure Me alarm system integration.

---

## ⚙️ Prerequisites

### Required
- **Home Assistant:** 2025.1.0 or newer
- **Python:** 3.11+ (included with HA)
- **HACS:** Recommended for easy installation

### Optional
- **GitHub Account:** For manual installation
- **SSH Access:** For terminal installation

---

## 🚀 Installation Methods

### Method 1: HACS (Recommended)

**Step 1: Add Custom Repository**
1. Open HACS in Home Assistant
2. Click the three dots (⋮) in the top right
3. Select "Custom repositories"
4. Add: `https://github.com/kingpainter/secure-me`
5. Category: "Integration"
6. Click "Add"

**Step 2: Install Integration**
1. Search for "Secure Me" in HACS
2. Click on the integration
3. Click "Download"
4. Restart Home Assistant

**Step 3: Configure**
1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Secure Me"
4. Follow the setup wizard

---

### Method 2: Manual Installation

**Step 1: Download Files**
```bash
# Option A: Git clone
cd /config
git clone https://github.com/kingpainter/secure-me.git temp_secure_me
cp -r temp_secure_me/custom_components/secure_me custom_components/
rm -rf temp_secure_me

# Option B: Download ZIP
# Download from GitHub → Extract → Copy secure_me folder
```

**Step 2: Verify Structure**
```
/config/
└── custom_components/
    └── secure_me/
        ├── __init__.py
        ├── manifest.json
        ├── const.py
        ├── config_flow.py
        ├── alarm_panel.py
        ├── binary_sensor.py
        ├── sensor.py
        ├── switch.py
        ├── select.py
        ├── strings.json
        └── translations/
            ├── en.json
            └── da.json
```

**Step 3: Restart Home Assistant**
```
Settings → System → Restart
```

**Step 4: Add Integration**
```
Settings → Devices & Services → Add Integration → "Secure Me"
```

---

## 🔧 Configuration

### Initial Setup

**Via GUI (Recommended):**
1. Settings → Devices & Services
2. Add Integration → "Secure Me"
3. Enter configuration:
   - **Alarm Code:** 4+ digits (e.g., "1811")
   - **Exit Delay:** 0-120 seconds (default: 30)
   - **Entry Delay:** 0-60 seconds (default: 30)
4. Click "Submit"

**Configuration Options:**
- **Alarm Code:** Used for arming/disarming
- **Exit Delay:** Time to leave before arming
- **Entry Delay:** Time to disarm after entry

---

## ✅ Verification

### Check Installation

**1. Integration Loaded:**
```
Settings → Devices & Services → Look for "Secure Me"
```

**2. Device Created:**
```
Settings → Devices & Services → Secure Me → Device: "Secure Me Alarm System"
```

**3. Entity Created:**
```
Developer Tools → States → Search "alarm_control_panel.secure_me_alarm"
```

**4. Logs Clean:**
```
Settings → System → Logs
# Should show: "Setting up Secure Me integration version 0.0.1"
```

---

## 🐛 Troubleshooting

### Integration Not Showing

**Problem:** Can't find "Secure Me" in integrations list

**Solutions:**
1. **Check files copied correctly:**
   ```bash
   ls -la /config/custom_components/secure_me/
   # Should show all .py files
   ```

2. **Check manifest.json:**
   ```bash
   cat /config/custom_components/secure_me/manifest.json
   # Should show valid JSON with domain "secure_me"
   ```

3. **Restart Home Assistant:**
   ```
   Settings → System → Restart
   ```

4. **Clear browser cache:**
   ```
   Ctrl + Shift + R (hard reload)
   ```

---

### Setup Fails

**Problem:** Setup wizard shows errors

**Solutions:**
1. **Check logs:**
   ```
   Settings → System → Logs
   Filter: "secure_me"
   ```

2. **Validate code length:**
   ```
   Code must be 4+ characters
   ```

3. **Check HA version:**
   ```
   Settings → About
   Version: 2025.1.0 or newer required
   ```

---

### Entity Not Created

**Problem:** Alarm panel entity doesn't appear

**Solutions:**
1. **Reload integration:**
   ```
   Settings → Devices & Services → Secure Me → ⋮ → Reload
   ```

2. **Check entity registry:**
   ```
   Developer Tools → States
   Search: "secure_me"
   ```

3. **Delete and re-add:**
   ```
   Settings → Devices & Services → Secure Me → Delete
   Then add again
   ```

---

## 🔄 Updates

### Via HACS
1. HACS will notify you of updates
2. Click "Update"
3. Restart Home Assistant

### Manual Updates
1. Download latest release
2. Replace files in `custom_components/secure_me/`
3. Restart Home Assistant

**Always backup before updating!**

---

## 🗑️ Uninstallation

### Remove Integration
1. Settings → Devices & Services
2. Find "Secure Me"
3. Click the three dots (⋮)
4. Click "Delete"
5. Confirm deletion

### Remove Files
```bash
rm -rf /config/custom_components/secure_me
```

### Restart
```
Settings → System → Restart
```

---

## 📝 Post-Installation

### Next Steps

1. **Configure Zones** (Phase 1)
   - Add sensors to zones
   - Define zone behaviors

2. **Enable Modules** (Phase 2)
   - Activate camera control
   - Setup lock integration
   - Configure lights

3. **Test System** (Phase 3)
   - Run comprehensive tests
   - Check health score
   - Verify all modules

---

## 🆘 Getting Help

**Problem not solved?**

1. **Check logs:**
   ```
   Settings → System → Logs
   Filter: "secure_me"
   ```

2. **Search existing issues:**
   - [GitHub Issues](https://github.com/kingpainter/secure-me/issues)

3. **Create new issue:**
   - Include HA version
   - Include log excerpts
   - Describe steps to reproduce

4. **Community forum:**
   - [Home Assistant Community](https://community.home-assistant.io/)

---

**Installation complete!** 🎉

Next: Read [FEATURES.md](FEATURES.md) to learn about all capabilities.
