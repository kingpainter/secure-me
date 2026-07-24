# Secure Me — Test System Description

## Overview

The Test tab provides three levels of automated system verification plus individual module tests. Results are stored (last 10 runs) and displayed with severity-weighted pass/fail/warn scoring.

---

## Test Levels

### Quick Test
**Purpose:** Fast vital-signs check. Safe to run at any time — no services are called, no devices are activated.

**What it checks:**
- Entity availability for all enabled modules (is each configured entity reachable in HA?)
- Enabled modules with zero entities configured → Warning
- Disabled modules → Skipped

**What it does NOT check:**
- Whether devices actually respond (no service calls)
- Battery levels
- Sensor signal quality

**Pass criteria:** All enabled modules have all configured entities available (state not `unavailable` or `unknown`).

**Duration:** < 2 seconds

---

### Standard Test
**Purpose:** Full module verification including actual device response. May briefly activate devices (e.g. lock unlock/relock cycle, TTS test announcement).

**What it checks (everything in Quick, plus):**
- Calls `async_test()` on each enabled module — actual device interaction:
  - **Camera:** POE switch availability, recording entity state
  - **Lock:** Brief unlock + relock cycle (skipped if door sensor reports open)
  - **Lights:** Brief flash test on first configured light
  - **Climate:** Entity availability + preset mode support
  - **Siren:** 2-second test ringtone + light flash
  - **TTS:** Test announcement on configured media players
- Battery discovery — all `device_class: battery` sensors scanned, levels reported (informational only, does not affect PASS/FAIL)

**Pass criteria:** Same as Quick + all `async_test()` calls succeed.

**Duration:** 10–60 seconds (depends on modules, POE delay excluded)

---

### Full Test
**Purpose:** Complete system verification including sensor signal quality and zone integrity. Most comprehensive — may take longer.

**What it checks (everything in Standard, plus):**
- **Sensor signal verification:** All enabled sensors checked for online/offline status
- Online count, offline count, per-sensor state reported
- Sensor offline → FAIL (sensor should always be reachable when system is healthy)

**Pass criteria:** Same as Standard + all enabled sensors online.

**Duration:** 15–90 seconds

---

### Individual Module Tests
**Purpose:** Test a single module in isolation without running the full suite. Uses the same `async_test()` logic as Standard Test for that module.

Available for each enabled module: Camera, Lock, Lights, Climate, Siren, TTS.

---

## Result Severity System

Results use a 4-level severity system:

| Status | Meaning | Affects overall? |
|---|---|---|
| `PASS` | All checks passed | — |
| `WARN` | Module enabled but not configured (no entities) | No — warning only |
| `FAIL` | Entity unavailable or device test failed | Yes → overall FAIL |
| `ERROR` | Exception during test execution | Yes → overall FAIL |
| `SKIP` | Module disabled or not selected | No |

**Overall result:**
- `pass` — no failures or errors
- `warning` — warnings only (unconfigured modules)
- `fail` — one or more FAIL or ERROR results
- `critical` — FAIL on siren, lock, or alarm cycle (highest severity modules)

**Battery results are always informational** — low/critical battery never causes a FAIL.

---

## What Each Module Tests

### Camera Module
- POE switch entities: available in HA?
- Camera entities: available in HA?
- Recording entities: available in HA?
- POE optimization status (already on = skip delay)

### Lock Module
- Lock entities: available in HA?
- Battery sensors: level reported (warning if < 20%)
- Door sensors: state reported
- Functional cycle: unlock → verify unlocked → relock → verify locked
- Skipped if door sensor reports open (cannot lock open door)

### Lights Module
- Light entities: available in HA?
- Brief flash test on first light (0.5s on, then off)
- Backup/restore state test

### Climate Module
- Climate entities: available in HA?
- Current temperature, target temperature, preset mode reported
- Warning if no `away` preset and no `away_temperature` configured

### Siren Module
- Gateway light entity: available in HA?
- 2-second ringtone test (volume 30% to avoid full alarm)
- Red/blue light flash test

### TTS Module
- Media player entities: available in HA?
- Plays first enabled custom message as test announcement
- Reports current volume level per player

---

## Future Test Additions (TODO)

| Test | Module | Priority | Notes |
|---|---|---|---|
| Push notification delivery | Notifications | Medium | Send test to admin, verify receipt |
| Sensor debounce verification | Zones | Medium | Rapid trigger, verify 500ms debounce |
| TTS quiet hours test | TTS | Low | Verify suppression during quiet period |
| Sensor group anti-masking | Zones | Medium | Single sensor trigger → should not alarm |
| Auto-bypass verification | Zones | Medium | Open sensor at arm time → verify bypass |
| bcrypt auth timing | Security | Low | Verify auth completes within 2s |
| Entry delay accuracy | Core | Medium | Verify countdown matches configured delay |
| Coordinator push actions | Push | Low | Test SECURE_ME_ARM_AWAY, etc. |

> Note: a full zone arm → trigger → disarm cycle test (`TestAlarmCycleTest`) was implemented in `tests/test_modules.py` since this list was written and is no longer a TODO.

---

## Test Result Storage

- Last 10 test results stored in HA storage (`secure_me.panel_config`)
- Results include: timestamp, duration, test_type, overall status, per-module details, battery snapshot
- History visible in Test tab

---

## Interpreting Common Failures

| Failure | Likely cause | Fix |
|---|---|---|
| Module FAIL — entity unavailable | Device offline or entity removed | Check device in HA, verify entity_id in module config |
| Module WARN — no entities | Module enabled but not configured | Open module settings, add entities |
| TTS FAIL — test announcement failed | Media player unavailable or TTS service wrong | Check media player entity, verify TTS service name |
| Lock FAIL — functional test failed | Lock unresponsive or door sensor issue | Check Z-Wave/Zigbee connection |
| Sensor FAIL — offline | Sensor unreachable | Check battery, Zigbee/Z-Wave mesh, entity registry |
| Overall FAIL but no module FAIL | Sensor offline (Full test only) | Check sensor status in Full test details |
