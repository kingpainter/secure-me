"""Select platform for Secure Me."""
# VERSION = "1.5.1"

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secure Me selects."""
    _LOGGER.info("Setting up Secure Me selects")
    # Placeholder - will be implemented in Phase 1
    pass
