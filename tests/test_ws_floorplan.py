"""Tests for ws_floorplan.py -- floorplan WebSocket endpoints and their
supporting pure functions.

Before this file, ws_floorplan.py (added in v1.5.0, ~420 lines covering
image upload/validation, room/opening/marker persistence, deletion, and a
self-healing restore-from-backup path) had NO dedicated test coverage at
all -- a known gap called out explicitly in instructions_for_claude_secure_me.md
section 11.

This file covers, in order of risk:
  1. _read_png_dimensions() -- the hand-rolled PNG header parser (no
     external image library used). Malformed/truncated input must return
     None, never raise or return garbage dimensions.
  2. _normalise_markers() -- validates/cleans frontend-supplied marker data
     (legacy v1.5.0 format); out-of-range coordinates and wrong types must
     be dropped, not silently accepted.
  3. _floorplan_paths()/_legacy_floorplan_file() -- path construction, since
     a mistake here either serves a stale file or silently loses uploads.
  4. The WebSocket handlers themselves (ws_get_floorplan,
     ws_save_floorplan_image, ws_save_floorplan_markers,
     ws_delete_floorplan): input validation (size/format rejection),
     correct store calls, and correct connection.send_result/send_error
     usage -- exercised by calling the decorated handler functions directly
     with a fake connection, per the project's testing rule of using real
     production code rather than re-implemented mirrors.
"""
# VERSION = "1.0.0"

import base64
import struct
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.secure_me.ws_floorplan import (
    _read_png_dimensions,
    _normalise_markers,
    _floorplan_paths,
    _legacy_floorplan_file,
    ws_get_floorplan,
    ws_save_floorplan_image,
    ws_save_floorplan_markers,
    ws_delete_floorplan,
)
from custom_components.secure_me.const import FLOORPLAN_MAX_BYTES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_png_bytes(width: int, height: int, extra: bytes = b"\x00" * 100) -> bytes:
    """Build enough of a PNG byte string for _read_png_dimensions() to parse:
    signature + length + 'IHDR' + width + height, plus arbitrary padding.
    Not a real, fully-valid PNG (no CRC/IDAT/IEND) -- the function under
    test only reads the first 24 bytes, and the save handler only checks
    the header before writing bytes to disk as-is.
    """
    signature = b"\x89PNG\r\n\x1a\n"
    length = struct.pack(">I", 13)  # IHDR chunk data length, not itself checked
    header = signature + length + b"IHDR" + struct.pack(">II", width, height)
    return header + extra


class FakeConnection:
    """Minimal stand-in for websocket_api.ActiveConnection."""

    def __init__(self, is_admin: bool = True):
        self.send_result = MagicMock()
        self.send_error = MagicMock()
        self.user = MagicMock()
        self.user.is_admin = is_admin


class FakeFloorplanStore:
    """Minimal store stand-in exposing only what ws_floorplan.py calls."""

    def __init__(self, floorplan: dict | None = None):
        self._floorplan = floorplan or {
            "image_url": None, "width": 0, "height": 0, "markers": {},
        }
        self.async_save_floorplan_image = AsyncMock()
        self.async_restore_floorplan_image_from_backup = AsyncMock(return_value=None)
        self.async_clear_floorplan_image = AsyncMock()
        self.async_save_floorplan_rooms = AsyncMock()
        self.async_save_floorplan_markers = AsyncMock()
        self.async_delete_floorplan = AsyncMock()

    def get_floorplan(self):
        return self._floorplan


async def _call_ws_handler(handler, hass, connection, msg):
    """Call a @websocket_api.async_response-decorated handler and wait for
    it to actually finish.

    async_response wraps the real coroutine in a plain (non-async) function
    that schedules it via hass.async_create_task() and returns None --
    calling the decorated handler directly is NOT awaitable (awaiting the
    None it returns raises TypeError). The correct way to drive it from a
    test is to call it (fire-and-forget, as the real websocket_api dispatch
    loop does) and then let hass's task tracking settle before asserting.
    """
    handler(hass, connection, msg)
    await hass.async_block_till_done(wait_background_tasks=True)


# ---------------------------------------------------------------------------
# _read_png_dimensions()
# ---------------------------------------------------------------------------

