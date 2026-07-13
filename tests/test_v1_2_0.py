"""Tests for Secure Me v1.2.0 new features.

Covers:
- bcrypt user code hashing (store.py)
- MigratableStore v1->v2 migration (store.py)
- Sensor groups / anti-masking (store.py + zones.py)
- Per-sensor entry_delay, auto_bypass, arm_on_close (store.py + zones.py)
- Push notification action constants (const.py)
- Coordinator: force-arm bypass open sensors (coordinator.py)
"""
# VERSION = "1.3.0"

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.secure_me.store import SecureMeStore, BCRYPT_ROUNDS
from custom_components.secure_me.zones import ZoneManager, Zone, SensorGroup
from custom_components.secure_me.const import (
    PUSH_EVENT,
    PUSH_EVENT_ACTIONS,
    EVENT_ACTION_DISARM,
    EVENT_ACTION_ARM_AWAY,
    EVENT_ACTION_FORCE_ARM,
    EVENT_ACTION_RETRY_ARM,
    EVENT_ACTION_ARM_HOME,
    EVENT_ACTION_ARM_NIGHT,
    EVENT_ACTION_ARM_VACATION,
    STORAGE_VERSION_MAJOR,
    STORAGE_VERSION_MINOR,
)


# ─── bcrypt hashing ──────────────────────────────────────────────────────────

