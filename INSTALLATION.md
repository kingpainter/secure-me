# Secure Me — Installation Guide

**Version:** 1.1.0  
**Requires:** Home Assistant 2025.1.1+

---

## Option 1: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations → Custom Repositories**
3. Add URL: `https://github.com/kingpainter/secure-me` — type: **Integration**
4. Search for **Secure Me** and click Install
5. Restart Home Assistant
6. Continue with [Initial Setup](#initial-setup)

---

## Option 2: Manual

1. Download the latest release from [GitHub Releases](https://github.com/kingpainter/secure-me/releases)
2. Unzip and copy the `custom_components/secure_me/` folder into your HA config:
   ```
   /config/custom_components/secure_me/
   ```
3. Restart Home Assistant
4. Continue with [Initial Setup](#initial-setup)

---

## Initial Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Secure Me** and click it
3. Fill in the setup form:

| Field | Description | Default |
|-------|-------------|---------|
| Alarm Code | PIN to arm/disarm (numbers only) | Required |
| Exit Delay | Seconds countdown after arming | 30 |
| Entry Delay | Seconds before alarm triggers on breach | 30 |
| Trigger Time | Seconds alarm stays triggered before auto-reset | 300 |

4. Click **Submit** — the integration loads
5. Open **Secure Me** from the HA sidebar

---

## First Configuration

### 1. Add Sensors (Sensors tab)

Go to the **Sensors tab** and enable the binary sensors you want to monitor — door contacts, motion sensors, window sensors, etc.

### 2. Create Zones (Zones tab)

Create at least one zone and assign your sensors to it. Choose a zone type:

| Type | When to use |
|------|-------------|
| Entry | Front door — gives you time to disarm |
| Instant | Window sensors — triggers immediately |
| Interior | Motion sensors — active when Armed Away |
| Perimeter | Garage sensors — active in all armed modes |

### 3. Enable Modules (Modules tab)

Enable the modules that match your hardware. Each module has a configure button — click it to set up entities. Changes take effect after restarting Home Assistant.

**TTS note:** When configuring the TTS module, select the service that matches your setup — `tts.cloud_say` for Nabu Casa, `tts.google_translate_say` for Google Translate, `tts.google_say` for Google Cast, or enter a custom service name.

### 4. Run a Test (Testing tab)

Run a **Quick Test** to verify entities are available, then a **Full Test** to check sensors and modules. A green result means you are ready.

---

## Updating

### Via HACS
HACS will notify you when a new version is available. Click Update, then restart HA.

### Manually
Replace the files in `/config/custom_components/secure_me/` with the new version, then restart HA.

After updating, always clear your browser cache:
- **Chrome / Edge:** `Ctrl+Shift+R`
- **Firefox:** `Ctrl+F5`
- **Safari:** `Cmd+Option+R`

---

## Uninstall

1. Go to **Settings → Devices & Services → Secure Me → Delete**
2. Remove the `custom_components/secure_me/` folder
3. Restart Home Assistant

---

## Troubleshooting

**Integration not showing up after install**
Make sure you restarted Home Assistant after copying the files.

**Panel blank after update**
Hard refresh your browser: `Ctrl+Shift+R`

**Alarm armed but sensors don't trigger**
Confirm your sensors are enabled in the Sensors tab and assigned to a zone in the Zones tab. Run a Full Test to see which sensors are offline.

**Enable debug logging**
Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.secure_me: debug
```
Then check logs at **Settings → System → Logs** (filter: `secure_me`).

**Download diagnostics**
Go to **Settings → Devices & Services → Secure Me → Download Diagnostics** for a full system snapshot to share when reporting issues.
