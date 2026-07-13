"""Data storage for Secure Me panel configuration."""
# VERSION = "1.5.0"

import base64
import concurrent.futures
import logging
import time
import uuid
from typing import Any

import bcrypt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    STORAGE_VERSION_MAJOR,
    STORAGE_VERSION_MINOR,
    ATTR_FLOORPLAN_IMAGE_URL,
    ATTR_FLOORPLAN_WIDTH,
    ATTR_FLOORPLAN_HEIGHT,
    ATTR_FLOORPLAN_MARKERS,
    CONF_AUTO_ACTIONS,
    AA_LOCK_ENABLED,
    AA_LOCK_DELAY,
    AA_ALARM_ENABLED,
    AA_ALARM_DELAY,
    AA_CAMERA_ENABLED,
    AA_CAMERA_DELAY,
    AA_ARRIVAL_DELAY,
    AA_NOTIFY_ALL,
    DEFAULT_AA_LOCK_DELAY,
    DEFAULT_AA_ALARM_DELAY,
    DEFAULT_AA_CAMERA_DELAY,
    DEFAULT_AA_ARRIVAL_DELAY,
    FP_ACTIVE,
    FP_BLOCK_ALARM,
    FP_BLOCK_LOCKS,
    FP_BLOCK_CAMERAS,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}.panel_config"
SAVE_DELAY = 10  # seconds — delay-save to batch rapid changes

# Max size for base64-encoded PNG backup stored in the store.
# Mirrors FLOORPLAN_MAX_BYTES from websocket_api but expressed as bytes.
# Stored as plain base64 string -- no data-url prefix.
_FP_BACKUP_MAX_BYTES = 10 * 1024 * 1024  # 10 MB

# bcrypt work factor — 10 rounds matches Alarmo (v1.2.0: truncate to 72 bytes)
BCRYPT_ROUNDS = 10
# Max parallel threads for bcrypt code checking
MAX_WORKERS = 4


class _MigratableStore(Store):
    """HA Store subclass that can migrate data between schema versions."""

    async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        data: dict,
    ) -> dict:
        """Migrate storage data from old schema to current schema.

        v1 -> v2: Add sensor group support, per-sensor entry_delay / auto_bypass /
                  arm_on_close fields, and ensure bcrypt field present on users.
        """
        _LOGGER.info(
            "Migrating Secure Me storage from v%d.%d to v%d.%d",
            old_major_version, old_minor_version,
            STORAGE_VERSION_MAJOR, STORAGE_VERSION_MINOR,
        )

        if old_major_version == 1:
            # Add sensor_groups key if missing
            if "sensor_groups" not in data:
                data["sensor_groups"] = {}

            # Add new per-sensor fields with defaults
            for entity_id, sensor_cfg in data.get("sensors", {}).items():
                sensor_cfg.setdefault("entry_delay", None)
                sensor_cfg.setdefault("auto_bypass", False)
                sensor_cfg.setdefault("arm_on_close", False)
                sensor_cfg.setdefault("allow_open",   False)

            # Add arm_modes to existing zones (default: away)
            for zone_cfg in data.get("zones", {}).values():
                zone_cfg.setdefault("arm_modes", ["away"])

            # Users: mark existing codes as plaintext so we can re-hash on
            # next save. We do NOT re-hash here (no blocking crypto in migration).
            for user_id, user_cfg in data.get("users", {}).items():
                if user_cfg.get("code") and not user_cfg.get("code_hashed"):
                    user_cfg["code_hashed"] = False  # flag for re-hash at next save
                # v1.2.0+: backfill notification settings
                user_cfg.setdefault("notify_service", "")
                user_cfg.setdefault("receive_critical", True)
                user_cfg.setdefault("receive_alerts", True)
                user_cfg.setdefault("receive_own_actions", True)
                user_cfg.setdefault("tts_quiet_start", None)
                user_cfg.setdefault("tts_quiet_end", None)

        return data


