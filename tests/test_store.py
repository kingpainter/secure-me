"""Tests for Secure Me store."""
# VERSION = "0.3.0"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from custom_components.secure_me.store import SecureMeStore


class TestStoreDefaults:
    """Test store default data structure."""

    def test_default_data_has_all_keys(self):
        mock_hass = MagicMock()
        store = SecureMeStore(mock_hass)
        defaults = store._default_data()
        expected_keys = {"sensors", "zones", "users", "modules",
                         "notifications", "automations"}
        assert set(defaults.keys()) == expected_keys

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
