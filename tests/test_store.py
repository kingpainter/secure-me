"""Tests for Secure Me store."""
# VERSION = "1.5.0"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.secure_me.store import SecureMeStore


class TestStoreDefaults:
    """Test store default data structure."""

    def test_default_data_has_all_keys(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        expected_keys = {"sensors", "sensor_groups", "zones", "users", "modules",
                         "notifications", "automations", "scheduled_tests",
                         "speaker_profiles",
                         "fake_presence", "home_alone_cameras",
                         "auto_actions",
                         "floorplan"}
        assert set(defaults.keys()) == expected_keys

    def test_default_fake_presence_is_dict_v2(self):
        """fake_presence is now a v2 dict, not a plain bool."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        fp = defaults["fake_presence"]
        assert isinstance(fp, dict)
        assert fp["active"] is False
        assert "block_alarm" in fp
        assert "block_locks" in fp
        assert "block_cameras" in fp

    def test_default_fake_presence_active_is_false(self):
        """get_fake_presence() returns False when fake_presence.active is False."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        assert store.get_fake_presence() is False

    def test_default_auto_actions_has_expected_keys(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        aa = defaults["auto_actions"]
        expected = {
            "auto_lock_enabled", "auto_lock_delay",
            "auto_alarm_enabled", "auto_alarm_delay",
            "auto_camera_enabled", "auto_camera_delay",
            "arrival_confirmation_delay", "notify_all_users",
        }
        assert set(aa.keys()) == expected

    def test_default_auto_actions_defaults(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        aa = defaults["auto_actions"]
        assert aa["auto_lock_enabled"] is True
        assert aa["auto_lock_delay"] == 120
        assert aa["auto_alarm_enabled"] is True
        assert aa["auto_alarm_delay"] == 300
        assert aa["auto_camera_enabled"] is True
        assert aa["auto_camera_delay"] == 0
        assert aa["arrival_confirmation_delay"] == 60
        assert aa["notify_all_users"] is False

    def test_default_home_alone_cameras_is_empty(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        assert defaults["home_alone_cameras"] == []

    def test_default_modules_all_disabled(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        for mod_id, mod_config in defaults["modules"].items():
            assert mod_config["enabled"] is False

    def test_default_modules_has_all_six(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        expected = {"camera", "lock", "lights", "climate", "siren", "tts"}
        assert set(defaults["modules"].keys()) == expected


class TestStoreInferType:
    """Test sensor type inference."""

    def test_infer_door(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        assert store._infer_type("door") == "contact"

    def test_infer_window(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        assert store._infer_type("window") == "contact"

    def test_infer_motion(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        assert store._infer_type("motion") == "motion"

    def test_infer_occupancy(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        assert store._infer_type("occupancy") == "motion"

    def test_infer_presence(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        assert store._infer_type("presence") == "presence"

    def test_infer_unknown_defaults_contact(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        assert store._infer_type("foobar") == "contact"


class TestStoreFakePresence:
    """Test fake presence CRUD."""

    def test_get_fake_presence_default_false(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        assert store.get_fake_presence() is False

    @pytest.mark.asyncio
    async def test_set_fake_presence_true(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_set_fake_presence(True)
        assert store.get_fake_presence() is True

    @pytest.mark.asyncio
    async def test_set_fake_presence_false(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        # Set active via the v2 dict
        store._data["fake_presence"]["active"] = True
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_set_fake_presence(False)
        assert store.get_fake_presence() is False

    def test_get_fake_presence_v2_returns_dict(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        fp = store.get_fake_presence_v2()
        assert isinstance(fp, dict)
        assert "active" in fp
        assert "block_alarm" in fp
        assert "block_locks" in fp
        assert "block_cameras" in fp

    @pytest.mark.asyncio
    async def test_save_fake_presence_v2(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        config = {"active": True, "block_alarm": False, "block_locks": True, "block_cameras": False}
        await store.async_save_fake_presence_v2(config)
        fp = store.get_fake_presence_v2()
        assert fp["active"] is True
        assert fp["block_locks"] is True
        assert fp["block_alarm"] is False
        # get_fake_presence() (v1 compat) should also reflect active state
        assert store.get_fake_presence() is True

    @pytest.mark.asyncio
    async def test_legacy_bool_migration(self):
        """If store has old bool fake_presence, get_fake_presence() still works."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._data["fake_presence"] = True  # legacy bool
        assert store.get_fake_presence() is True
        store._data["fake_presence"] = False
        assert store.get_fake_presence() is False

    def test_get_home_alone_cameras_default_empty(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        assert store.get_home_alone_cameras() == []

    @pytest.mark.asyncio
    async def test_save_and_get_home_alone_cameras(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        cameras = ["camera.front", "camera.back"]
        await store.async_save_home_alone_cameras(cameras)
        assert store.get_home_alone_cameras() == cameras


class TestStoreCRUD:
    """Test store CRUD operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_zone(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_zone("zone_1", {"name": "Entry", "type": "entry"})
        zones = store.get_zones()
        assert "zone_1" in zones
        assert zones["zone_1"]["name"] == "Entry"

    @pytest.mark.asyncio
    async def test_delete_zone(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._data["zones"]["zone_1"] = {"name": "Test"}
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        result = await store.async_delete_zone("zone_1")
        assert result is True
        assert "zone_1" not in store.get_zones()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_zone(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        result = await store.async_delete_zone("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_save_and_get_user(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_user("user_1", {"name": "Admin", "role": "admin"})
        users = store.get_users()
        assert "user_1" in users
        assert users["user_1"]["name"] == "Admin"

    @pytest.mark.asyncio
    async def test_save_and_get_notification(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_notification("notif_1", {
            "name": "Alert",
            "service": "notify.notify",
            "message": "Test alert",
        })
        notifs = store.get_notifications()
        assert "notif_1" in notifs

    @pytest.mark.asyncio
    async def test_save_and_get_automation(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_automation("auto_1", {
            "name": "Auto Arm",
            "trigger": "everyone_leaves",
            "actions": [{"service": "secure_me.arm_away"}],
        })
        autos = store.get_automations()
        assert "auto_1" in autos

    @pytest.mark.asyncio
    async def test_delete_automation(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._data["automations"]["auto_1"] = {"name": "Test"}
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        result = await store.async_delete_automation("auto_1")
        assert result is True
        assert "auto_1" not in store.get_automations()

    @pytest.mark.asyncio
    async def test_save_module_config(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_save_module("camera", {
            "enabled": True,
            "entities": ["camera.front"],
            "config": {"poe_delay": 5},
        })
        modules = store.get_modules()
        assert modules["camera"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_save_sensors_bulk(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        sensors = {
            "binary_sensor.door": {"enabled": True, "sensor_type": "contact"},
            "binary_sensor.motion": {"enabled": False, "sensor_type": "motion"},
        }
        await store.async_save_sensors_bulk(sensors)
        assert len(store.get_sensors()) == 2


class TestStoreTestHistory:
    """Tests for get_test_history() / async_append_test_result().

    Previously get_test_history() had zero test coverage and zero callers --
    ws_get_test_results() in ws_modules.py reached into store._data directly
    instead of using the public accessor. Now wired in, so this needs
    real coverage.
    """

    def test_get_test_history_default_empty(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        assert store.get_test_history() == []

    @pytest.mark.asyncio
    async def test_append_test_result_adds_entry(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_append_test_result({"test_type": "quick", "overall": "pass"})
        history = store.get_test_history()
        assert len(history) == 1
        assert history[0]["overall"] == "pass"

    @pytest.mark.asyncio
    async def test_append_test_result_newest_first(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        await store.async_append_test_result({"test_type": "quick", "overall": "pass"})
        await store.async_append_test_result({"test_type": "full", "overall": "fail"})
        history = store.get_test_history()
        assert history[0]["test_type"] == "full"
        assert history[1]["test_type"] == "quick"

    @pytest.mark.asyncio
    async def test_append_test_result_caps_at_ten(self):
        """Only the last 10 test results are kept."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        store._data = store._default_data()
        store._store = MagicMock()
        store._store.async_save = AsyncMock()

        for i in range(15):
            await store.async_append_test_result({"test_type": "quick", "overall": str(i)})
        history = store.get_test_history()
        assert len(history) == 10
        # Newest (i=14) first
        assert history[0]["overall"] == "14"


class TestGetAreaName:
    """Tests for _get_area_name() -- room/area lookup used to group the
    sensor list in the panel by HA area instead of an unsorted flat list.
    """

    def test_entity_with_direct_area_returns_area_name(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)

        mock_entry = MagicMock(area_id="area_kitchen", device_id=None)
        mock_area = MagicMock(name="Køkken")
        mock_area.name = "Køkken"

        with patch("homeassistant.helpers.entity_registry.async_get") as mock_er, \
             patch("homeassistant.helpers.area_registry.async_get") as mock_ar:
            mock_er.return_value.async_get.return_value = mock_entry
            mock_ar.return_value.async_get_area.return_value = mock_area
            result = store._get_area_name("binary_sensor.kitchen_door")

        assert result == "Køkken"

    def test_entity_falls_back_to_device_area(self):
        """Most entities don't have their own area -- they inherit from their device."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)

        mock_entry = MagicMock(area_id=None, device_id="device_1")
        mock_device = MagicMock(area_id="area_hall")
        mock_area = MagicMock()
        mock_area.name = "Entré"

        with patch("homeassistant.helpers.entity_registry.async_get") as mock_er, \
             patch("homeassistant.helpers.device_registry.async_get") as mock_dr, \
             patch("homeassistant.helpers.area_registry.async_get") as mock_ar:
            mock_er.return_value.async_get.return_value = mock_entry
            mock_dr.return_value.async_get.return_value = mock_device
            mock_ar.return_value.async_get_area.return_value = mock_area
            result = store._get_area_name("binary_sensor.hall_motion")

        assert result == "Entré"

    def test_no_area_anywhere_returns_andet(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)

        mock_entry = MagicMock(area_id=None, device_id=None)

        with patch("homeassistant.helpers.entity_registry.async_get") as mock_er:
            mock_er.return_value.async_get.return_value = mock_entry
            result = store._get_area_name("binary_sensor.unassigned")

        assert result == "Andet"

    def test_entity_not_in_registry_returns_andet(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)

        with patch("homeassistant.helpers.entity_registry.async_get") as mock_er:
            mock_er.return_value.async_get.return_value = None
            result = store._get_area_name("binary_sensor.not_registered")

        assert result == "Andet"

    def test_area_id_set_but_area_deleted_returns_andet(self):
        """area_id points at an area that no longer exists in the registry."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)

        mock_entry = MagicMock(area_id="area_deleted", device_id=None)

        with patch("homeassistant.helpers.entity_registry.async_get") as mock_er, \
             patch("homeassistant.helpers.area_registry.async_get") as mock_ar:
            mock_er.return_value.async_get.return_value = mock_entry
            mock_ar.return_value.async_get_area.return_value = None
            result = store._get_area_name("binary_sensor.orphaned")

        assert result == "Andet"

    def test_registry_lookup_exception_returns_andet(self):
        """Any unexpected error must not break sensor list rendering."""
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)

        with patch("homeassistant.helpers.entity_registry.async_get", side_effect=RuntimeError("boom")):
            result = store._get_area_name("binary_sensor.whatever")

        assert result == "Andet"