class SecureMeStore:
    """Manage persistent storage for Secure Me panel.

    v1.2.0 additions (Alarmo-inspired):
    - Versioned MigratableStore with migration from v1 -> v2
    - bcrypt hashing for user PIN codes (10 rounds, base64-encoded)
    - Sensor groups with timeout + event_count (anti-masking)
    - Per-sensor: entry_delay override, auto_bypass, arm_on_close
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize store."""
        self.hass = hass
        self._store = _MigratableStore(
            hass,
            STORAGE_VERSION_MAJOR,
            STORAGE_KEY,
            minor_version=STORAGE_VERSION_MINOR,
        )
        self._data: dict[str, Any] = {}

    async def async_load(self) -> None:
        """Load data from storage."""
        stored = await self._store.async_load()
        if stored:
            self._data = stored
        else:
            self._data = self._default_data()

        # v1.5.0: Lazy backfill of floorplan key for stores written before
        # the feature existed. Pure additive -- no schema-version bump needed.
        if "floorplan" not in self._data:
            self._data["floorplan"] = {
                ATTR_FLOORPLAN_IMAGE_URL: None,
                ATTR_FLOORPLAN_WIDTH: 0,
                ATTR_FLOORPLAN_HEIGHT: 0,
                ATTR_FLOORPLAN_MARKERS: {},
            }
            _LOGGER.info("Backfilled empty floorplan key on existing store")

        # v1.4.3: Lazy backfill of per-sensor auto_bypass_modes.
        # The migration func only runs on schema-version bumps, but this
        # additive field was introduced mid-v2 so we backfill on every load.
        # Idempotent: skips sensors that already have the key.
        # Legacy auto_bypass=True maps to ["away"] only -- conservative
        # default chosen in v1.4.3 design (do not silently expand bypass
        # behaviour to home/night/vacation/home_alone without user consent).
        backfilled = 0
        for sensor_cfg in self._data.get("sensors", {}).values():
            if "auto_bypass_modes" not in sensor_cfg:
                if sensor_cfg.get("auto_bypass", False):
                    sensor_cfg["auto_bypass_modes"] = ["away"]
                else:
                    sensor_cfg["auto_bypass_modes"] = []
                backfilled += 1
        if backfilled:
            _LOGGER.info(
                "Backfilled auto_bypass_modes on %d sensor(s) -- saving",
                backfilled,
            )
            await self._store.async_save(self._data)

        # v1.5.0+: Lazy backfill of auto_actions key.
        if CONF_AUTO_ACTIONS not in self._data:
            self._data[CONF_AUTO_ACTIONS] = self._default_auto_actions()
            _LOGGER.info("Backfilled auto_actions defaults on existing store")
            await self._store.async_save(self._data)

        # v1.5.0+: Lazy migration of fake_presence from plain bool to v2 dict.
        fp = self._data.get("fake_presence")
        if not isinstance(fp, dict):
            # Preserve the old active state if it was True
            was_active = bool(fp) if fp is not None else False
            self._data["fake_presence"] = self._default_fake_presence_v2()
            self._data["fake_presence"][FP_ACTIVE] = was_active
            _LOGGER.info(
                "Migrated fake_presence from bool (%s) to v2 dict",
                was_active,
            )
            await self._store.async_save(self._data)

        _LOGGER.info(
            "Secure Me store loaded (%d sensors, %d zones, %d users, %d sensor_groups)",
            len(self._data.get("sensors", {})),
            len(self._data.get("zones", {})),
            len(self._data.get("users", {})),
            len(self._data.get("sensor_groups", {})),
        )

    async def async_save(self) -> None:
        """Save data to storage immediately."""
        await self._store.async_save(self._data)

    def _schedule_save(self) -> None:
        """Schedule a delayed save to batch rapid changes."""
        self._store.async_delay_save(lambda: self._data, SAVE_DELAY)

    def _default_data(self) -> dict[str, Any]:
        """Return default data structure (v2 schema)."""
        return {
            "sensors": {},
            "sensor_groups": {},
            "zones": {},
            "users": {},
            "modules": {
                "camera":  {"enabled": False, "entities": [], "config": {}},
                "lock":    {"enabled": False, "entities": [], "config": {}},
                "lights":  {"enabled": False, "entities": [], "config": {}},
                "climate": {"enabled": False, "entities": [], "config": {}},
                "siren":   {"enabled": False, "entities": [], "config": {}},
                "tts":     {"enabled": False, "entities": [], "config": {"tts_service": "tts.cloud_say", "language": "da", "volume": 0.5, "custom_messages": []}},
            },
            "notifications": {},
            "automations": {},
            "scheduled_tests": {},
            "speaker_profiles": [],
            "fake_presence": self._default_fake_presence_v2(),
            "home_alone_cameras": [],
            CONF_AUTO_ACTIONS: self._default_auto_actions(),
            # v1.5.0 floorplan (Home Alone live-view).
            # Empty by default -- frontend treats image_url=None as "no floorplan configured".
            "floorplan": {
                ATTR_FLOORPLAN_IMAGE_URL: None,
                ATTR_FLOORPLAN_WIDTH: 0,
                ATTR_FLOORPLAN_HEIGHT: 0,
                ATTR_FLOORPLAN_MARKERS: {},
            },
        }

    # ─── bcrypt helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _default_auto_actions() -> dict:
        """Return default Auto Actions v2 configuration."""
        return {
            AA_LOCK_ENABLED:   True,
            AA_LOCK_DELAY:     DEFAULT_AA_LOCK_DELAY,
            AA_ALARM_ENABLED:  True,
            AA_ALARM_DELAY:    DEFAULT_AA_ALARM_DELAY,
            AA_CAMERA_ENABLED: True,
            AA_CAMERA_DELAY:   DEFAULT_AA_CAMERA_DELAY,
            AA_ARRIVAL_DELAY:  DEFAULT_AA_ARRIVAL_DELAY,
            AA_NOTIFY_ALL:     False,
        }

    @staticmethod
    def _default_fake_presence_v2() -> dict:
        """Return default Fake Presence v2 configuration."""
        return {
            FP_ACTIVE:        False,
            FP_BLOCK_ALARM:   True,
            FP_BLOCK_LOCKS:   False,
            FP_BLOCK_CAMERAS: False,
        }

    @staticmethod
    def _hash_code(code: str) -> str:
        """Hash a PIN/code with bcrypt. Returns base64-encoded hash string.

        bcrypt rejects passwords longer than 72 bytes — truncate to the
        bcrypt maximum before hashing. This is consistent with how virtually
        all bcrypt implementations handle long passwords.
        """
        code_bytes = code.encode("utf-8")[:72]
        hashed = bcrypt.hashpw(code_bytes, bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
        return base64.b64encode(hashed).decode("utf-8")

    @staticmethod
    def _check_code(code: str, stored_hash: str) -> bool:
        """Verify a code against a stored bcrypt hash."""
        try:
            code_bytes = code.encode("utf-8")[:72]
            raw_hash = base64.b64decode(stored_hash.encode("utf-8"))
            return bcrypt.checkpw(code_bytes, raw_hash)
        except Exception:
            return False

    # ─── Sensors ─────────────────────────────────────────────────────────────

    # Environmental device classes — always monitored, cannot be disabled
    _ENV_CLASSES = frozenset({"smoke", "gas", "moisture"})

    def get_sensors(self) -> dict[str, Any]:
        """Get all configured sensors."""
        return self._data.get("sensors", {})

    def get_available_sensors(self) -> list[dict[str, Any]]:
        """Get all available binary_sensors from HA that could be alarm sensors."""
        sensors = []
        for state in self.hass.states.async_all("binary_sensor"):
            device_class = state.attributes.get("device_class", "")
            if device_class not in (
                "door", "window", "garage_door", "opening",
                "motion", "occupancy", "presence",
                "vibration", "smoke", "gas", "moisture",
            ):
                continue
            configured = self._data.get("sensors", {}).get(state.entity_id, {})
            if configured.get("excluded", False):
                continue
            is_env = (
                device_class in self._ENV_CLASSES
                and not configured.get("env_unmarked", False)
            ) or configured.get("is_environmental", False)
            sensors.append({
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "device_class": device_class,
                "state": state.state,
                "is_environmental": is_env,
                "enabled": True if is_env else configured.get("enabled", False),
                "sensor_type": "environmental" if is_env else configured.get(
                    "sensor_type", self._infer_type(device_class)
                ),
                "env_unmarked": configured.get("env_unmarked", False),
                # v1.2.0 per-sensor fields
                "entry_delay": configured.get("entry_delay", None),
                "auto_bypass": configured.get("auto_bypass", False),
                "auto_bypass_modes": configured.get("auto_bypass_modes", []),
                "arm_on_close": configured.get("arm_on_close", False),
                "allow_open":   configured.get("allow_open",   False),
            })

        # person entities
        for state in self.hass.states.async_all("person"):
            configured = self._data.get("sensors", {}).get(state.entity_id, {})
            if configured.get("excluded", False):
                continue
            sensors.append({
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "device_class": "presence",
                "state": state.state,
                "enabled": configured.get("enabled", False),
                "sensor_type": "presence",
                "excluded": False,
                "entry_delay": None,
                "auto_bypass": False,
                "auto_bypass_modes": [],
                "arm_on_close": False,
            })

        _IRRELEVANT_PATTERNS = (
            "unifi_", "dlna_", "_tv_", "_samsung_", "_lg_", "_roku_",
            "skraldespands", "printer", "_sonos_",
        )
        for state in self.hass.states.async_all("device_tracker"):
            configured = self._data.get("sensors", {}).get(state.entity_id, {})
            if configured.get("excluded", False):
                continue
            eid_lower = state.entity_id.lower()
            auto_hidden = any(p in eid_lower for p in _IRRELEVANT_PATTERNS)
            sensors.append({
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "device_class": "presence",
                "state": state.state,
                "enabled": configured.get("enabled", False),
                "sensor_type": "presence",
                "auto_hidden": auto_hidden and not configured.get("enabled", False),
                "entry_delay": None,
                "auto_bypass": False,
                "auto_bypass_modes": [],
                "arm_on_close": False,
            })
        return sensors

    def _infer_type(self, device_class: str) -> str:
        """Infer sensor type from device class."""
        if device_class in ("door", "window", "garage_door", "opening"):
            return "contact"
        if device_class in ("motion", "occupancy", "vibration"):
            return "motion"
        if device_class in ("presence",):
            return "presence"
        if device_class in ("smoke", "gas", "moisture"):
            return "environmental"
        return "contact"

    async def async_save_sensors_bulk(self, sensors: dict[str, Any]) -> None:
        """Save multiple sensor configurations at once."""
        self._data["sensors"] = sensors
        self._schedule_save()

    # ─── Sensor Groups (anti-masking) ────────────────────────────────────────

    def get_sensor_groups(self) -> dict[str, Any]:
        """Get all sensor groups."""
        return self._data.get("sensor_groups", {})

    async def async_save_sensor_group(
        self, group_id: str | None, config: dict[str, Any]
    ) -> str:
        """Create or update a sensor group. Returns the group_id."""
        if not group_id:
            group_id = str(int(time.time()))
        self._data.setdefault("sensor_groups", {})[group_id] = {
            "group_id": group_id,
            "name": config.get("name", ""),
            "entities": config.get("entities", []),
            "timeout": int(config.get("timeout", 0)),
            "event_count": int(config.get("event_count", 2)),
        }
        self._schedule_save()
        return group_id

    async def async_delete_sensor_group(self, group_id: str) -> bool:
        """Delete a sensor group."""
        if group_id in self._data.get("sensor_groups", {}):
            del self._data["sensor_groups"][group_id]
            self._schedule_save()
            return True
        return False

    # ─── Zones ───────────────────────────────────────────────────────────────

    def get_zones(self) -> dict[str, Any]:
        """Get all zones."""
        return self._data.get("zones", {})

    async def async_save_zone(self, zone_id: str, config: dict[str, Any]) -> None:
        """Save zone configuration."""
        self._data.setdefault("zones", {})[zone_id] = config
        self._schedule_save()

    async def async_delete_zone(self, zone_id: str) -> bool:
        """Delete a zone."""
        if zone_id in self._data.get("zones", {}):
            del self._data["zones"][zone_id]
            self._schedule_save()
            return True
        return False

    # ─── Users (bcrypt) ──────────────────────────────────────────────────────

    def get_users(self) -> dict[str, Any]:
        """Get all users. Codes are stored as bcrypt hashes — never returned raw."""
        return self._data.get("users", {})

    def authenticate_user(self, code: str, user_id: str | None = None) -> dict | None:
        """Authenticate a user by code.

        Uses bcrypt.checkpw in a ThreadPoolExecutor (non-blocking).
        If user_id is given, only that user is checked.
        Returns the matching user dict on success, None on failure.
        Falls back to plaintext comparison for legacy (non-hashed) entries.
        """
        users = self._data.get("users", {})

        def _check(user: dict) -> dict | None:
            if not user.get("enabled", True):
                return None
            stored = user.get("code", "")
            if not stored:
                return user if not code else None
            if user.get("code_hashed", False):
                return user if self._check_code(code, stored) else None
            # Legacy plaintext fallback
            return user if stored == code else None

        if user_id:
            user = users.get(user_id)
            return _check(user) if user else None

        # Parallel check across all users (matches Alarmo approach)
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(_check, u): u
                for u in users.values()
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result is not None:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return result
        return None

    async def async_save_user(self, user_id: str, config: dict[str, Any]) -> None:
        """Save user configuration. Hashes code with bcrypt if plaintext provided."""
        if not user_id:
            user_id = str(int(time.time()))

        cfg = dict(config)
        raw_code = cfg.get("code", "")

        # Hash if a new plaintext code is provided (not already a hash)
        if raw_code and not cfg.get("code_hashed", False):
            cfg["code"] = self._hash_code(raw_code)
            cfg["code_hashed"] = True

        self._data.setdefault("users", {})[user_id] = cfg
        await self.async_save()

    async def async_delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id in self._data.get("users", {}):
            del self._data["users"][user_id]
            self._schedule_save()
            return True
        return False

    def get_nfc_tags(self) -> list[dict[str, str]]:
        """Get available NFC tags from HA."""
        tags = []
        tag_registry = self.hass.data.get("tag")
        if tag_registry and hasattr(tag_registry, "async_list_tags"):
            for tag in tag_registry.async_list_tags():
                tags.append({"id": tag.id, "name": tag.name or tag.id})
        return tags

    # ─── Modules ─────────────────────────────────────────────────────────────

    def get_modules(self) -> dict[str, Any]:
        """Get all module configurations."""
        return self._data.get("modules", self._default_data()["modules"])

    async def async_save_module(self, module_id: str, config: dict[str, Any]) -> None:
        """Save module configuration."""
        self._data.setdefault("modules", self._default_data()["modules"])[module_id] = config
        self._schedule_save()

    def get_available_entities(self, domain: str) -> list[dict[str, Any]]:
        """Get available entities for a domain."""
        return [
            {
                "entity_id": s.entity_id,
                "name": s.attributes.get("friendly_name", s.entity_id),
                "state": s.state,
            }
            for s in self.hass.states.async_all(domain)
        ]

    # -- Speaker Profiles (v1.4.0) ------------------------------------------

    def get_speaker_profiles(self) -> list[dict[str, Any]]:
        """Get all speaker profiles."""
        return self._data.get("speaker_profiles", [])

    async def async_save_speaker_profiles(self, profiles: list[dict[str, Any]]) -> None:
        """Save the full speaker profile list."""
        self._data["speaker_profiles"] = profiles
        self._schedule_save()

    # -- Notifications -------------------------------------------------------

    def get_notifications(self) -> dict[str, Any]:
        """Get all notification configurations."""
        return self._data.get("notifications", {})

    async def async_save_notification(self, notif_id: str, config: dict[str, Any]) -> None:
        """Save notification configuration."""
        self._data.setdefault("notifications", {})[notif_id] = config
        self._schedule_save()

    async def async_delete_notification(self, notif_id: str) -> bool:
        """Delete a notification."""
        if notif_id in self._data.get("notifications", {}):
            del self._data["notifications"][notif_id]
            self._schedule_save()
            return True
        return False

    # ─── Automations ─────────────────────────────────────────────────────────

    def get_automations(self) -> dict[str, Any]:
        """Get all automation configurations."""
        return self._data.get("automations", {})

    async def async_save_automation(self, auto_id: str, config: dict[str, Any]) -> None:
        """Save automation configuration."""
        self._data.setdefault("automations", {})[auto_id] = config
        self._schedule_save()

    async def async_delete_automation(self, auto_id: str) -> bool:
        """Delete an automation."""
        if auto_id in self._data.get("automations", {}):
            del self._data["automations"][auto_id]
            self._schedule_save()
            return True
        return False

    # ─── Scheduled Tests ──────────────────────────────────────────────────────

    def get_scheduled_tests(self) -> dict[str, Any]:
        """Get all scheduled test configurations."""
        return self._data.get("scheduled_tests", {})

    async def async_save_scheduled_test(self, test_id: str | None, config: dict[str, Any]) -> str:
        """Save a scheduled test. Creates new ID if test_id is None."""
        if not test_id:
            test_id = "sched_" + str(uuid.uuid4())[:8]
        self._data.setdefault("scheduled_tests", {})[test_id] = config
        self._schedule_save()
        return test_id

    async def async_delete_scheduled_test(self, test_id: str) -> bool:
        """Delete a scheduled test."""
        if test_id in self._data.get("scheduled_tests", {}):
            del self._data["scheduled_tests"][test_id]
            self._schedule_save()
            return True
        return False

    async def async_update_scheduled_test_result(
        self, test_id: str, last_run: str, last_result: str
    ) -> None:
        """Update last_run and last_result after a scheduled test executes."""
        sched = self._data.get("scheduled_tests", {}).get(test_id)
        if sched:
            sched["last_run"] = last_run
            sched["last_result"] = last_result
            self._schedule_save()

    # ─── Fake Presence ────────────────────────────────────────────────────────
    # NOTE: get_fake_presence() / async_set_fake_presence() for Fake Presence v2
    # (dict-based, with block_alarm/block_locks/block_cameras) are defined further
    # down under "Fake Presence v2". The old v1 bool-only versions that used to
    # live here were removed — they were dead code (shadowed by the v2 versions)
    # and, if ever called again by mistake, would have overwritten the v2 dict
    # with a bare bool and wiped the block_* settings.

    def get_home_alone_cameras(self) -> list[str]:
        """Get configured Home Alone Monitor camera entity IDs."""
        return self._data.get("home_alone_cameras", [])

    async def async_save_home_alone_cameras(self, cameras: list[str]) -> None:
        """Save Home Alone Monitor camera entity IDs."""
        self._data["home_alone_cameras"] = cameras
        self._schedule_save()

    # ─── Floorplan (v1.5.0) ───────────────────────────────────────────
    # The image itself is stored on disk under custom_components/secure_me/
    # floorplan/floorplan.png and exposed via panel.py's static-resource
    # handler. The store only holds image metadata + per-sensor markers.

    def _empty_floorplan(self) -> dict[str, Any]:
        """Return an empty floorplan structure."""
        return {
            ATTR_FLOORPLAN_IMAGE_URL: None,
            ATTR_FLOORPLAN_WIDTH: 0,
            ATTR_FLOORPLAN_HEIGHT: 0,
            ATTR_FLOORPLAN_MARKERS: {},
            "rooms": {},
            "openings": [],
            "image_b64": None,  # PNG backup -- survives HACS updates
        }

    def get_floorplan(self) -> dict[str, Any]:
        """Get full floorplan config (image url + dimensions + rooms + legacy markers)."""
        fp = self._data.get("floorplan")
        if not fp:
            return self._empty_floorplan()
        return {
            ATTR_FLOORPLAN_IMAGE_URL: fp.get(ATTR_FLOORPLAN_IMAGE_URL),
            ATTR_FLOORPLAN_WIDTH: fp.get(ATTR_FLOORPLAN_WIDTH, 0),
            ATTR_FLOORPLAN_HEIGHT: fp.get(ATTR_FLOORPLAN_HEIGHT, 0),
            ATTR_FLOORPLAN_MARKERS: fp.get(ATTR_FLOORPLAN_MARKERS, {}),
            "rooms": fp.get("rooms", {}),
            "openings": fp.get("openings", []),
        }

    async def async_save_floorplan_image(
        self, image_url: str, width: int, height: int, image_b64: str | None = None
    ) -> None:
        """Save floorplan image metadata (url + dimensions + optional base64 backup).

        Rooms and markers are preserved -- only the image fields are overwritten.
        image_b64: plain base64-encoded PNG (no data-url prefix). When provided
        it is stored alongside the metadata so it can be restored after a HACS
        update that deletes the PNG file on disk.
        """
        fp = self._data.setdefault("floorplan", self._empty_floorplan())
        fp[ATTR_FLOORPLAN_IMAGE_URL] = image_url
        fp[ATTR_FLOORPLAN_WIDTH] = int(width)
        fp[ATTR_FLOORPLAN_HEIGHT] = int(height)
        fp.setdefault(ATTR_FLOORPLAN_MARKERS, {})
        fp.setdefault("rooms", {})
        if image_b64 is not None:
            encoded_len = len(image_b64.encode("utf-8"))
            if encoded_len <= _FP_BACKUP_MAX_BYTES:
                fp["image_b64"] = image_b64
            else:
                _LOGGER.warning(
                    "Floorplan base64 backup too large (%d bytes) -- skipping backup",
                    encoded_len,
                )
                fp.setdefault("image_b64", None)
        await self.async_save()

    async def async_save_floorplan_rooms(
        self,
        rooms: dict[str, dict[str, Any]],
        openings: list[dict[str, Any]] | None = None,
    ) -> None:
        """Replace the full rooms dict and openings list.

        v1.6.0: rooms replace the old flat markers structure.
        v1.6.1: openings (doors/windows) added as separate list.
        Image metadata is preserved.
        """
        fp = self._data.setdefault("floorplan", self._empty_floorplan())
        fp["rooms"] = rooms or {}
        if openings is not None:
            fp["openings"] = openings
        else:
            fp.setdefault("openings", [])
        self._schedule_save()

    async def async_save_floorplan_markers(
        self, markers: dict[str, dict[str, Any]]
    ) -> None:
        """Replace the full markers dict (legacy v1.5.0 format).

        Image metadata and rooms are preserved.
        """
        fp = self._data.setdefault("floorplan", self._empty_floorplan())
        fp[ATTR_FLOORPLAN_MARKERS] = markers or {}
        self._schedule_save()

    async def async_clear_floorplan_image(self) -> None:
        """Clear only the image metadata (url + dimensions).

        Rooms, openings, and markers are preserved. Use this when the PNG
        file is missing on disk (e.g. after a HACS update) so room/sensor
        configuration is not lost unnecessarily.
        """
        fp = self._data.setdefault("floorplan", self._empty_floorplan())
        fp[ATTR_FLOORPLAN_IMAGE_URL] = None
        fp[ATTR_FLOORPLAN_WIDTH] = 0
        fp[ATTR_FLOORPLAN_HEIGHT] = 0
        await self.async_save()

    def get_test_history(self) -> list[dict]:
        """Return test result history (newest first, max 10)."""
        return self._data.get("test_history", [])

    async def async_append_test_result(self, result: dict) -> None:
        """Prepend a test result and keep only the last 10 entries."""
        history = self._data.get("test_history", [])
        history.insert(0, result)
        self._data["test_history"] = history[:10]
        self._schedule_save()

    async def async_get_floorplan_image_b64(self) -> str | None:
        """Return the stored base64 PNG backup from the dedicated image store."""
        data = await self._image_store.async_load()
        if data and data.get("image_b64"):
            return data["image_b64"]
        return self._data.get("floorplan", {}).get("image_b64")

    async def async_restore_floorplan_image_from_backup(
        self, image_url: str
    ) -> tuple[bytes, int, int] | None:
        """Attempt to restore the PNG file from the base64 backup in the store.

        Returns (image_bytes, width, height) on success, None if no backup exists.
        Caller is responsible for writing image_bytes to disk.
        """
        import base64 as _base64
        import struct as _struct

        b64 = await self.async_get_floorplan_image_b64()
        if not b64:
            return None
        try:
            image_bytes = _base64.b64decode(b64)
        except Exception as err:
            _LOGGER.warning("Floorplan backup decode failed: %s", err)
            return None

        # Re-read dimensions from the PNG IHDR chunk
        if len(image_bytes) < 24:
            return None
        if image_bytes[12:16] != b"IHDR":
            return None
        try:
            width, height = _struct.unpack(">II", image_bytes[16:24])
        except _struct.error:
            return None
        if width == 0 or height == 0:
            return None

        # Update store metadata to reflect the restored image
        fp = self._data.setdefault("floorplan", self._empty_floorplan())
        fp[ATTR_FLOORPLAN_IMAGE_URL] = image_url
        fp[ATTR_FLOORPLAN_WIDTH] = width
        fp[ATTR_FLOORPLAN_HEIGHT] = height
        await self.async_save()
        _LOGGER.info(
            "Floorplan restored from base64 backup (%dx%d, %d bytes)",
            width, height, len(image_bytes),
        )
        return image_bytes, width, height

    async def async_delete_floorplan(self) -> None:
        """Reset floorplan to empty (image + rooms + markers + openings all cleared).

        This is a full destructive reset. For cases where only the image is
        missing (e.g. after HACS update), use async_clear_floorplan_image()
        to preserve room/sensor configuration.
        Caller is responsible for unlinking the image file on disk.
        """
        self._data["floorplan"] = self._empty_floorplan()
        await self.async_save()

    # Auto Actions v2

    def get_auto_actions(self) -> dict:
        """Get current Auto Actions configuration with defaults for missing keys."""
        stored = self._data.get(CONF_AUTO_ACTIONS, {})
        defaults = self._default_auto_actions()
        return {**defaults, **stored}

    async def async_save_auto_actions(self, config: dict) -> None:
        """Save Auto Actions configuration."""
        current = self._data.get(CONF_AUTO_ACTIONS, {})
        current.update(config)
        self._data[CONF_AUTO_ACTIONS] = current
        self._schedule_save()

    # Fake Presence v2

    def get_fake_presence_v2(self) -> dict:
        """Get Fake Presence v2 config dict. Always returns a full dict."""
        fp = self._data.get("fake_presence", {})
        if not isinstance(fp, dict):
            return self._default_fake_presence_v2()
        defaults = self._default_fake_presence_v2()
        return {**defaults, **fp}

    def get_fake_presence(self) -> bool:
        """Get whether Fake Presence is currently active (v1 compat)."""
        fp = self._data.get("fake_presence", False)
        if isinstance(fp, dict):
            return fp.get(FP_ACTIVE, False)
        return bool(fp)

    async def async_set_fake_presence(self, active: bool) -> None:
        """Set Fake Presence active state, preserving other v2 fields."""
        fp = self._data.get("fake_presence", {})
        if not isinstance(fp, dict):
            fp = self._default_fake_presence_v2()
        fp[FP_ACTIVE] = active
        self._data["fake_presence"] = fp
        self._schedule_save()

    async def async_save_fake_presence_v2(self, config: dict) -> None:
        """Save full Fake Presence v2 config dict."""
        fp = self._data.get("fake_presence", {})
        if not isinstance(fp, dict):
            fp = self._default_fake_presence_v2()
        fp.update(config)
        self._data["fake_presence"] = fp
        self._schedule_save()