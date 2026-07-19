# Changelog — Secure Me

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.5.0] - 2026-07-19

### Added

#### Floorplan
- New **Floorplan tab** — upload a PNG floor plan and draw rooms directly on the map
- Draw rooms as rectangles or free-form polygons
- Assign binary sensors to rooms; rooms glow when their sensors activate in Home Alone mode
- Mark doors and windows by dragging a line across a wall; assign door/window sensors for live open/close indication
- Door openings show a directional arc indicating swing side (standard architecture convention)
- Room labels visible in view mode (dimmed) with dashed room outline — not only in edit mode
- **Undo** (Ctrl+Z): up to 20 undo steps, with undo button in toolbar
- Keyboard shortcuts in edit mode: `R` rectangle, `P` polygon, `O` door/window, `Delete` delete selected, `Esc` cancel/exit, `Ctrl+Z` undo
- Tool titles show keyboard shortcuts as hints (`[R]`, `[P]`, `[O]`)
- Touch support: canvas drawing migrated from `mousemove`/`mouseup` to pointer events with `setPointerCapture` — works on tablets
- Sensor assignment via searchable flyout dropdown per room
- Door/window sensor assignment via dropdown filtered to `device_class`: door, window, opening, garage_door

#### Floorplan — HACS survival
- Floor plan PNG is now backed up as base64 in HA storage (`image_b64` field in `secure_me.panel_config`)
- On next HA startup after a HACS update, the PNG is automatically restored from backup if missing on disk
- Self-heal: missing PNG file now clears only `image_url` (not rooms/openings/sensor assignments) — rooms survive HACS updates
- New store methods: `async_clear_floorplan_image()`, `async_restore_floorplan_image_from_backup()`, `get_floorplan_image_b64()`

#### Floorplan — sensor dropdown stability
- `_fpFlyoutActive()` guard in `_render()`: main content rebuild is skipped while the sensor flyout is open, preventing inspector DOM teardown during sensor selection
- `set hass()` alarm-state gate and live-mode gate both respect `_fpFlyoutActive()`
- Flyout option selection uses `pointerdown` with `capture: true` and `stopImmediatePropagation()` — runs before and blocks the close-outside handler; selection is now reliable
- Close-outside handler runs without capture and never sees clicks on flyout options
- Flyout repositions correctly when panel scrolls (`onPanelScroll` listener on `#shell-main`)

#### Sensor options
- New **Allow Open** flag per sensor in the Sensors tab
- Sensors with `allow_open: true` are permanently bypassed at all arm times — skipped in open-sensor check and ready-mode calculation
- Useful for always-open windows, ventilation hatches, or intentionally excluded sensors
- `const.py`: new constant `ATTR_SENSOR_ALLOW_OPEN`
- `zones.py`: `get_auto_bypass_sensors()` and `_compute_ready_modes()` both respect `allow_open`
- `store.py`: `allow_open` field in sensor struct with migration `setdefault`

#### Force arm via WebSocket
- `arm_away` and `arm_home` WebSocket endpoints now accept a `force: bool` parameter
- `force: true` bypasses the open-sensor check and arms regardless of sensor state
- Response now includes `bypassed_sensors` list so the frontend can show a bypass notification
- Existing mobile push `FORCE_ARM` action continues to work unchanged via coordinator

### Changed
- `websocket_api.py`: `ws_get_floorplan` self-heal now calls `async_clear_floorplan_image()` instead of `async_delete_floorplan()` — preserves room configuration when PNG is missing
- `websocket_api.py`: `ws_save_floorplan_image` passes `image_b64=raw_b64` to store so backup is saved immediately on upload
- `store.py`: `async_save_floorplan_image()` signature extended with optional `image_b64` parameter
- `store.py`: `async_delete_floorplan()` docstring updated to clarify it is a full destructive reset; use `async_clear_floorplan_image()` for image-only reset
- `store.py`: `_empty_floorplan()` includes `image_b64: None` field
- Room labels in SVG now use `data-fp-label` attribute and are rendered in non-live mode (dimmed, smaller font)
- Room polygons in view mode show a faint dashed stroke (opacity 0.2, `stroke-dasharray: 6,4`) so room outlines are visible without edit mode

### Fixed
- Sensor flyout closing before sensor could be selected (root cause: `preventDefault()` on `pointerdown` does not prevent `blur` on `<input>` across all browsers; fixed by using `pointerdown` with `capture: true` + `stopImmediatePropagation()`)
- Sensor flyout closing mid-scroll due to `mouseover`/`mouseout` events bubbling from child elements (replaced with `pointerenter`/`pointerleave`)
- Sensor flyout drifting away from input field when panel is scrolled
- `_render()` tearing down floorplan inspector DOM while sensor flyout was open, causing HA state updates (fired every second via `set hass()`) to interrupt sensor selection
- `coordinator.py`: scheduled test runner (`_check_scheduled_tests`) imported `_run_test_internal` from `.websocket_api`, but that function lives in `.ws_modules` and was never re-exported from `websocket_api.py` — every scheduled test run would have failed with `ImportError`. Found while wiring up `services.py` and fixed by importing from the correct module.