class TestReadPngDimensions:
    def test_valid_header_returns_dimensions(self):
        data = _make_png_bytes(800, 600)
        assert _read_png_dimensions(data) == (800, 600)

    def test_wrong_signature_returns_none(self):
        data = b"NOTPNG\r\n\x1a\n" + b"\x00" * 20
        assert _read_png_dimensions(data) is None

    def test_missing_ihdr_marker_returns_none(self):
        signature = b"\x89PNG\r\n\x1a\n"
        data = signature + struct.pack(">I", 13) + b"XXXX" + struct.pack(">II", 100, 100)
        assert _read_png_dimensions(data) is None

    def test_too_short_returns_none(self):
        assert _read_png_dimensions(b"\x89PNG\r\n") is None

    def test_zero_width_returns_none(self):
        data = _make_png_bytes(0, 600)
        assert _read_png_dimensions(data) is None

    def test_zero_height_returns_none(self):
        data = _make_png_bytes(800, 0)
        assert _read_png_dimensions(data) is None

    def test_empty_bytes_returns_none(self):
        assert _read_png_dimensions(b"") is None

    def test_does_not_raise_on_garbage_input(self):
        """Defensive: arbitrary junk must never raise, only return None."""
        assert _read_png_dimensions(b"\xff" * 30) is None


# ---------------------------------------------------------------------------
# _normalise_markers()
# ---------------------------------------------------------------------------

class TestNormaliseMarkers:
    def test_valid_marker_is_kept(self):
        raw = {"binary_sensor.front_door": {"x_pct": 50.0, "y_pct": 25.0, "kind": "door", "label": "Front"}}
        result = _normalise_markers(raw)
        assert "binary_sensor.front_door" in result
        assert result["binary_sensor.front_door"]["x_pct"] == 50.0
        assert result["binary_sensor.front_door"]["kind"] == "door"

    def test_out_of_range_x_is_dropped(self):
        raw = {"binary_sensor.a": {"x_pct": 150.0, "y_pct": 50.0}}
        assert _normalise_markers(raw) == {}

    def test_negative_y_is_dropped(self):
        raw = {"binary_sensor.a": {"x_pct": 50.0, "y_pct": -5.0}}
        assert _normalise_markers(raw) == {}

    def test_non_numeric_coordinates_are_dropped(self):
        raw = {"binary_sensor.a": {"x_pct": "not_a_number", "y_pct": 50.0}}
        assert _normalise_markers(raw) == {}

    def test_missing_coordinates_are_dropped(self):
        raw = {"binary_sensor.a": {"kind": "door"}}
        assert _normalise_markers(raw) == {}

    def test_unknown_kind_defaults_to_motion(self):
        raw = {"binary_sensor.a": {"x_pct": 10, "y_pct": 10, "kind": "not_a_real_kind"}}
        result = _normalise_markers(raw)
        assert result["binary_sensor.a"]["kind"] == "motion"

    def test_non_string_label_is_dropped_to_none(self):
        raw = {"binary_sensor.a": {"x_pct": 10, "y_pct": 10, "label": 12345}}
        result = _normalise_markers(raw)
        assert result["binary_sensor.a"]["label"] is None

    def test_non_dict_entity_config_is_skipped(self):
        raw = {"binary_sensor.a": "not_a_dict"}
        assert _normalise_markers(raw) == {}

    def test_non_string_entity_key_is_skipped(self):
        raw = {123: {"x_pct": 10, "y_pct": 10}}
        assert _normalise_markers(raw) == {}

    def test_none_input_returns_empty_dict(self):
        assert _normalise_markers(None) == {}

    def test_non_dict_input_returns_empty_dict(self):
        assert _normalise_markers(["not", "a", "dict"]) == {}

    def test_boundary_values_zero_and_hundred_are_kept(self):
        raw = {"binary_sensor.a": {"x_pct": 0.0, "y_pct": 100.0}}
        result = _normalise_markers(raw)
        assert "binary_sensor.a" in result


# ---------------------------------------------------------------------------
# Path construction
# ---------------------------------------------------------------------------

class TestFloorplanPaths:
    def test_floorplan_paths_under_www_dir(self, hass):
        www_dir, floorplan_file = _floorplan_paths(hass)
        assert "www" in www_dir
        assert "secure_me_floorplan" in www_dir
        assert floorplan_file.startswith(www_dir)
        assert floorplan_file.endswith("floorplan.png")

    def test_legacy_path_under_custom_components(self, hass):
        legacy = _legacy_floorplan_file(hass)
        assert "custom_components" in legacy
        assert "secure_me" in legacy
        assert legacy.endswith("floorplan.png")

    def test_legacy_and_current_paths_differ(self, hass):
        _, current = _floorplan_paths(hass)
        legacy = _legacy_floorplan_file(hass)
        assert current != legacy


# ---------------------------------------------------------------------------
# ws_get_floorplan
# ---------------------------------------------------------------------------