class TestBcryptHashing:
    """Test bcrypt code hashing in SecureMeStore."""

    def test_hash_code_returns_string(self):
        hashed = SecureMeStore._hash_code("1234")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_different_from_plaintext(self):
        hashed = SecureMeStore._hash_code("1234")
        assert hashed != "1234"

    def test_check_code_correct(self):
        hashed = SecureMeStore._hash_code("5678")
        assert SecureMeStore._check_code("5678", hashed) is True

    def test_check_code_wrong(self):
        hashed = SecureMeStore._hash_code("5678")
        assert SecureMeStore._check_code("9999", hashed) is False

    def test_check_code_empty_wrong(self):
        hashed = SecureMeStore._hash_code("5678")
        assert SecureMeStore._check_code("", hashed) is False

    def test_two_hashes_of_same_code_differ(self):
        """bcrypt uses random salt — same code hashes differently each time."""
        h1 = SecureMeStore._hash_code("1234")
        h2 = SecureMeStore._hash_code("1234")
        assert h1 != h2

    def test_both_hashes_verify_correctly(self):
        h1 = SecureMeStore._hash_code("1234")
        h2 = SecureMeStore._hash_code("1234")
        assert SecureMeStore._check_code("1234", h1) is True
        assert SecureMeStore._check_code("1234", h2) is True

    @pytest.mark.asyncio
    async def test_save_user_hashes_code(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_user("u1", {"name": "Admin", "code": "1234", "enabled": True})

        user = store.get_users()["u1"]
        assert user["code"] != "1234"
        assert user["code_hashed"] is True
        # Verify hash is valid bcrypt
        assert SecureMeStore._check_code("1234", user["code"]) is True

    @pytest.mark.asyncio
    async def test_save_user_no_code_stays_empty(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_user("u2", {"name": "Guest", "code": "", "enabled": True})

        user = store.get_users()["u2"]
        assert user["code"] == ""
        assert not user.get("code_hashed", False)

    def test_authenticate_user_hashed_code(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        hashed = SecureMeStore._hash_code("9876")
        store._data["users"]["u1"] = {
            "name": "Test",
            "code": hashed,
            "code_hashed": True,
            "enabled": True,
        }

        result = store.authenticate_user("9876")
        assert result is not None
        assert result["name"] == "Test"

    def test_authenticate_user_wrong_code_returns_none(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        hashed = SecureMeStore._hash_code("9876")
        store._data["users"]["u1"] = {
            "name": "Test",
            "code": hashed,
            "code_hashed": True,
            "enabled": True,
        }

        result = store.authenticate_user("0000")
        assert result is None

    def test_authenticate_user_disabled_returns_none(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        hashed = SecureMeStore._hash_code("1234")
        store._data["users"]["u1"] = {
            "name": "Disabled",
            "code": hashed,
            "code_hashed": True,
            "enabled": False,
        }

        result = store.authenticate_user("1234")
        assert result is None

    def test_authenticate_user_plaintext_fallback(self):
        """Legacy users without code_hashed=True use plaintext comparison."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._data["users"]["u1"] = {
            "name": "Legacy",
            "code": "oldplaintext",
            "code_hashed": False,
            "enabled": True,
        }

        result = store.authenticate_user("oldplaintext")
        assert result is not None

    def test_authenticate_user_by_id(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        hashed = SecureMeStore._hash_code("abc")
        store._data["users"]["u1"] = {
            "name": "Specific",
            "code": hashed,
            "code_hashed": True,
            "enabled": True,
        }

        result = store.authenticate_user("abc", user_id="u1")
        assert result is not None

        result_wrong = store.authenticate_user("xyz", user_id="u1")
        assert result_wrong is None

    def test_authenticate_nonexistent_user_by_id(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()

        result = store.authenticate_user("1234", user_id="nobody")
        assert result is None


# ─── Storage versioning ───────────────────────────────────────────────────────

class TestStorageVersioning:
    """Test STORAGE_VERSION_MAJOR / MINOR constants."""

    def test_storage_version_major_is_2(self):
        assert STORAGE_VERSION_MAJOR == 2

    def test_storage_version_minor_is_0(self):
        assert STORAGE_VERSION_MINOR == 1

    def test_default_data_has_sensor_groups(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        assert "sensor_groups" in defaults
        assert isinstance(defaults["sensor_groups"], dict)

    def test_default_data_sensors_have_per_sensor_fields(self):
        """sensor_groups key is in default — sensors themselves get fields on load."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        # sensors dict starts empty; fields are added when sensors are saved
        assert "sensors" in defaults


# ─── Sensor Groups ────────────────────────────────────────────────────────────

class TestSensorGroup:
    """Unit tests for the SensorGroup anti-masking class."""

    def test_single_activation_below_threshold(self):
        group = SensorGroup("g1", "Test", ["s1", "s2"], timeout=30, event_count=2)
        result = group.record_activation("s1")
        assert result is False

    def test_two_activations_meets_threshold(self):
        group = SensorGroup("g1", "Test", ["s1", "s2"], timeout=30, event_count=2)
        group.record_activation("s1")
        result = group.record_activation("s2")
        assert result is True

    def test_same_sensor_twice_counts_as_one(self):
        """Repeated activation of same sensor should not double-count."""
        group = SensorGroup("g1", "Test", ["s1", "s2"], timeout=30, event_count=2)
        group.record_activation("s1")
        result = group.record_activation("s1")
        # Still only 1 unique sensor active
        assert result is False

    def test_timeout_zero_means_no_expiry(self):
        """timeout=0 disables window — all activations always count."""
        group = SensorGroup("g1", "Test", ["s1", "s2", "s3"], timeout=0, event_count=3)
        group.record_activation("s1")
        group.record_activation("s2")
        result = group.record_activation("s3")
        assert result is True

    def test_expired_activations_removed(self):
        """Activations older than timeout should be discarded."""
        group = SensorGroup("g1", "Test", ["s1", "s2"], timeout=1, event_count=2)
        # Manually inject a stale activation
        group._activations["s1"] = time.monotonic() - 10  # 10s ago > 1s timeout
        result = group.record_activation("s2")
        # s1 expired, only s2 active — threshold not met
        assert result is False

    def test_reset_clears_activations(self):
        group = SensorGroup("g1", "Test", ["s1", "s2"], timeout=30, event_count=2)
        group.record_activation("s1")
        group.record_activation("s2")
        group.reset()
        assert len(group._activations) == 0

    def test_event_count_one_triggers_immediately(self):
        """event_count=1 means any single sensor triggers the group."""
        group = SensorGroup("g1", "Test", ["s1"], timeout=30, event_count=1)
        result = group.record_activation("s1")
        assert result is True


class TestSensorGroupInStore:
    """Tests for sensor group CRUD in SecureMeStore."""

    @pytest.mark.asyncio
    async def test_save_and_get_sensor_group(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        group_id = await store.async_save_sensor_group(None, {
            "name": "Entry sensors",
            "entities": ["binary_sensor.front_door", "binary_sensor.back_door"],
            "timeout": 30,
            "event_count": 2,
        })

        assert group_id is not None
        groups = store.get_sensor_groups()
        assert group_id in groups
        g = groups[group_id]
        assert g["name"] == "Entry sensors"
        assert g["event_count"] == 2
        assert g["timeout"] == 30
        assert "binary_sensor.front_door" in g["entities"]

    @pytest.mark.asyncio
    async def test_update_sensor_group(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        gid = await store.async_save_sensor_group("fixed_id", {
            "name": "Old name",
            "entities": ["s1"],
            "timeout": 10,
            "event_count": 2,
        })
        assert gid == "fixed_id"

        await store.async_save_sensor_group("fixed_id", {
            "name": "New name",
            "entities": ["s1", "s2"],
            "timeout": 20,
            "event_count": 3,
        })

        g = store.get_sensor_groups()["fixed_id"]
        assert g["name"] == "New name"
        assert g["event_count"] == 3

    @pytest.mark.asyncio
    async def test_delete_sensor_group(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        gid = await store.async_save_sensor_group(None, {
            "name": "To delete",
            "entities": ["s1"],
            "timeout": 0,
            "event_count": 2,
        })

        result = await store.async_delete_sensor_group(gid)
        assert result is True
        assert gid not in store.get_sensor_groups()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_group(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        result = await store.async_delete_sensor_group("does_not_exist")
        assert result is False

    def test_get_group_for_sensor(self):
        """store.get_sensor_groups() is the surviving public accessor -- the
        singular get_group_for_sensor()/get_sensor_group() helpers were removed
        as dead code (zero production callers; only get_sensor_groups() /
        the plural form is used by ws_sensors.py). This test now checks the
        same lookup-by-sensor behaviour directly against the full dict.
        """
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._data["sensor_groups"]["g1"] = {
            "group_id": "g1",
            "name": "G1",
            "entities": ["binary_sensor.door1", "binary_sensor.door2"],
            "timeout": 30,
            "event_count": 2,
        }

        def _find_group_for_sensor(groups, entity_id):
            for gid, group in groups.items():
                if entity_id in group.get("entities", []):
                    return gid
            return None

        groups = store.get_sensor_groups()
        assert _find_group_for_sensor(groups, "binary_sensor.door1") == "g1"
        assert _find_group_for_sensor(groups, "binary_sensor.other") is None


# ─── ZoneManager sensor group integration ────────────────────────────────────

class TestZoneManagerSensorGroups:
    """Test ZoneManager.load_sensor_groups and anti-masking during monitoring."""

    def _make_hass(self):
        mock_hass = MagicMock()
        mock_hass.states = MagicMock()
        mock_hass.states.get = MagicMock(return_value=None)
        return mock_hass

    def test_load_sensor_groups(self):
        zm = ZoneManager(self._make_hass())
        zm.load_sensor_groups({
            "g1": {
                "group_id": "g1",
                "name": "Doors",
                "entities": ["binary_sensor.d1", "binary_sensor.d2"],
                "timeout": 30,
                "event_count": 2,
            }
        })
        assert "g1" in zm._sensor_groups
        assert zm._sensor_groups["g1"].event_count == 2

    def test_get_group_for_sensor_found(self):
        zm = ZoneManager(self._make_hass())
        zm.load_sensor_groups({
            "g1": {
                "group_id": "g1",
                "name": "G",
                "entities": ["binary_sensor.x"],
                "timeout": 0,
                "event_count": 2,
            }
        })
        group = zm._get_group_for_sensor("binary_sensor.x")
        assert group is not None
        assert group.group_id == "g1"

    def test_get_group_for_sensor_not_found(self):
        zm = ZoneManager(self._make_hass())
        zm.load_sensor_groups({})
        group = zm._get_group_for_sensor("binary_sensor.unknown")
        assert group is None

    def test_reset_sensor_groups(self):
        zm = ZoneManager(self._make_hass())
        zm.load_sensor_groups({
            "g1": {
                "group_id": "g1",
                "name": "G",
                "entities": ["s1", "s2"],
                "timeout": 30,
                "event_count": 2,
            }
        })
        zm._sensor_groups["g1"]._activations["s1"] = time.monotonic()
        zm.reset_sensor_groups()
        assert len(zm._sensor_groups["g1"]._activations) == 0


class TestHomeAloneDoorDispatchDebounce:
    """Regression: the Home Alone door-notification dispatch (camera snapshot
    + push + TTS) used to fire on every single sensor trigger with zero
    debounce -- unlike the normal alarm trigger path, which suppresses rapid
    re-fires per sensor. A door that rattles in the wind or has a bouncy
    contact sensor could spam push/TTS repeatedly. Uses the real hass fixture
    (not a mirror) so the actual async_track_state_change_event wiring in
    ZoneManager.start_monitoring is exercised end-to-end.
    """

    @pytest.mark.asyncio
    async def test_rapid_door_flap_dispatches_only_once(self, hass):
        hass.states.async_set("binary_sensor.front_door", "off", {"device_class": "door"})
        await hass.async_block_till_done()

        zm = ZoneManager(hass)
        zm.add_zone("z1", "entry", sensors=["binary_sensor.front_door"], enabled=True, arm_modes=["home_alone"])
        zm.load_sensor_configs({})

        with patch(
            "custom_components.secure_me.notification_dispatcher.dispatch_home_alone_door_trigger",
            new=AsyncMock(),
        ) as mock_dispatch:
            zm.start_monitoring(callback_func=AsyncMock(), arm_mode="home_alone")

            # Rapid flap: on -> off -> on, all within the 0.5s debounce window
            hass.states.async_set("binary_sensor.front_door", "on", {"device_class": "door"})
            await hass.async_block_till_done()
            hass.states.async_set("binary_sensor.front_door", "off", {"device_class": "door"})
            await hass.async_block_till_done()
            hass.states.async_set("binary_sensor.front_door", "on", {"device_class": "door"})
            await hass.async_block_till_done()

            assert mock_dispatch.call_count == 1

    @pytest.mark.asyncio
    async def test_different_doors_debounced_independently(self, hass):
        """Debounce is keyed per-entity -- one door flapping must not
        suppress a genuine, simultaneous trigger from a different door."""
        hass.states.async_set("binary_sensor.front_door", "off", {"device_class": "door"})
        hass.states.async_set("binary_sensor.back_door", "off", {"device_class": "door"})
        await hass.async_block_till_done()

        zm = ZoneManager(hass)
        zm.add_zone(
            "z1", "entry",
            sensors=["binary_sensor.front_door", "binary_sensor.back_door"],
            enabled=True, arm_modes=["home_alone"],
        )
        zm.load_sensor_configs({})

        with patch(
            "custom_components.secure_me.notification_dispatcher.dispatch_home_alone_door_trigger",
            new=AsyncMock(),
        ) as mock_dispatch:
            zm.start_monitoring(callback_func=AsyncMock(), arm_mode="home_alone")

            hass.states.async_set("binary_sensor.front_door", "on", {"device_class": "door"})
            await hass.async_block_till_done()
            hass.states.async_set("binary_sensor.back_door", "on", {"device_class": "door"})
            await hass.async_block_till_done()

            assert mock_dispatch.call_count == 2


# ─── Per-sensor fields in store ───────────────────────────────────────────────

class TestPerSensorFields:
    """Test per-sensor entry_delay, auto_bypass, arm_on_close in store."""

    @pytest.mark.asyncio
    async def test_save_sensor_with_entry_delay(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_sensors_bulk({
            "binary_sensor.garage": {"enabled": True, "entry_delay": 45, "auto_bypass": False, "arm_on_close": False},
        })

        sensors = store.get_sensors()
        assert sensors["binary_sensor.garage"]["entry_delay"] == 45

    @pytest.mark.asyncio
    async def test_save_sensor_with_auto_bypass(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_sensors_bulk({
            "binary_sensor.back_door": {"enabled": True, "entry_delay": None, "auto_bypass": True, "arm_on_close": False},
        })

        sensors = store.get_sensors()
        assert sensors["binary_sensor.back_door"]["auto_bypass"] is True

    @pytest.mark.asyncio
    async def test_save_sensor_with_arm_on_close(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_sensors_bulk({
            "binary_sensor.front_door": {"enabled": True, "entry_delay": None, "auto_bypass": False, "arm_on_close": True},
        })

        sensors = store.get_sensors()
        assert sensors["binary_sensor.front_door"]["arm_on_close"] is True


# ─── ZoneManager per-sensor helpers ──────────────────────────────────────────

class TestZoneManagerPerSensorHelpers:
    """Test per-sensor helpers in ZoneManager."""

    def _make_hass(self):
        mock_hass = MagicMock()
        mock_hass.states = MagicMock()
        mock_hass.states.get = MagicMock(return_value=None)
        return mock_hass

    def test_get_sensor_entry_delay_override(self):
        zm = ZoneManager(self._make_hass())
        zm.load_sensor_configs({
            "binary_sensor.garage": {"entry_delay": 45, "auto_bypass": False, "arm_on_close": False}
        })
        delay = zm.get_sensor_entry_delay("binary_sensor.garage", zone_default=30)
        assert delay == 45

    def test_get_sensor_entry_delay_uses_default_when_none(self):
        zm = ZoneManager(self._make_hass())
        zm.load_sensor_configs({
            "binary_sensor.other": {"entry_delay": None, "auto_bypass": False, "arm_on_close": False}
        })
        delay = zm.get_sensor_entry_delay("binary_sensor.other", zone_default=30)
        assert delay == 30

    def test_get_sensor_entry_delay_uses_default_when_missing(self):
        zm = ZoneManager(self._make_hass())
        zm.load_sensor_configs({})
        delay = zm.get_sensor_entry_delay("binary_sensor.unknown", zone_default=20)
        assert delay == 20

    def test_get_auto_bypass_sensors_open(self):
        hass = self._make_hass()

        # Mock: front_door is open, back_door is closed
        def mock_states_get(entity_id):
            s = MagicMock()
            if entity_id == "binary_sensor.front_door":
                s.state = "on"
            else:
                s.state = "off"
            return s

        hass.states.get = mock_states_get

        zm = ZoneManager(hass)
        zm.load_sensor_configs({
            "binary_sensor.front_door": {"auto_bypass": True, "entry_delay": None, "arm_on_close": False},
            "binary_sensor.back_door": {"auto_bypass": True, "entry_delay": None, "arm_on_close": False},
        })

        bypassed = zm.get_auto_bypass_sensors(
            ["binary_sensor.front_door", "binary_sensor.back_door"]
        )
        assert "binary_sensor.front_door" in bypassed
        assert "binary_sensor.back_door" not in bypassed

    def test_get_auto_bypass_sensors_not_marked(self):
        hass = self._make_hass()

        def mock_states_get(entity_id):
            s = MagicMock()
            s.state = "on"  # open but NOT marked auto_bypass
            return s

        hass.states.get = mock_states_get

        zm = ZoneManager(hass)
        zm.load_sensor_configs({
            "binary_sensor.door": {"auto_bypass": False, "entry_delay": None, "arm_on_close": False},
        })

        bypassed = zm.get_auto_bypass_sensors(["binary_sensor.door"])
        assert bypassed == []

    def test_load_sensor_configs_stores_correctly(self):
        zm = ZoneManager(self._make_hass())
        configs = {
            "binary_sensor.a": {"entry_delay": 10, "auto_bypass": True, "arm_on_close": False},
            "binary_sensor.b": {"entry_delay": None, "auto_bypass": False, "arm_on_close": True},
        }
        zm.load_sensor_configs(configs)
        assert zm._sensor_configs["binary_sensor.a"]["auto_bypass"] is True
        assert zm._sensor_configs["binary_sensor.b"]["arm_on_close"] is True


# ─── Push notification constants ─────────────────────────────────────────────

class TestPushNotificationConstants:
    """Test that push notification action constants are correct."""

    def test_push_event_is_mobile_app(self):
        assert PUSH_EVENT == "mobile_app_notification_action"

    def test_all_actions_present(self):
        expected = {
            "SECURE_ME_FORCE_ARM",
            "SECURE_ME_RETRY_ARM",
            "SECURE_ME_DISARM",
            "SECURE_ME_ARM_AWAY",
            "SECURE_ME_ARM_HOME",
            "SECURE_ME_ARM_NIGHT",
            "SECURE_ME_ARM_VACATION",
            "SECURE_ME_ARM_HOME_ALONE",
            # v1.5.0: Home Alone door-notification quick-response buttons
            "SECURE_ME_HOME_ALONE_ACTION_1",
            "SECURE_ME_HOME_ALONE_ACTION_2",
        }
        assert set(PUSH_EVENT_ACTIONS) == expected

    def test_action_constants_match_list(self):
        assert EVENT_ACTION_DISARM in PUSH_EVENT_ACTIONS
        assert EVENT_ACTION_ARM_AWAY in PUSH_EVENT_ACTIONS
        assert EVENT_ACTION_FORCE_ARM in PUSH_EVENT_ACTIONS
        assert EVENT_ACTION_RETRY_ARM in PUSH_EVENT_ACTIONS
        assert EVENT_ACTION_ARM_HOME in PUSH_EVENT_ACTIONS
        assert EVENT_ACTION_ARM_NIGHT in PUSH_EVENT_ACTIONS
        assert EVENT_ACTION_ARM_VACATION in PUSH_EVENT_ACTIONS

    def test_no_duplicate_actions(self):
        assert len(PUSH_EVENT_ACTIONS) == len(set(PUSH_EVENT_ACTIONS))

    def test_all_actions_prefixed_secure_me(self):
        for action in PUSH_EVENT_ACTIONS:
            assert action.startswith("SECURE_ME_"), f"{action} missing SECURE_ME_ prefix"


# ─── Store default data v2 completeness ──────────────────────────────────────

class TestDefaultDataV2:
    """Verify all v1.2.0 keys present in default data."""

    def test_all_v2_keys_present(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        required = {
            "sensors", "sensor_groups", "zones", "users",
            "modules", "notifications", "automations",
            "fake_presence", "home_alone_cameras",
        }
        assert required.issubset(set(defaults.keys()))

    def test_sensor_groups_empty_by_default(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        assert defaults["sensor_groups"] == {}

    def test_modules_still_has_all_six(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        assert set(defaults["modules"].keys()) == {
            "camera", "lock", "lights", "climate", "siren", "tts"
        }

    def test_speaker_profiles_empty_by_default(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        assert "speaker_profiles" in defaults
        assert defaults["speaker_profiles"] == []


# -- Speaker profiles (v1.4.0) -----------------------------------------------

class TestSpeakerProfiles:
    """Tests for speaker profile CRUD in SecureMeStore."""

    def test_get_speaker_profiles_returns_list(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        assert isinstance(store.get_speaker_profiles(), list)

    @pytest.mark.asyncio
    async def test_save_and_get_speaker_profiles(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        profiles = [
            {
                "entity_id": "media_player.stue",
                "name": "Stue",
                "volume": 0.6,
                "tts_service": "tts.cloud_say",
                "tts_entity": "tts.home_assistant_cloud",
            },
            {
                "entity_id": "media_player.kontor",
                "name": "Kontor",
                "volume": 0.4,
                "tts_service": "tts.cloud_say",
                "tts_entity": "tts.home_assistant_cloud",
            },
        ]
        await store.async_save_speaker_profiles(profiles)
        result = store.get_speaker_profiles()
        assert len(result) == 2
        assert result[0]["name"] == "Stue"
        assert result[1]["volume"] == 0.4

    @pytest.mark.asyncio
    async def test_save_speaker_profiles_overwrites(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_speaker_profiles([
            {"entity_id": "media_player.a", "name": "A", "volume": 0.5,
             "tts_service": "tts.cloud_say", "tts_entity": "tts.home_assistant_cloud"}
        ])
        await store.async_save_speaker_profiles([])
        assert store.get_speaker_profiles() == []
