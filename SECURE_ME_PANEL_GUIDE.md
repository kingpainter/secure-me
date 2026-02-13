# 🎉 Secure Me Panel v0.3.0 - Installation & Testing Guide

## ✨ MAJOR NEW FEATURES:

### 🧪 Testing Framework
- **Three test levels:** Quick (~30s), Standard (~60s), Full (~90s)
- **Real-time test execution** with progress display
- **Health scoring system** (PASS/FAIL/UNKNOWN)
- **Test result persistence** across sessions
- **Detailed error reporting** with solutions

### 🏥 Health Monitoring
- **Module health sensors** for all 6 modules
- **Real-time availability checking**
- **Visual health indicators** on module cards
- **Auto-refresh** every 30 seconds
- **Dashboard integration** ready

### 🔋 Battery Tracking
- **Auto-discovery** of all battery entities
- **Battery level display** in testing tab
- **Low battery warnings** (< 20%)
- **Battery count indicator**
- **Dashboard integration** ready

### 📊 Testing Tab (NEW)
- Professional test execution interface
- Test level selection
- Real-time progress display
- Module health summary
- Battery status overview
- Test history log

---

## 📦 Installation (5 minutter)

### Trin 1: Backup Existing Panel

```bash
cd /config/custom_components/secure_me/frontend/
cp secure-me-panel.js secure-me-panel.js.backup_v1.0.0
```

### Trin 2: Upload New Panel File

**Option A: Via File Editor (Recommended)**
1. Open File Editor in Home Assistant
2. Navigate to `/config/custom_components/secure_me/frontend/`
3. Delete old `secure-me-panel.js`
4. Upload new `secure-me-panel-v0.3.0.js`
5. Rename to `secure-me-panel.js`

**Option B: Via SSH/Terminal**
```bash
cd /config/custom_components/secure_me/frontend/
# Upload secure-me-panel-v0.3.0.js via your preferred method
mv secure-me-panel-v0.3.0.js secure-me-panel.js
```

### Trin 3: Verify Integration Files

Ensure these files exist and are v0.3.0:
```bash
/config/custom_components/secure_me/
├── binary_sensor.py      # Health sensors
├── sensor.py             # Battery sensors
├── websocket_api.py      # Testing API
└── frontend/
    └── secure-me-panel.js
```

### Trin 4: Hard Refresh Browser Cache