class TestWsGetFloorplan:
    @pytest.mark.asyncio
    async def test_returns_defaults_when_store_missing(self, hass, monkeypatch):
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: None)
        connection = FakeConnection()

        await _call_ws_handler(ws_get_floorplan, hass, connection, {"id": 1})

        connection.send_result.assert_called_once()
        result = connection.send_result.call_args.args[1]
        assert result["image_url"] is None
        assert result["width"] == 0

    @pytest.mark.asyncio
    async def test_returns_stored_floorplan_when_file_present(self, hass, monkeypatch, tmp_path):
        www_dir, floorplan_file = _floorplan_paths(hass)
        import os
        os.makedirs(www_dir, exist_ok=True)
        with open(floorplan_file, "wb") as fh:
            fh.write(b"fake png bytes")

        store = FakeFloorplanStore(floorplan={
            "image_url": "/local/secure_me_floorplan/floorplan.png",
            "width": 800, "height": 600, "markers": {},
        })
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        await _call_ws_handler(ws_get_floorplan, hass, connection, {"id": 1})

        connection.send_result.assert_called_once()
        result = connection.send_result.call_args.args[1]
        assert result["width"] == 800
        store.async_clear_floorplan_image.assert_not_called()

        os.unlink(floorplan_file)

    @pytest.mark.asyncio
    async def test_self_heals_when_file_missing_and_no_backup(self, hass, monkeypatch):
        """If the store thinks an image exists but the file is gone and no
        backup is available, image metadata must be cleared -- but this
        must never raise, and rooms/markers are left untouched by the
        clear call itself (that's async_clear_floorplan_image's job)."""
        store = FakeFloorplanStore(floorplan={
            "image_url": "/local/secure_me_floorplan/floorplan.png",
            "width": 800, "height": 600, "markers": {},
        })
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        await _call_ws_handler(ws_get_floorplan, hass, connection, {"id": 1})

        store.async_clear_floorplan_image.assert_called_once()
        connection.send_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_backup_restore_error_does_not_crash_response(self, hass, monkeypatch):
        """Regression guard for the v1.5.1 self._image_store AttributeError:
        an unexpected exception from the restore path must degrade to
        clearing image metadata, never propagate and break the response."""
        store = FakeFloorplanStore(floorplan={
            "image_url": "/local/secure_me_floorplan/floorplan.png",
            "width": 800, "height": 600, "markers": {},
        })
        store.async_restore_floorplan_image_from_backup = AsyncMock(
            side_effect=AttributeError("boom")
        )
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        await _call_ws_handler(ws_get_floorplan, hass, connection, {"id": 1})

        store.async_clear_floorplan_image.assert_called_once()
        connection.send_result.assert_called_once()
        connection.send_error.assert_not_called()


# ---------------------------------------------------------------------------
# ws_save_floorplan_image
# ---------------------------------------------------------------------------

