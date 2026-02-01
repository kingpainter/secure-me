"""Binary sensor platform for Secure Me."""
# VERSION = "0.0.1"

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secure Me binary sensors."""
    _LOGGER.info("Setting up Secure Me binary sensors")
    # Placeholder - will be implemented in Phase 1
    pass