**Critical Step!**
```
Windows/Linux: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

Alternatively, clear browser cache completely:
```
Chrome: Settings → Privacy → Clear browsing data
Firefox: Settings → Privacy → Clear History
Safari: Develop → Empty Caches
```

### Trin 5: Restart Home Assistant

```
Settings → System → Restart Home Assistant
```

Wait for full restart (typically 1-2 minutes)

### Trin 6: Verify Installation

1. **Check Version:**
   - Open Secure Me panel
   - Scroll to footer
   - Verify version shows "v0.3.0"

2. **Check Testing Tab:**
   - New "Testing" tab should be visible
   - Tab icon: 🧪
   - Click to access testing interface

3. **Check Logs:**
   - Settings → System → Logs
   - Filter: "secure_me"
   - Should show no errors

---

## 🧪 Using the Testing Framework

### First-Time Testing

#### Step 1: Access Testing Tab
```
Open Secure Me Panel → Click "Testing" tab (🧪 icon)
```

#### Step 2: Review Interface
You'll see:
- **Test Level Selector** - Choose Quick/Standard/Full
- **Module Health Summary** - Current health status
- **Battery Status** - Auto-discovered batteries
- **Test History** - Previous test results
- **Action Buttons** - Run Test, Refresh Status

#### Step 3: Select Test Level

**Quick Test (~30s)** - Choose if:
- You just changed configuration
- Want rapid validation
- Need basic health check

**Standard Test (~60s)** - Choose if: ⭐ **RECOMMENDED**
- Running regular health checks
- Post-installation verification
- Troubleshooting issues

**Full Test (~90s)** - Choose if:
- Need complete validation
- Pre-production testing
- Comprehensive diagnostics
- Want battery status included

#### Step 4: Run Test
1. Click "Run Test" button
2. Watch real-time progress bar
3. Monitor module checks as they complete
4. Wait for final results

#### Step 5: Review Results

**Test Completed Display:**
```
┌──────────────────────────────────┐
│ Test Result: PASS ✅             │
│ Duration: 58 seconds              │
│ Timestamp: 2026-02-13 14:30:00   │
├──────────────────────────────────┤
│ Module Health:                    │
│ ✅ Camera   - Healthy             │
│ ✅ Lock     - Healthy             │
│ ✅ Lights   - Healthy             │
│ ✅ Climate  - Healthy             │
│ ✅ Siren    - Healthy             │
│ ✅ TTS      - Healthy             │
├──────────────────────────────────┤
│ Battery Status: (17 found)        │
│ ✅ 15 batteries OK (> 20%)        │
│ ⚠️ 2 batteries low (< 20%)        │
│   - Front door: 18%               │
│   - Window sensor 3: 15%          │
└──────────────────────────────────┘
```

#### Step 6: Address Issues (if any)

**If Test Shows FAIL:**
1. Click on failed module for details
2. Read error message
3. Fix configuration issue
4. Run test again
5. Repeat until PASS

**Common Issues:**
- Entity not found → Check entity ID
- Entity unavailable → Check device status
- Config invalid → Review module settings

---

## 🏥 Health Monitoring

### Understanding Health Sensors

**6 Health Binary Sensors Created:**
```yaml
binary_sensor.secure_me_camera_health
binary_sensor.secure_me_lock_health
binary_sensor.secure_me_lights_health
binary_sensor.secure_me_climate_health
binary_sensor.secure_me_siren_health
binary_sensor.secure_me_tts_health
```

**Sensor States:**
- **ON (Green ✅):** Module healthy, all entities available
- **OFF (Red ❌):** Module unhealthy, issues detected
- **UNKNOWN (Gray ❓):** Module disabled or not configured

### Viewing Health Status

**In Panel:**
1. Each module card shows health badge
2. Green ✅ = Healthy
3. Yellow ⚠️ = Warning
4. Red ❌ = Unhealthy

**In Dashboard:**
```yaml
type: entities
title: Module Health
entities:
  - binary_sensor.secure_me_camera_health
  - binary_sensor.secure_me_lock_health
  - binary_sensor.secure_me_lights_health
  - binary_sensor.secure_me_climate_health
  - binary_sensor.secure_me_siren_health
  - binary_sensor.secure_me_tts_health
```

### Health Checks Performed

**Entity Availability:**
- Verifies all configured entities exist
- Checks entities are responsive
- Tests entity state accessibility

**Configuration Validation:**
- Required fields present
- Valid entity IDs
- Proper data types
- Logical consistency

**Module Status:**
- Module enabled/disabled
- Last successful operation
- Error count tracking

### Auto-Refresh

Health status automatically refreshes:
- **Every 30 seconds** in panel
- **On module configuration changes**
- **After test execution**
- **Manual refresh available**

---

## 🔋 Battery Tracking

### Auto-Discovery Process

**Automatic Detection:**
Battery entities are discovered automatically:
1. Scans all entities with `device_class: battery`
2. Creates sensor for each battery found
3. Updates every 5 minutes
4. No manual configuration needed

**Example Discovered Batteries:**
```
sensor.secure_me_front_door_battery          (85%)
sensor.secure_me_window_sensor_1_battery     (72%)
sensor.secure_me_motion_detector_battery     (45%)
sensor.secure_me_smoke_detector_battery      (20%) ⚠️ LOW
```

### Battery Status Display

**In Testing Tab:**
- **Battery Count:** Shows total batteries found
- **Battery List:** All batteries with levels
- **Low Battery Warning:** Highlights < 20%
- **Critical Warning:** Highlights < 10%

**Color Coding:**
- **Green (> 50%):** Good battery level
- **Yellow (20-50%):** Consider replacement soon
- **Red (< 20%):** Replace battery soon
- **Red Blinking (< 10%):** Replace immediately

### Battery Monitoring

**Dashboard Integration:**
```yaml
type: entities
title: Battery Status
entities:
  - sensor.secure_me_front_door_battery
  - sensor.secure_me_window_sensor_1_battery
  - sensor.secure_me_motion_detector_battery