#### Control API
- New `services.py` registers the `secure_me.arm_away` / `arm_home` / `arm_night` / `arm_vacation` / `arm_home_alone` / `disarm` / `trigger` / `run_test` / `enable_module` / `disable_module` services with `hass.services.async_register()`. These were documented in `services.yaml` since early versions but had no backing handler -- calling them (e.g. from an automation) failed with "service not found". They now work and are unregistered cleanly on last config entry unload.
- `services.yaml`: added `force` field to all five arm services, matching what README.md already documented and what the coordinator methods already accepted
- `services.yaml`: added `arm_home_alone` entry (was previously undocumented despite the `SERVICE_ARM_HOME_ALONE` constant existing)
- `secure-me-alarm-card.js`: `arm_vacation` now goes through the standard `alarm_control_panel.alarm_arm_vacation` service instead of the `secure_me/arm_vacation` websocket command, now that `ARM_VACATION` is a first-class HA feature (since v1.4.3). Only `arm_home_alone` remains websocket-only, since HA's `alarm_control_panel` entity interface has no equivalent standard command for it.
- New `API.md`: formal, versioned documentation of the alarm entity's state mapping, attribute contract, and which arm/disarm modes use standard HA services vs. `secure_me.*` services vs. websocket -- replaces "read the code comments" as the source of truth
- `services.py`: `enable_module`/`disable_module` handlers now normalize the module config (via `ws_modules._normalize_module_config`) before calling `coordinator.update_module_config()`, matching what `ws_save_module` already does. Found during pre-commit self-audit -- without this, toggling a module via the service would have passed the store's raw panel-object config (e.g. `cameras: [{entity_id, poe_port}]`) straight into the module class, which expects flat entity_id string lists, silently breaking that module's entity extraction.

