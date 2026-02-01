"""Alarm Control Panel platform for Secure Me."""
# VERSION = "0.0.1"

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CODE,
    DOMAIN,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_DISARMED,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secure Me alarm control panel."""
    _LOGGER.info("Setting up Secure Me alarm control panel")
    
    # Get configuration
    config = hass.data[DOMAIN][config_entry.entry_id]["config"]
    
    # Create alarm panel entity
    async_add_entities([SecureMeAlarmPanel(config_entry, config)])


class SecureMeAlarmPanel(AlarmControlPanelEntity):
    """Representation of a Secure Me alarm control panel."""

    _attr_has_entity_name = True
    _attr_name = "Alarm"
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS
        | AlarmControlPanelEntityFeature.TRIGGER
    )

    def __init__(self, config_entry: ConfigEntry, config: dict[str, Any]) -> None:
        """Initialize the alarm panel."""
        self._config_entry = config_entry
        self._config = config
        self._attr_unique_id = f"{config_entry.entry_id}_alarm"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Secure Me Alarm System",
            "manufacturer": "Secure Me",
            "model": "Alarm Manager",
            "sw_version": "0.0.1",
        }
        self._state = STATE_ALARM_DISARMED
        self._code = config.get(CONF_CODE)

    @property
    def state(self) -> str:
        """Return the state of the device."""
        return self._state

    @property
    def code_arm_required(self) -> bool:
        """Whether the code is required for arm actions."""
        return False  # Make optional for now

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        if code and code != self._config.get(CONF_CODE):
            _LOGGER.warning("Invalid code provided for disarm")
            return
        
        _LOGGER.info("Disarming alarm")
        self._state = STATE_ALARM_DISARMED
        self.async_write_ha_state()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        _LOGGER.info("Arming alarm (away mode)")
        self._state = STATE_ALARM_ARMED_AWAY
        self.async_write_ha_state()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        _LOGGER.info("Arming alarm (home mode)")
        self._state = STATE_ALARM_ARMED_HOME
        self.async_write_ha_state()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        _LOGGER.info("Arming alarm (night mode)")
        self._state = STATE_ALARM_ARMED_NIGHT
        self.async_write_ha_state()

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        """Send arm vacation command."""
        _LOGGER.info("Arming alarm (vacation mode)")
        self._state = STATE_ALARM_ARMED_VACATION
        self.async_write_ha_state()

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Send trigger command."""
        _LOGGER.warning("Alarm triggered!")
        # Will be implemented with full state machine
        self.async_write_ha_state()