state_color: true
```

**Low Battery Automation:**
```yaml
automation:
  - alias: "Low Battery Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.secure_me_*_battery
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "Low Battery"
          message: "{{ trigger.to_state.name }}: {{ trigger.to_state.state }}%"
```

### Important Notes

**Battery Status is Informational:**
- Does NOT affect test PASS/FAIL
- Tracked separately from module health
- Useful for maintenance planning
- Prevents unexpected failures

---

## 📊 Test Levels Explained

### Quick Test (~30 seconds)

**What It Checks:**
- Module configuration structure
- Required fields present
- Entity ID format validation
- Basic syntax checks

**Use When:**
- Just changed configuration
- Need rapid validation
- Doing quick health check
- Pre-deployment verification

**Does NOT Check:**
- Entity availability
- Entity response times
- Battery status
- Full functionality

### Standard Test (~60 seconds) ⭐ RECOMMENDED

**What It Checks:**
- All Quick Test checks
- Entity availability verification
- Module health status
- Configuration consistency
- Entity response times

**Use When:**
- Regular health monitoring (daily/weekly)
- Post-installation verification
- Troubleshooting module issues
- After entity changes

**Does NOT Check:**
- Battery status (optional)
- Full end-to-end functionality
- Performance under load

### Full Test (~90 seconds)

**What It Checks:**
- All Standard Test checks
- Complete battery scan
- Integration health
- WebSocket connectivity
- End-to-end functionality
- Performance metrics

**Use When:**
- Complete system validation
- Pre-production deployment
- Comprehensive diagnostics
- Monthly/quarterly checks

**Includes:**
- Everything from Standard Test
- Battery discovery and levels
- Advanced diagnostics
- Performance measurements

---

## 🎯 Best Practices

### Testing Schedule

**Recommended Testing:**
```
Daily:    Quick Test (via automation)
Weekly:   Standard Test (manual)
Monthly:  Full Test (complete validation)
```

**After Changes:**
```
Config change:  Quick Test
Entity change:  Standard Test
Major update:   Full Test
```

### Health Monitoring

**Setup Alerts:**
```yaml
automation:
  - alias: "Module Health Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.secure_me_*_health
        to: 'off'
        for: "00:05:00"  # 5 minute delay to avoid false alarms
    action:
      - service: notify.mobile_app
        data:
          title: "Module Unhealthy"
          message: "{{ trigger.to_state.name }} needs attention"
```

**Daily Summary:**
```yaml
automation:
  - alias: "Daily Health Summary"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Secure Me Status:
            Modules: {{ states.binary_sensor | selectattr('entity_id', 'search', 'secure_me.*_health') | selectattr('state', 'eq', 'on') | list | count }}/6 healthy
            Low Batteries: {{ states.sensor | selectattr('entity_id', 'search', 'secure_me.*_battery') | selectattr('state', 'lt', '20') | list | count }}
