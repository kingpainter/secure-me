# Secure Me — Professional Home Alarm Manager

A comprehensive alarm system integration for Home Assistant with multi-zone support, modular architecture, and a modern configuration panel.

---

## What is Secure Me?

Secure Me turns Home Assistant into a full-featured alarm system. You configure your door/window sensors into zones, enable the smart modules you need, and the system handles everything — from exit countdowns to locking doors, flashing lights, sounding sirens, and announcing via TTS when the alarm triggers.

---

## Key Features

**Alarm System**
- Four modes: Away, Home, Night, Vacation
- Configurable exit and entry delays
- Auto-reset after trigger time
- Code-protected operation

**Zone Management**
- Entry, Instant, Interior, and Perimeter zone types
- Each zone groups multiple binary sensors
- Sensor debouncing prevents false alarms from flapping sensors

**6 Smart Modules**
- **Camera** — Enables recording and controls POE switches on alarm
- **Lock** — Locks smart locks when armed, unlocks when disarmed
- **Lights** — Controls lights and flashes them during alarm
- **Climate** — Sets away temperature when armed, restores on disarm
- **Siren** — Sounds alarm patterns via Xiaomi gateway or compatible devices
- **TTS** — Voice notifications via any TTS service (cloud_say, google_say, piper, custom)

**Health & Testing**
- Per-module health status visible directly on the Modules tab
- Battery auto-discovery with low/critical warnings
- Three test levels: Quick, Standard, Full
- Test history stored for the last 10 runs

**Configuration Panel**
- Modern sidebar UI — no YAML required
- Mobile-responsive with bottom navigation bar
- Real-time status updates via WebSocket
- Toast notifications instead of browser popups
- Environmental sensors always-on with forced notifications
- Fake Presence toggle to block automatic arming
- Sensor hide/exclude for irrelevant device trackers
- User to person tracker binding for presence automation
- Home Alone Monitor camera configuration

---

## Requirements

- Home Assistant 2025.1.1 or newer

---

## Installation

1. Install via HACS or copy `custom_components/secure_me/` to your config directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration → Secure Me**
4. Enter your alarm code and configure delays
5. Open the **Secure Me** panel from the sidebar

---

## Documentation

Full documentation, automation examples, and API reference: [GitHub](https://github.com/kingpainter/secure-me)
