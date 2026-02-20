"""Alarm Control Panel platform for Secure Me."""
# VERSION = "0.3.3"

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COORDINATOR,
    DOMAIN,
    STATE_ALARM_ARMING,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    ATTR_CHANGED_BY,
    ATTR_CODE_ARM_REQUIRED,
)
from .coordinator import SecureMeCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Secure Me alarm control panel."""
    _LOGGER.info("Setting up Secure Me alarm control panel")
    
    # Get coordinator
    coordinator: SecureMeCoordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    
    # Create alarm panel entity
    async_add_entities([SecureMeAlarmPanel(coordinator, config_entry)])


class SecureMeAlarmPanel(CoordinatorEntity[SecureMeCoordinator], AlarmControlPanelEntity):
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

    def __init__(
        self,
        coordinator: SecureMeCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the alarm panel."""
        super().__init__(coordinator)
        
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_alarm"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Secure Me Alarm System",
            "manufacturer": "Secure Me",
            "model": "Alarm Manager",
            "sw_version": "0.2.0",
        }

    @property
    def state(self) -> str:
        """Return the state of the device."""
        return self.coordinator.alarm_state

    @property
    def code_arm_required(self) -> bool:
        """Whether the code is required for arm actions."""
        # For now, code is optional for arming
        # Will be configurable in Phase 2
        return False

    @property
    def code_format(self) -> str | None:
        """Return the regex for code format."""
        # Code must be 4-6 digits
        return r"^\d{4,6}$"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs = {
            ATTR_CHANGED_BY: self.coordinator.armed_by or self.coordinator.disarmed_by,
            ATTR_CODE_ARM_REQUIRED: self.code_arm_required,
        }
        
        # Add countdown if in arming/pending state
        if self.coordinator.alarm_state in [STATE_ALARM_ARMING, STATE_ALARM_PENDING]:
            attrs["delay_countdown"] = self.coordinator.delay_countdown
        
        # Add triggered_by if triggered
        if self.coordinator.alarm_state == STATE_ALARM_TRIGGERED:
            attrs["triggered_by"] = self.coordinator.triggered_by
        
        # Add open sensors if any
        if self.coordinator.open_sensors:
            attrs["open_sensors"] = self.coordinator.open_sensors
        
        return attrs

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        _LOGGER.info("Alarm panel: Disarm requested")
        
        success = await self.coordinator.async_disarm(code)
        if success:
            _LOGGER.info("Alarm successfully disarmed")
        else:
            _LOGGER.warning("Alarm disarm failed (invalid code)")

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        _LOGGER.info("Alarm panel: Arm away requested")
        await self.coordinator.async_arm_away(code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        _LOGGER.info("Alarm panel: Arm home requested")
        await self.coordinator.async_arm_home(code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        _LOGGER.info("Alarm panel: Arm night requested")
        await self.coordinator.async_arm_night(code)

    async def async_alarm_arm_custom_bypass(self, code: str | None = None) -> None:
        """Send arm vacation command."""
        _LOGGER.info("Alarm panel: Arm vacation requested")
        await self.coordinator.async_arm_vacation(code)

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Send trigger command."""
        _LOGGER.warning("Alarm panel: Trigger requested")
        await self.coordinator.async_trigger("manual")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
