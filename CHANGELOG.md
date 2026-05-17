# Changelog — Secure Me

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.5.0] - unreleased

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