```

### Battery Management

**Replacement Schedule:**
- **< 20%:** Plan replacement within 2 weeks
- **< 10%:** Replace within 1 week
- **< 5%:** Replace immediately

**Bulk Replacement:**
- Replace all batteries annually
- Mark replacement date in calendar
- Keep spare batteries on hand
- Test after replacement

---

## 🔧 Troubleshooting

### Testing Tab Not Showing

**Problem:** New Testing tab is not visible

**Solutions:**
1. **Hard refresh browser** (Ctrl+Shift+R)
2. **Clear browser cache completely**
3. **Check panel version in footer** (should be v0.3.0)
4. **Verify file upload successful**
5. **Restart Home Assistant**

### Test Execution Fails

**Problem:** Test won't run or crashes

**Solutions:**
1. **Check Home Assistant logs** (filter: secure_me)
2. **Verify all modules are configured**
3. **Check entity IDs are correct**
4. **Ensure entities are available**
5. **Run Quick Test first** to isolate issues
6. **Disable problematic module** and retry

### Health Status Shows Unknown

**Problem:** Health sensors show "Unknown" state

**Solutions:**
1. **Wait 30 seconds** for auto-refresh
2. **Click "Refresh Health Status"**
3. **Verify integration is loaded**
4. **Check coordinator is running**
5. **Run test to update status**
6. **Restart integration if needed**

### Battery Status Not Showing

**Problem:** No batteries discovered or displayed

**Solutions:**
1. **Verify battery entities exist**
2. **Check device_class is "battery"**
3. **Run Full Test** to trigger discovery
4. **Wait 1-2 minutes** for auto-discovery
5. **Check integration logs** for errors

### Module Configuration Issues

**Problem:** Module fails health check after configuration

**Solutions:**
1. **Open module configuration**
2. **Verify all entity IDs**
3. **Check entities are available** (Developer Tools → States)
4. **Save configuration again**
5. **Run Standard Test**
6. **Review error messages**

### Panel Performance Issues

**Problem:** Panel slow or unresponsive

**Solutions:**
1. **Clear browser cache**
2. **Check browser console** for errors
3. **Disable browser extensions**
4. **Try different browser**
5. **Check system resources** (CPU/RAM)
6. **Restart Home Assistant**

---

## 📱 Mobile Usage

### Mobile-Optimized Interface

**Testing Tab on Mobile:**
- Vertical scrolling layout
- Touch-friendly buttons
- Responsive text sizes
- Collapsible sections
- Easy navigation

**Best Practices:**
- Use landscape mode for better view
- Test results expand for details
- Tap health badges for quick info
- Swipe for history navigation

---

## 🔄 Upgrade from v1.0.0

### Pre-Upgrade Checklist

```
[ ] Backup current panel file
[ ] Note current module configurations
[ ] Export test history (if available)
[ ] Document any custom settings
[ ] Check Home Assistant version (2025.1.1+)
```

### Upgrade Steps

1. **Backup existing file**
2. **Upload new v0.3.0 file**
3. **Hard refresh browser**
4. **Restart Home Assistant**
5. **Verify Testing tab appears**
6. **Run Standard Test**
7. **Check all modules healthy**
8. **Review battery status**

### Post-Upgrade Verification

```
[ ] Panel version shows v0.3.0
[ ] Testing tab visible and functional
[ ] All module cards show health status
[ ] Health sensors created (6 total)
[ ] Battery sensors discovered
[ ] Test execution works
[ ] No errors in logs
```

---

## 📚 Additional Resources

### Documentation
- **Testing Framework Guide:** TESTING_FRAMEWORK_README.md
- **Main README:** README.md
- **Changelog:** CHANGELOG.md
- **Feature List:** FEATURES.md

### Support
- **GitHub Issues:** https://github.com/kingpainter/secure-me/issues
- **Discussions:** https://github.com/kingpainter/secure-me/discussions
- **Wiki:** https://github.com/kingpainter/secure-me/wiki

### Video Guides (Coming Soon)
- Panel installation walkthrough
- Testing framework tutorial
- Health monitoring setup
- Battery tracking configuration

---

## ❓ FAQ

**Q: Do I need to reconfigure modules after update?**
A: No, existing configurations load automatically.

**Q: Will battery tracking work with existing batteries?**
A: Yes, auto-discovery finds all battery entities automatically.

**Q: How often should I run tests?**
A: Weekly Standard Test recommended, Full Test monthly.

**Q: Can I automate testing?**
A: Command-line testing via pytest available, panel automation planned.

**Q: Does battery status affect alarm functionality?**
A: No, battery tracking is informational only.

**Q: What if a health check fails?**
A: Review error message, fix configuration, re-test until PASS.

**Q: Can I export test results?**
A: Export feature planned for v0.4.0.

**Q: How long are test results stored?**
A: Stored in browser localStorage indefinitely (or until cleared).

---

**Panel Version:** v0.3.0  
**Status:** Production Ready with Testing ✅  
**Last Updated:** 2026-02-13  
**Integration Version:** 0.3.0  
**Minimum HA Version:** 2025.1.1+

**Made with ❤️ for the Home Assistant Community**