class TestWsSaveFloorplanImage:
    @pytest.mark.asyncio
    async def test_rejects_invalid_base64(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        await _call_ws_handler(ws_save_floorplan_image, hass, connection, {"id": 1, "image_base64": "not-valid-base64!!"})

        connection.send_error.assert_called_once()
        assert connection.send_error.call_args.args[1] == "invalid_base64"

    @pytest.mark.asyncio
    async def test_rejects_oversized_image(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        oversized = base64.b64encode(b"\x00" * (FLOORPLAN_MAX_BYTES + 1)).decode()

        await _call_ws_handler(ws_save_floorplan_image, hass, connection, {"id": 1, "image_base64": oversized})

        connection.send_error.assert_called_once()
        assert connection.send_error.call_args.args[1] == "image_too_large"

    @pytest.mark.asyncio
    async def test_rejects_non_png_data(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        not_png = base64.b64encode(b"this is definitely not a png").decode()

        await _call_ws_handler(ws_save_floorplan_image, hass, connection, {"id": 1, "image_base64": not_png})

        connection.send_error.assert_called_once()
        assert connection.send_error.call_args.args[1] == "invalid_png"

    @pytest.mark.asyncio
    async def test_strips_data_url_prefix(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        png_bytes = _make_png_bytes(400, 300)
        b64 = base64.b64encode(png_bytes).decode()
        data_url = f"data:image/png;base64,{b64}"

        await _call_ws_handler(ws_save_floorplan_image, hass, connection, {"id": 1, "image_base64": data_url})

        connection.send_result.assert_called_once()
        result = connection.send_result.call_args.args[1]
        assert result["success"] is True
        assert result["width"] == 400
        assert result["height"] == 300

    @pytest.mark.asyncio
    async def test_valid_png_saves_and_calls_store(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        png_bytes = _make_png_bytes(1024, 768)
        b64 = base64.b64encode(png_bytes).decode()

        await _call_ws_handler(ws_save_floorplan_image, hass, connection, {"id": 1, "image_base64": b64})

        store.async_save_floorplan_image.assert_awaited_once()
        call_args = store.async_save_floorplan_image.call_args
        assert call_args.args[1] == 1024
        assert call_args.args[2] == 768
        connection.send_error.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_store_returns_error(self, hass, monkeypatch):
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: None)
        connection = FakeConnection()

        await _call_ws_handler(ws_save_floorplan_image, hass, connection, {"id": 1, "image_base64": "AAAA"})

        connection.send_error.assert_called_once()
        assert connection.send_error.call_args.args[1] == "store_not_ready"


# ---------------------------------------------------------------------------
# ws_save_floorplan_markers
# ---------------------------------------------------------------------------

class TestWsSaveFloorplanMarkers:
    @pytest.mark.asyncio
    async def test_rooms_payload_routes_to_rooms_save(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        rooms = {"room1": {"name": "Living Room", "color": "#fff", "points": [], "sensors": []}}
        await _call_ws_handler(ws_save_floorplan_markers, hass, connection, {"id": 1, "rooms": rooms, "openings": []})

        store.async_save_floorplan_rooms.assert_awaited_once_with(rooms, [])
        store.async_save_floorplan_markers.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_invalid_rooms_type_returns_error(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        await _call_ws_handler(ws_save_floorplan_markers, hass, connection, {"id": 1, "rooms": ["not", "a", "dict"]})

        connection.send_error.assert_called_once()
        assert connection.send_error.call_args.args[1] == "invalid_format"

    @pytest.mark.asyncio
    async def test_invalid_openings_type_returns_error(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        await _call_ws_handler(
            ws_save_floorplan_markers, hass, connection, {"id": 1, "rooms": {}, "openings": "not_a_list"}
        )

        connection.send_error.assert_called_once()
        assert connection.send_error.call_args.args[1] == "invalid_format"

    @pytest.mark.asyncio
    async def test_legacy_markers_payload_routes_to_markers_save(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        await _call_ws_handler(
            ws_save_floorplan_markers, hass, connection,
            {"id": 1, "markers": {"binary_sensor.a": {"x_pct": 10, "y_pct": 10}}},
        )

        store.async_save_floorplan_markers.assert_awaited_once()
        store.async_save_floorplan_rooms.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_store_returns_error(self, hass, monkeypatch):
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: None)
        connection = FakeConnection()

        await _call_ws_handler(ws_save_floorplan_markers, hass, connection, {"id": 1, "markers": {}})

        connection.send_error.assert_called_once()
        assert connection.send_error.call_args.args[1] == "store_not_ready"


# ---------------------------------------------------------------------------
# ws_delete_floorplan
# ---------------------------------------------------------------------------

class TestWsDeleteFloorplan:
    @pytest.mark.asyncio
    async def test_deletes_existing_file_and_clears_store(self, hass, monkeypatch):
        import os
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        www_dir, floorplan_file = _floorplan_paths(hass)
        os.makedirs(www_dir, exist_ok=True)
        with open(floorplan_file, "wb") as fh:
            fh.write(b"fake png bytes")

        await _call_ws_handler(ws_delete_floorplan, hass, connection, {"id": 1})

        store.async_delete_floorplan.assert_awaited_once()
        result = connection.send_result.call_args.args[1]
        assert result["success"] is True
        assert result["file_removed"] is True
        assert not os.path.isfile(floorplan_file)

    @pytest.mark.asyncio
    async def test_missing_file_still_clears_store_and_reports_not_removed(self, hass, monkeypatch):
        store = FakeFloorplanStore()
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: store)
        connection = FakeConnection()

        await _call_ws_handler(ws_delete_floorplan, hass, connection, {"id": 1})

        store.async_delete_floorplan.assert_awaited_once()
        result = connection.send_result.call_args.args[1]
        assert result["success"] is True
        assert result["file_removed"] is False

    @pytest.mark.asyncio
    async def test_no_store_returns_error(self, hass, monkeypatch):
        monkeypatch.setattr("custom_components.secure_me.ws_floorplan._get_store", lambda h: None)
        connection = FakeConnection()

        await _call_ws_handler(ws_delete_floorplan, hass, connection, {"id": 1})

        connection.send_error.assert_called_once()
        assert connection.send_error.call_args.args[1] == "store_not_ready"
