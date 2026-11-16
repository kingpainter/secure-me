# Secure Me — Test System Description

## Overview

The Test tab provides three levels of automated system verification plus individual module tests. Results are stored (last 10 runs) and displayed as pass, warning or fail.

---

## Test Levels

Durations below are estimates, not measurements.

### Quick Test
**Purpose:** Fast vital-signs check. Safe to run at any time — no services are called, no devices are activated.

**What it checks:**
- Entity availability for all enabled modules (is each configured entity reachable in HA?)
- Enabled modules with zero entities configured → Warning
- Disabled modules → Skipped
- Environmental sensors (smoke, water leak): available in HA? Runs on every test level, including Quick. Offline → FAIL

**What it does NOT check:**
- Whether devices actually respond (no service calls)
- Battery levels
- Sensor signal quality

**Pass criteria:** All enabled modules have all configured entities available (state not `unavailable` or `unknown`), and all environmental sensors are online.

**Duration:** < 2 seconds

---

### Standard Test
**Purpose:** Full module verification including actual device response. May briefly activate devices (e.g. lock unlock/relock cycle, TTS test announcement).

**What it checks (everything in Quick, plus):**
- Calls `async_test()` on each enabled module — actual device interaction:
  - **Camera:** POE switch availability, recording entity state
  - **Lock:** Brief unlock + relock cycle (skipped if the door sensor reports open, or if no person entity is `home`)
  - **Lights:** Brief flash test on first configured light
  - **Climate:** Entity availability + preset mode support
  - **Siren:** each configured siren, switch or input_boolean entity is turned on for 2 seconds at 50% volume; the legacy Xiaomi gateway gets a 2-second ringtone at 30% volume and a red/blue light flash
  - **TTS:** Test announcement on configured media players
- Battery discovery — `device_class: battery` sensors on the same devices as the configured sensors, levels reported (a low level adds a warning, never a FAIL)

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
- `warning` — no failures, but at least one warning (an enabled module with no entities, or a module warning such as a low battery or a climate without away mode)
- `fail` — one or more FAIL or ERROR results
- There is no `critical` overall value in the code. Overall is `pass`, `warning`, `fail`, or `error`. `error` is only set when the coordinator is missing. A failed siren test makes overall `fail`. The severity table above describes per-module statuses

**Battery results are informational** — a low or critical battery adds a warning line and can make the overall result `warning`, but never causes a FAIL.

---

## What Each Module Tests

> Checked against the module classes in `modules/` on 2026-11-16. Each module's `async_test()` runs at Standard and Full level, and in an individual-module run with the module id as `test_type`.

### Camera Module
- POE switch entities: available in HA?
- Camera entities: available in HA?
- Recording entities: available in HA?
- POE optimization status (already on = skip delay)
- Recording entities: reported with their current mode; they do not affect PASS/FAIL
- If POE was OFF before the test, it is turned back OFF afterwards; a failed restore → FAIL

### Lock Module
- Lock entities: available in HA?
- Battery sensors: level reported (warning if < 20%)
- Door sensors: state reported
- Functional cycle: if the lock starts locked, unlock → verify → relock → verify; if it starts unlocked, lock → verify
- Skipped if door sensor reports open (cannot lock open door)
- Skipped if no person entity is `home` (no unlock/relock with nobody there); counted as passed

### Lights Module
- Light entities (flash and steady lights): available in HA?
- Brief red flash on first light (0.5s on, then off)
- Backup check: state is backed up and the backup is stored (no restore step)

### Climate Module
- Climate entities: available in HA?
- Current temperature, target temperature, preset mode reported
- Warning if no `away` preset and no `away_temperature` configured

### Siren Module
- Siren, switch and input_boolean entities: available in HA? Each is turned on and back off after 2 seconds; an unsupported domain → FAIL
- Legacy Xiaomi gateway: ringtone test at volume 30% for 2 seconds, gateway light availability, red/blue flash test

### TTS Module
- Media player entities: available in HA?
- Plays first enabled custom message as test announcement (at half volume)
- Reports each speaker's configured volume (not the live player volume)

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

## Trend vs. previous run

Each run is compared with the newest stored result. Batteries whose level fell are listed in `trend.battery_declining`. Entities that are unavailable now but were available last time are listed in `trend.newly_unavailable`. Trend data is informational and does not change the overall result.

## Test Result Storage

- Every run is appended with `async_append_test_result`, which keeps the newest 10 results under `test_history` in the panel store (`secure_me.panel_config`)
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
| Overall FAIL but no module FAIL | A sensor is offline: enabled sensors (Full test) or environmental sensors (any test) | Check sensor status in the test details |
