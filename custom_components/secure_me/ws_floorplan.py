"""WebSocket API — Floorplan commands for Secure Me."""
# VERSION = "1.5.4"
from __future__ import annotations

import base64
import binascii
import logging
import os
import struct
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    FLOORPLAN_DIR_NAME,
    FLOORPLAN_WWW_DIR_NAME,
    FLOORPLAN_IMAGE_NAME,
    FLOORPLAN_MAX_BYTES,
    FLOORPLAN_URL_PATH,
    ATTR_FLOORPLAN_IMAGE_URL,
    ATTR_FLOORPLAN_WIDTH,
    ATTR_FLOORPLAN_HEIGHT,
    ATTR_FLOORPLAN_MARKERS,
    ATTR_MARKER_X_PCT,
    ATTR_MARKER_Y_PCT,
    ATTR_MARKER_LABEL,
    ATTR_MARKER_KIND,
)

_LOGGER = logging.getLogger(__name__)


from .ws_helpers import _get_store  # noqa: F401


# v1.5.3: the floorplan image lives on disk under config/www/secure_me_floorplan/
# and is served natively by HA under /local/ -- a path HACS never touches on
# update, since www/ is user config data rather than integration code. Before
# v1.5.3 the file lived under custom_components/secure_me/floorplan/, which a
# HACS update always wipes and replaces along with the rest of the integration.
# The store still only holds image metadata + per-sensor markers; the bytes
# never go through the store except as the image_b64 backup safety net.

# PNG signature for header validation (8 bytes per the PNG spec).
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _floorplan_paths(hass: HomeAssistant) -> tuple[str, str]:
    """Return (directory, file_path) for the floorplan image on disk (www/)."""
    www_dir = hass.config.path("www", FLOORPLAN_WWW_DIR_NAME)
    floorplan_file = os.path.join(www_dir, FLOORPLAN_IMAGE_NAME)
    return www_dir, floorplan_file


def _legacy_floorplan_file(hass: HomeAssistant) -> str:
    """Return the pre-v1.5.3 file path under custom_components/secure_me/.

    Kept only so a one-time migration can pick up a file left over from
    before the move to www/. Never written to going forward.
    """
    root_dir = hass.config.path("custom_components", DOMAIN)
    return os.path.join(root_dir, FLOORPLAN_DIR_NAME, FLOORPLAN_IMAGE_NAME)


def _migrate_legacy_floorplan_file(hass: HomeAssistant) -> bool:
    """One-time migration: move a pre-v1.5.3 file into www/ if present.

    Runs synchronously on the executor. Returns True if a file was moved.
    No-op if the legacy file doesn't exist or the new location is already
    populated (never overwrites a newer upload with an older legacy file).
    """
    legacy_file = _legacy_floorplan_file(hass)
    if not os.path.isfile(legacy_file):
        return False

    www_dir, floorplan_file = _floorplan_paths(hass)
    if os.path.isfile(floorplan_file):
        return False

    os.makedirs(www_dir, exist_ok=True)
    try:
        os.replace(legacy_file, floorplan_file)
    except OSError as err:
        _LOGGER.warning(
            "Secure Me: failed to migrate legacy floorplan file %s -> %s (%s)",
            legacy_file, floorplan_file, err,
        )
        return False
    _LOGGER.info(
        "Secure Me: migrated legacy floorplan image %s -> %s",
        legacy_file, floorplan_file,
    )
    return True


def _read_png_dimensions(data: bytes) -> tuple[int, int] | None:
    """Return (width, height) from a PNG byte string, or None if invalid.

    Reads the IHDR chunk -- the first chunk after the 8-byte signature --
    which always starts at offset 8 with a 4-byte length, the 4-byte type
    'IHDR', then 4 bytes width and 4 bytes height (big-endian unsigned).
    """
    if len(data) < 24:
        return None
    if data[:8] != _PNG_SIGNATURE:
        return None
    if data[12:16] != b"IHDR":
        return None
    try:
        width, height = struct.unpack(">II", data[16:24])
    except struct.error:
        return None
    if width == 0 or height == 0:
        return None
    return width, height


