"""Data storage for Secure Me panel configuration."""
# VERSION = "1.0.0"

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.panel_config"


class SecureMeStore:
    """Manage persistent storage for Secure Me panel."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize store."""
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._data: dict[str, Any] = {}

    async def async_load(self) -> None:
        """Load data from storage."""
        stored = await self._store.async_load()
        if stored:
            self._data = stored
        else:
            self._data = self._default_data()
        _LOGGER.info("Secure Me store loaded (%d sensors, %d zones, %d users)",
                     len(self._data.get("sensors", {})),
                     len(self._data.get("zones", {})),
                     len(self._data.get("users", {})))

    async def async_save(self) -> None:
        """Save data to storage."""
        await self._store.async_save(self._data)

    def _default_data(self) -> dict[str, Any]:
        """Return default data structure."""
        return {
            "sensors": {},
            "zones": {},
            "users": {},
            "modules": {
                "camera": {"enabled": False, "entities": [], "config": {}},
                "lock": {"enabled": False, "entities": [], "config": {}},
                "lights": {"enabled": False, "entities": [], "config": {}},
                "climate": {"enabled": False, "entities": [], "config": {}},
                "siren": {"enabled": False, "entities": [], "config": {}},
                "tts": {"enabled": False, "entities": [], "config": {}},
            },
            "notifications": {},
            "automations": {},
        }

    # ─── Sensors ───

    def get_sensors(self) -> dict[str, Any]:
        """Get all configured sensors."""
        return self._data.get("sensors", {})

    # Environmental device classes — always monitored, cannot be disabled
    _ENV_CLASSES = frozenset({"smoke", "gas", "moisture"})

    def get_available_sensors(self) -> list[dict[str, Any]]:
        """Get all available binary_sensors from HA that could be alarm sensors.

        Environmental sensors (smoke, gas, moisture) are always enabled and
        use sensor_type "environmental". They are displayed in a separate
        read-only section in the panel and cannot be toggled off.
        """
        sensors = []
        for state in self.hass.states.async_all("binary_sensor"):
            device_class = state.attributes.get("device_class", "")
            if device_class in ("door", "window", "garage_door", "opening",
                                "motion", "occupancy", "presence",
                                "vibration", "smoke", "gas", "moisture"):
                configured = self._data.get("sensors", {}).get(state.entity_id, {})
                # is_environmental: True if device_class matches OR user manually marked it
                is_env = (
                    device_class in self._ENV_CLASSES
                    or configured.get("is_environmental", False)
                )
                sensors.append({
                    "entity_id": state.entity_id,
                    "name": state.attributes.get("friendly_name", state.entity_id),
                    "device_class": device_class,
                    "state": state.state,
                    "is_environmental": is_env,
                    # Environmental sensors are always enabled — user cannot toggle
                    "enabled": True if is_env else configured.get("enabled", False),
                    "sensor_type": "environmental" if is_env else configured.get("sensor_type", self._infer_type(device_class)),
                })
        # Also include person/device_tracker for presence
        for state in self.hass.states.async_all("person"):
            configured = self._data.get("sensors", {}).get(state.entity_id, {})
            sensors.append({
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "device_class": "presence",
                "state": state.state,
                "enabled": configured.get("enabled", False),
                "sensor_type": "presence",
            })
        for state in self.hass.states.async_all("device_tracker"):
            configured = self._data.get("sensors", {}).get(state.entity_id, {})
            sensors.append({
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "device_class": "presence",
                "state": state.state,
                "enabled": configured.get("enabled", False),
                "sensor_type": "presence",
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

    async def async_save_sensor(self, entity_id: str, config: dict[str, Any]) -> None:
        """Save sensor configuration."""
        if "sensors" not in self._data:
            self._data["sensors"] = {}
        self._data["sensors"][entity_id] = config
        await self.async_save()

    async def async_save_sensors_bulk(self, sensors: dict[str, Any]) -> None:
        """Save multiple sensor configurations at once."""
        self._data["sensors"] = sensors
        await self.async_save()

    # ─── Zones ───

    def get_zones(self) -> dict[str, Any]:
        """Get all zones."""
        return self._data.get("zones", {})

    async def async_save_zone(self, zone_id: str, config: dict[str, Any]) -> None:
        """Save zone configuration."""
        if "zones" not in self._data:
            self._data["zones"] = {}
        self._data["zones"][zone_id] = config
        await self.async_save()

    async def async_delete_zone(self, zone_id: str) -> bool:
        """Delete a zone."""
        if zone_id in self._data.get("zones", {}):
            del self._data["zones"][zone_id]
            await self.async_save()
            return True
        return False

    # ─── Users ───

    def get_users(self) -> dict[str, Any]:
        """Get all users."""
        return self._data.get("users", {})

    async def async_save_user(self, user_id: str, config: dict[str, Any]) -> None:
        """Save user configuration."""
        if "users" not in self._data:
            self._data["users"] = {}
        self._data["users"][user_id] = config
        await self.async_save()

    async def async_delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id in self._data.get("users", {}):
            del self._data["users"][user_id]
            await self.async_save()
            return True
        return False

    def get_nfc_tags(self) -> list[dict[str, str]]:
        """Get available NFC tags from HA."""
        tags = []
        # Check tag registry if available
        tag_registry = self.hass.data.get("tag")
        if tag_registry and hasattr(tag_registry, "async_list_tags"):
            for tag in tag_registry.async_list_tags():
                tags.append({
                    "id": tag.id,
                    "name": tag.name or tag.id,
                })
        return tags

    # ─── Modules ───

    def get_modules(self) -> dict[str, Any]:
        """Get all module configurations."""
        return self._data.get("modules", self._default_data()["modules"])

    async def async_save_module(self, module_id: str, config: dict[str, Any]) -> None:
        """Save module configuration."""
        if "modules" not in self._data:
            self._data["modules"] = self._default_data()["modules"]
        self._data["modules"][module_id] = config
        await self.async_save()

    def get_available_entities(self, domain: str) -> list[dict[str, Any]]:
        """Get available entities for a domain (camera, lock, light, etc.)."""
        entities = []
        for state in self.hass.states.async_all(domain):
            entities.append({
                "entity_id": state.entity_id,
                "name": state.attributes.get("friendly_name", state.entity_id),
                "state": state.state,
            })
        return entities

    # ─── Notifications ───

    def get_notifications(self) -> dict[str, Any]:
        """Get all notification configurations."""
        return self._data.get("notifications", {})

    async def async_save_notification(self, notif_id: str, config: dict[str, Any]) -> None:
        """Save notification configuration."""
        if "notifications" not in self._data:
            self._data["notifications"] = {}
        self._data["notifications"][notif_id] = config
        await self.async_save()

    async def async_delete_notification(self, notif_id: str) -> bool:
        """Delete a notification."""
        if notif_id in self._data.get("notifications", {}):
            del self._data["notifications"][notif_id]
            await self.async_save()
            return True
        return False

    # ─── Automations ───

    def get_automations(self) -> dict[str, Any]:
        """Get all automation configurations."""
        return self._data.get("automations", {})

    async def async_save_automation(self, auto_id: str, config: dict[str, Any]) -> None:
        """Save automation configuration."""
        if "automations" not in self._data:
            self._data["automations"] = {}
        self._data["automations"][auto_id] = config
        await self.async_save()

    async def async_delete_automation(self, auto_id: str) -> bool:
        """Delete an automation."""
        if auto_id in self._data.get("automations", {}):
            del self._data["automations"][auto_id]
            await self.async_save()
            return True
        return False