#### Zone sensor tracking (found via CI)
- `zones.py`: `Zone.update_sensor_state()` returned whether the zone's aggregate `is_triggered` flag flipped, not whether the specific sensor's own open/closed status changed. In a zone with two+ sensors, once one sensor was already open, a second sensor opening returned `changed=False` (True -> True), causing `_sensor_state_changed()` to return early before reaching the debounce check or the Home Alone door-notification dispatch. Concretely: two doors in the same zone, first door opens (dispatches fine), second door opens while the first is still open -- its notification is silently dropped. Caught by CI (`test_different_doors_debounced_independently`, added alongside the v1.5.0 debounce fix -- it's what exposed this pre-existing latent bug in the first place). Fixed by returning per-sensor membership change instead of the zone aggregate; verified against the exact test scenario before applying.

#### Etape 3: floorplan live-view parity (secure-me-alarm-card.js)
- The dashboard alarm card's Home Alone live-view only rendered room glow and opening fade -- it was missing individual sensor pin markers (`fp.markers`, for point-sensors not assigned to any room polygon) entirely, even though the panel's own "Alene-tilstand live" preview (`_renderFloorplanCanvas` in `secure-me-panel.js`) has always rendered these as pulsing red/green pins. A floorplan that looked complete when testing inside the panel was missing pins on the actual dashboard.
- Ported `_fpRenderSensorPinInner()` / `_sensorIsActive()` / `_sensorFriendlyName()` from `secure-me-panel.js` into `secure-me-alarm-card.js`; `_buildFloorplanSVGContent()` now also renders `svgSensorPins`.
- Found and fixed two supporting bugs while closing the gap: (1) `_loadDynamic()` never copied `fpRes.markers` into `this._floorplan` at all -- pins had no data to render even after the rendering code existed; (2) the live sensor-watch list in `set hass()` only tracked room/opening sensors, so a pin-only sensor's state change would never trigger a repaint once the initial view loaded.
- Verified with a functional smoke test (Node, stubbed DOM) asserting active/inactive pin color, presence/absence of the friendly-name label, and `data-fp-pin-active` state -- not just JS syntax validation.

#### Test suite: removed mirror-class anti-pattern in `test_zones_edge_cases.py`
- This file tested local copies of `Zone`/`ZoneManager` instead of the real `custom_components.secure_me.zones` classes -- the same anti-pattern that let the zone aggregate-vs-per-sensor bug (above) ship undetected. Rewrote all 28 tests to exercise the real classes via the real `hass` pytest fixture.
- While migrating, found the mirror's `test_unavailable_fires_notification` asserted a `persistent_notification` IS created for unavailable/unknown sensors -- but the real module has logged this at DEBUG with no notification since v1.4.2 (avoids alerting on routine Zigbee/WiFi flaps). The test had been silently asserting stale, pre-v1.4.2 behaviour. Corrected to `test_unavailable_does_not_fire_notification` asserting the real (current) behaviour.
- Added `test_different_sensors_debounced_independently` for the main (non-Home-Alone) `trigger_callback` path, mirroring the same regression test that caught the zone aggregate bug on the Home Alone dispatch path -- now covered on both code paths.

#### Dead code cleanup
- `__init__.py`: removed the duplicate local `PLATFORMS` list (was defining the exact same list independently of `const.PLATFORMS`, which only `test_const.py` actually read -- two sources of truth for the same list is a drift risk). Now imports `PLATFORMS` from `.const`, matching every other constant.
- Identified `module_manager.py` (215 lines, a `ModuleManager` class with its own `async_arm`/`async_disarm`/`async_test_all`) as fully dead code -- zero references anywhere else in the codebase. Superseded long ago by `coordinator.py`'s own `_init_modules()`/`_execute_modules_arm_*()`. Flagged for manual deletion (Claude does not delete files per project rules).

#### Architecture
- `websocket_api.py` split into four focused sub-modules: `ws_sensors.py`, `ws_modules.py`, `ws_floorplan.py`, `ws_alarm.py`
- New `ws_helpers.py` with shared `_get_store()` and `_get_coordinator()` helpers — eliminates four duplicate definitions
- `websocket_api.py` reduced from 2600 lines to 172 lines (entry point + imports only)

#### Alarm state
- `alarm_control_panel.py`: `state` property replaced with `alarm_state` override returning `AlarmControlPanelState` enum values — `armed_home_alone` maps to `ARMED_CUSTOM_BYPASS` for HA compatibility
- New `secure_me_mode` state attribute always exposes the true Secure Me coordinator state (e.g. `armed_home_alone`)
- Frontend panel now reads `secure_me_mode` attribute instead of `.state` — fixes panel showing "Disarmed" when Home Alone was active

#### Frontend stability
- `set hass()` reads `secure_me_mode` attribute from alarm entity — panel pill now shows correct state for all arm modes
- `_armingCountdown` also tracks open sensors and triggered-by sensor from entity attributes
- Status pill in `triggered` state now shows the triggering sensor's friendly name (truncated to 22 chars) instead of the generic "Triggered" label
- WS reconnect banner: subtle spinning indicator shown below topbar when WebSocket connection is lost; hides automatically on reconnect with 3s auto-retry of `_loadData()`
- Skeleton loading state: shimmer cards shown on first panel load before data arrives
- Module tab render cache: `_renderModules()` output cached by JSON fingerprint of modules + health data — skips re-render when data is unchanged, reducing DOM work on every `set hass()` call
- Sensor pin markers in floorplan live view: `fp.markers` positions shown as SVG pins, coloured red (active, with pulse ring) or green (inactive), with friendly name label on active sensors
- `&times;` entity reference replaces raw `✕` character in room inspector delete button

#### Startup robustness
- `async_setup_entry` retries `async_config_entry_first_refresh` up to 3 times with 2s delay before raising `ConfigEntryNotReady` — prevents integration failure on transient startup errors


---

## [1.4.3] - 2025-11-01

### Added
- Selective Fake Presence v2: block alarm, locks, or cameras independently
- Auto Actions v2: three independent action timers with individual delays on alarm trigger
- Arrival confirmation delay to prevent GPS flicker from resetting auto-arm timers
- Environmental sensors always-on section with forced notifications regardless of alarm state
- Sensor hide/exclude: hide irrelevant device trackers and auto-hidden sensors from the sensor list
- Sensor groups (anti-masking): require N sensors to activate within a configurable time window
- Per-sensor auto-bypass modes: choose which arm modes bypass a sensor if open at arm time
- Steady white lights: separate light list held at 100% brightness during alarm (no flash pattern)
- Live arming/pending countdown in sidebar status pill
- bcrypt PIN hashing — user codes never stored in plaintext (bcrypt rounds: 10)
- Mobile push actions: arm, disarm, force-arm directly from Companion app notification buttons
- Toast notification system — no browser popups
- In-panel confirm dialogs
- Home Alone Monitor camera configuration
- User to person tracker binding for presence automation
- Enhanced diagnostics download
- Test result history (last 10 runs)
- 2-column test dashboard: Last Run | History and Sensor Status | Battery Overview

### Changed
- Panel UI redesigned to Alarmo-inspired sidebar layout
- Config panel is now mobile-responsive with bottom navigation on small screens
- WebSocket API expanded to 51 endpoints
- Battery auto-discovery improved — tracks all HA devices with battery attributes

### Fixed
- State restore on HA restart — alarm stays armed, zone monitoring resumes immediately
- Auto-reset after trigger time no longer leaves alarm in permanent triggered state

---

## [1.4.2] - 2025-09-15

### Added
- Four arming modes: Away, Home, Night, Vacation
- Configurable exit delay and entry delay
- Multi-zone support with zone types: Entry, Instant, Interior, Perimeter
- 6 smart modules: Camera, Lock, Lights, Climate, Siren, TTS
- System health score with per-module status badges
- Battery monitoring with low/critical warnings
- Three test levels: Quick, Standard, Full
- Scheduled tests with configurable day, time, and type
- Sensor debouncing to prevent false alarms
- Per-sensor entry delay override
- Arm-on-close sensor option

---

## [1.0.0] - 2025-06-01

### Added
- Initial release
- Basic alarm control panel entity
- Away mode arming
- Binary sensor zone support
- Simple sidebar panel
- TTS notification support