def _normalise_markers(
    raw_markers: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Validate and clean a markers dict from the frontend.

    Each marker is keyed by entity_id and must have x_pct / y_pct in [0, 100].
    Unknown fields are dropped. Returns a fresh dict; never raises.
    """
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_markers, dict):
        return out

    for entity_id, cfg in raw_markers.items():
        if not isinstance(entity_id, str) or not entity_id:
            continue
        if not isinstance(cfg, dict):
            continue
        try:
            x = float(cfg.get(ATTR_MARKER_X_PCT, -1))
            y = float(cfg.get(ATTR_MARKER_Y_PCT, -1))
        except (TypeError, ValueError):
            continue
        if not (0.0 <= x <= 100.0) or not (0.0 <= y <= 100.0):
            continue

        kind = cfg.get(ATTR_MARKER_KIND) or "motion"
        if kind not in ("motion", "door", "window"):
            kind = "motion"

        label = cfg.get(ATTR_MARKER_LABEL)
        if label is not None and not isinstance(label, str):
            label = None

        out[entity_id] = {
            ATTR_MARKER_X_PCT: round(x, 2),
            ATTR_MARKER_Y_PCT: round(y, 2),
            ATTR_MARKER_LABEL: label,
            ATTR_MARKER_KIND: kind,
        }
    return out


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/get_floorplan",
})
@websocket_api.async_response
async def ws_get_floorplan(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the current floorplan config (image url + dimensions + markers).

    image_url is None when no floorplan has been uploaded yet.
    """
    store = _get_store(hass)
    if not store:
        connection.send_result(msg["id"], {
            ATTR_FLOORPLAN_IMAGE_URL: None,
            ATTR_FLOORPLAN_WIDTH: 0,
            ATTR_FLOORPLAN_HEIGHT: 0,
            ATTR_FLOORPLAN_MARKERS: {},
        })
        return

    fp = store.get_floorplan()

    # One-time migration: pick up a file left over from before v1.5.3 moved
    # the floorplan image from custom_components/secure_me/floorplan/ to
    # config/www/secure_me_floorplan/. No-op once migrated (or if there was
    # never a legacy file to begin with).
    await hass.async_add_executor_job(_migrate_legacy_floorplan_file, hass)

    # Self-heal: if the store thinks an image exists but the file is gone
    # (e.g. after a HACS update or manual deletion), report image_url=None
    # so the frontend falls back to the upload state.
    # IMPORTANT: only clear the image metadata -- rooms, openings, and sensor
    # assignments must survive a HACS update. Use async_clear_floorplan_image()
    # rather than async_delete_floorplan() to preserve room configuration.
    if fp.get(ATTR_FLOORPLAN_IMAGE_URL):
        _, floorplan_file = _floorplan_paths(hass)
        if not await hass.async_add_executor_job(os.path.isfile, floorplan_file):
            _LOGGER.info(
                "Floorplan image missing on disk (%s) -- attempting restore from backup",
                floorplan_file,
            )
            # Try to restore from base64 backup stored in the store.
            # This recovers the PNG automatically after a HACS update.
            # Defensive try/except: a failure here must never crash the whole
            # get_floorplan response, since rooms/openings/sensor bindings are
            # otherwise intact and must still reach the frontend. This is
            # exactly what happened in v1.5.1 (AttributeError on a stray
            # self._image_store reference) -- fixed now, but this guard stays
            # so a future regression here degrades gracefully instead of
            # making the whole floorplan config look "gone".
            try:
                restored = await store.async_restore_floorplan_image_from_backup(
                    FLOORPLAN_URL_PATH
                )
            except Exception as err:
                _LOGGER.warning(
                    "Floorplan backup restore raised an unexpected error (%s) -- "
                    "clearing image metadata only (rooms and openings preserved)",
                    err,
                )
                restored = None
            if restored:
                image_bytes, _w, _h = restored
                floorplan_dir, _ = _floorplan_paths(hass)

                def _write_restore() -> None:
                    os.makedirs(floorplan_dir, exist_ok=True)
                    tmp = floorplan_file + ".tmp"
                    with open(tmp, "wb") as fh:
                        fh.write(image_bytes)
                    os.replace(tmp, floorplan_file)

                try:
                    await hass.async_add_executor_job(_write_restore)
                    _LOGGER.info(
                        "Floorplan auto-restored from backup -- %d bytes written to %s",
                        len(image_bytes), floorplan_file,
                    )
                except OSError as err:
                    _LOGGER.warning(
                        "Floorplan restore write failed (%s) -- clearing image metadata only",
                        err,
                    )
                    await store.async_clear_floorplan_image()
            else:
                _LOGGER.info(
                    "No floorplan backup available -- clearing image metadata only"
                    " (rooms and openings preserved)",
                )
                await store.async_clear_floorplan_image()
            fp = store.get_floorplan()

    connection.send_result(msg["id"], fp)


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_floorplan_image",
    vol.Required("image_base64"): str,
})
@websocket_api.async_response
async def ws_save_floorplan_image(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Decode a base64-encoded PNG and write it to disk.

    Validates: max size (FLOORPLAN_MAX_BYTES), PNG signature + IHDR header.
    On success, persists the image URL + decoded width/height to the store.
    Existing markers are preserved (use save_floorplan_markers to clear them).
    """
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialised")
        return

    raw_b64 = msg["image_base64"]
    # Strip data-url prefix if the frontend sent the whole thing.
    if "," in raw_b64 and raw_b64.lstrip().startswith("data:"):
        raw_b64 = raw_b64.split(",", 1)[1]

    try:
        image_bytes = base64.b64decode(raw_b64, validate=True)
    except (binascii.Error, ValueError) as err:
        connection.send_error(msg["id"], "invalid_base64", f"Could not decode image: {err}")
        return

    if len(image_bytes) > FLOORPLAN_MAX_BYTES:
        connection.send_error(
            msg["id"],
            "image_too_large",
            f"Floorplan image is {len(image_bytes)} bytes (max {FLOORPLAN_MAX_BYTES})",
        )
        return

    dimensions = _read_png_dimensions(image_bytes)
    if dimensions is None:
        connection.send_error(
            msg["id"],
            "invalid_png",
            "Uploaded data is not a valid PNG image",
        )
        return
    width, height = dimensions

    floorplan_dir, floorplan_file = _floorplan_paths(hass)

    def _write() -> None:
        os.makedirs(floorplan_dir, exist_ok=True)
        # Atomic-ish write: tmp file then rename so a half-written file
        # never gets served by the static handler.
        tmp_path = floorplan_file + ".tmp"
        with open(tmp_path, "wb") as fh:
            fh.write(image_bytes)
        os.replace(tmp_path, floorplan_file)

    try:
        await hass.async_add_executor_job(_write)
    except OSError as err:
        _LOGGER.error("Failed to write floorplan image to %s: %s", floorplan_file, err)
        connection.send_error(msg["id"], "write_failed", f"Could not write image: {err}")
        return

    await store.async_save_floorplan_image(FLOORPLAN_URL_PATH, width, height, image_b64=raw_b64)
    _LOGGER.info(
        "Floorplan image saved (%dx%d, %d bytes) -> %s",
        width, height, len(image_bytes), floorplan_file,
    )

    connection.send_result(msg["id"], {
        "success": True,
        ATTR_FLOORPLAN_IMAGE_URL: FLOORPLAN_URL_PATH,
        ATTR_FLOORPLAN_WIDTH: width,
        ATTR_FLOORPLAN_HEIGHT: height,
    })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/save_floorplan_markers",
    vol.Optional("markers"): dict,
    vol.Optional("rooms"): dict,
    vol.Optional("openings"): list,
})
@websocket_api.async_response
async def ws_save_floorplan_markers(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Replace the full floorplan data (rooms, openings, or legacy markers).

    v1.6.0: frontend sends { rooms: { room_id: { name, color, points, sensors } } }.
    v1.6.1: frontend also sends { openings: [ { type, label, points } ] }.
    v1.5.0 legacy: frontend sent { markers: { entity_id: { x_pct, y_pct, ... } } }.
    """
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialised")
        return

    if "rooms" in msg:
        # v1.6.0+ room-based format
        rooms = msg["rooms"]
        if not isinstance(rooms, dict):
            connection.send_error(msg["id"], "invalid_format", "rooms must be a dict")
            return
        openings = msg.get("openings")
        if openings is not None and not isinstance(openings, list):
            connection.send_error(msg["id"], "invalid_format", "openings must be a list")
            return
        await store.async_save_floorplan_rooms(rooms, openings)
        _LOGGER.debug(
            "Floorplan saved: %d rooms, %d openings",
            len(rooms),
            len(openings) if openings else 0,
        )
        connection.send_result(msg["id"], {"success": True, "rooms": rooms})
    else:
        # v1.5.0 legacy markers format
        cleaned = _normalise_markers(msg.get("markers"))
        await store.async_save_floorplan_markers(cleaned)
        _LOGGER.debug("Floorplan markers saved: %d markers", len(cleaned))
        connection.send_result(msg["id"], {
            "success": True,
            ATTR_FLOORPLAN_MARKERS: cleaned,
        })


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/delete_floorplan",
})
@websocket_api.async_response
async def ws_delete_floorplan(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete the floorplan image from disk and clear the store."""
    store = _get_store(hass)
    if not store:
        connection.send_error(msg["id"], "store_not_ready", "Store not initialised")
        return

    _, floorplan_file = _floorplan_paths(hass)

    def _unlink() -> bool:
        try:
            os.unlink(floorplan_file)
            return True
        except FileNotFoundError:
            return False
        except OSError as err:
            _LOGGER.warning("Could not delete floorplan file %s: %s", floorplan_file, err)
            return False

    removed = await hass.async_add_executor_job(_unlink)
    await store.async_delete_floorplan()
    _LOGGER.info("Floorplan deleted (file_removed=%s)", removed)
    connection.send_result(msg["id"], {"success": True, "file_removed": removed})


