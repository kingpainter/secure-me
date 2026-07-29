"""Alarm Control Panel platform for Secure Me."""
# VERSION = "1.5.3"

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COORDINATOR,
    DOMAIN,
    STATE_ALARM_ARMING,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    ATTR_CHANGED_BY,
    ATTR_CODE_ARM_REQUIRED,
    ATTR_BYPASSED_SENSORS,
    ATTR_LAST_TRIGGERED,
    EVENT_ALARM_INVALID_CODE,
    VERSION,
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


class SecureMeAlarmPanel(CoordinatorEntity[SecureMeCoordinator], RestoreEntity, AlarmControlPanelEntity):
    """Representation of a Secure Me alarm control panel."""

    _attr_has_entity_name = True
    _attr_name = "Alarm"
    # v1.4.3: ARM_VACATION is now a first-class HA feature (HA Core 2024.11+).
    # Previously we shoehorned vacation into ARM_CUSTOM_BYPASS which made the
    # standard HA alarm dialog label the button "Custom" instead of "Vacation".
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.ARM_VACATION
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
            "sw_version": VERSION,
        }

    @property
    def alarm_state(self):
        """Return the current alarm state.

        REVERT: 'armed_home_alone' previously mapped to HA's
        ARMED_CUSTOM_BYPASS enum member, since AlarmControlPanelState has
        no dedicated slot for it. That broke secure_me_alarm_tab_card.js
        (lost ability to distinguish Home Alone from a real bypass) and
        risked colliding with anything else using that same slot.

        We now report the raw string 'armed_home_alone' directly instead.
        This is NOT a member of HA's AlarmControlPanelState enum (HA Core
        2024.11+ only recognises the fixed enum values), so:
          - Secure Me's own frontend cards (secure-me-panel.js,
            secure-me-alarm-card.js, secure_me_alarm_tab_card.js) work
            correctly -- they read the raw entity state (or the
            'secure_me_mode' attribute) directly and already have an
            explicit 'armed_home_alone' branch.
          - HA's built-in default alarm-control-panel card, and any
            voice assistant exposure (Google Home / Alexa), would show
            this as "Unknown" since it's not a recognised enum value.
            Accepted trade-off: Secure Me is only ever driven through its
            own cards.

        The other five modes (disarmed/away/home/night/vacation) are
        untouched and continue to use HA's native enum values.
        """
        from homeassistant.components.alarm_control_panel import AlarmControlPanelState
        state = self.coordinator.alarm_state

        # Home Alone: raw custom string, not part of HA's enum (see above).
        if state == "armed_home_alone":
            return "armed_home_alone"

        _MAP = {
            "disarmed":       AlarmControlPanelState.DISARMED,
            "arming":         AlarmControlPanelState.ARMING,
            "armed_away":     AlarmControlPanelState.ARMED_AWAY,
            "armed_home":     AlarmControlPanelState.ARMED_HOME,
            "armed_night":    AlarmControlPanelState.ARMED_NIGHT,
            "armed_vacation": AlarmControlPanelState.ARMED_VACATION,
            "pending":        AlarmControlPanelState.PENDING,
            "triggered":      AlarmControlPanelState.TRIGGERED,
        }
        return _MAP.get(state, AlarmControlPanelState.DISARMED)

    @property
    def code_arm_required(self) -> bool:
        """Whether the code is required for arm actions.

        Secure Me handles code validation internally via bcrypt.
        We set this to True so HA passes the code through to our
        async_alarm_arm_* methods instead of ignoring it.
        """
        return True

    @property
    def code_format(self) -> CodeFormat | None:
        """Return the format of the code.

        Returning NUMBER makes HA's standard alarm dialog show a numeric
        PIN entry field. Secure Me still validates the actual PIN value
        internally via authenticate_user() + bcrypt — HA only checks that
        the input matches the format (digits only).
        """
        return CodeFormat.NUMBER

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        attrs: dict[str, Any] = {
            ATTR_CHANGED_BY: self.coordinator.armed_by or self.coordinator.disarmed_by,
            ATTR_CODE_ARM_REQUIRED: self.code_arm_required,
        }

        # Add countdown during arming/pending -- key must be 'countdown' to match
        # what the alarm card reads via this._attr("countdown").
        if self.coordinator.alarm_state in [STATE_ALARM_ARMING, STATE_ALARM_PENDING]:
            attrs["countdown"] = self.coordinator.delay_countdown

        # v1.5.0: expose which mode is being armed into during the exit-delay
        # countdown, so the card can show "Tilkobler <mode>..." instead of a
        # bare countdown number.
        if self.coordinator.alarm_state == STATE_ALARM_ARMING:
            attrs["target_mode"] = self.coordinator.target_mode

        # Add triggered_by if triggered
        if self.coordinator.alarm_state == STATE_ALARM_TRIGGERED:
            attrs["triggered_by"] = self.coordinator.triggered_by

        # Add open sensors if any
        if self.coordinator.open_sensors:
            attrs["open_sensors"] = self.coordinator.open_sensors

        # v1.4.3: Bypassed sensors at last arm operation (Alarmo-inspired).
        # Visible to users / automations so they know which sensors were
        # auto-bypassed (auto_bypass=True) or force-bypassed via FORCE_ARM.
        bypassed = getattr(self.coordinator, "bypassed_sensors", None)
        if bypassed:
            attrs[ATTR_BYPASSED_SENSORS] = bypassed

        # v1.4.3: Timestamp of last trigger event (Alarmo-inspired).
        # Persists across HA restarts via RestoreEntity.
        last_triggered = getattr(self.coordinator, "last_triggered", None)
        if last_triggered:
            attrs[ATTR_LAST_TRIGGERED] = last_triggered

        # Expose the raw Secure Me coordinator state as an attribute too.
        # This is now identical to the entity's own state for every mode
        # (armed_home_alone is reported raw, see alarm_state above), but we
        # keep it for older frontend code that still reads secure_me_mode
        # explicitly, and as a stable contract independent of any future HA
        # enum changes.
        attrs["secure_me_mode"] = self.coordinator.alarm_state

        return attrs

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command.

        v1.4.3: Validate code in this layer (consistent with arm methods)
        so we get unified rejection logging and can fire the
        EVENT_ALARM_INVALID_CODE event for HA automations to react to.
        Coordinator also re-validates as defense in depth.
        """
        _LOGGER.info("Alarm panel: Disarm requested")
        if not self.coordinator.validate_code(code):
            _LOGGER.warning("Alarm panel: Disarm rejected -- invalid code")
            self.hass.bus.async_fire(EVENT_ALARM_INVALID_CODE, {
                "command": "disarm",
                "entity_id": self.entity_id,
            })
            return
        success = await self.coordinator.async_disarm(code)
        if success:
            _LOGGER.info("Alarm successfully disarmed")
        else:
            _LOGGER.warning("Alarm disarm failed")

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        _LOGGER.info("Alarm panel: Arm away requested")
        if not self.coordinator.validate_code(code):
            _LOGGER.warning("Alarm panel: Arm away rejected -- invalid code")
            self.hass.bus.async_fire(EVENT_ALARM_INVALID_CODE, {
                "command": "arm_away",
                "entity_id": self.entity_id,
            })
            return
        await self.coordinator.async_arm_away(code)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        _LOGGER.info("Alarm panel: Arm home requested")
        if not self.coordinator.validate_code(code):
            _LOGGER.warning("Alarm panel: Arm home rejected -- invalid code")
            self.hass.bus.async_fire(EVENT_ALARM_INVALID_CODE, {
                "command": "arm_home",
                "entity_id": self.entity_id,
            })
            return
        await self.coordinator.async_arm_home(code)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        _LOGGER.info("Alarm panel: Arm night requested")
        if not self.coordinator.validate_code(code):
            _LOGGER.warning("Alarm panel: Arm night rejected -- invalid code")
            self.hass.bus.async_fire(EVENT_ALARM_INVALID_CODE, {
                "command": "arm_night",
                "entity_id": self.entity_id,
            })
            return
        await self.coordinator.async_arm_night(code)

    async def async_alarm_arm_vacation(self, code: str | None = None) -> None:
        """Send arm vacation command.

        v1.4.3: First-class ARM_VACATION feature (HA Core 2024.11+).
        Previously this was async_alarm_arm_custom_bypass.
        """
        _LOGGER.info("Alarm panel: Arm vacation requested")
        if not self.coordinator.validate_code(code):
            _LOGGER.warning("Alarm panel: Arm vacation rejected -- invalid code")
            self.hass.bus.async_fire(EVENT_ALARM_INVALID_CODE, {
                "command": "arm_vacation",
                "entity_id": self.entity_id,
            })
            return
        await self.coordinator.async_arm_vacation(code)

    async def async_alarm_arm_home_alone(self, code: str | None = None) -> None:
        """Send arm home alone command."""
        _LOGGER.info("Alarm panel: Arm home alone requested")
        if not self.coordinator.validate_code(code):
            _LOGGER.warning("Alarm panel: Arm home alone rejected -- invalid code")
            self.hass.bus.async_fire(EVENT_ALARM_INVALID_CODE, {
                "command": "arm_home_alone",
                "entity_id": self.entity_id,
            })
            return
        await self.coordinator.async_arm_home_alone(code)

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Send trigger command."""
        _LOGGER.warning("Alarm panel: Trigger requested")
        await self.coordinator.async_trigger("manual")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore last known alarm state after HA restart.

        Called by HA after the entity is added. We read the last persisted
        state from HA's entity registry and feed it back into the coordinator
        so the alarm stays armed across restarts.

        Transient states (arming, pending, triggered) are intentionally
        ignored and left as disarmed — the coordinator will log a warning.

        v1.4.3: Also restores last_triggered timestamp and bypassed_sensors
        list so the alarm panel attributes survive HA restart.

        Prefer the 'secure_me_mode' extra_state_attribute over last.state as
        the authoritative source for the restored state. The raw entity
        state for armed_home_alone now already matches secure_me_mode (no
        more armed_custom_bypass indirection), but secure_me_mode is still
        preferred here as a safety net for entities last persisted by an
        older Secure Me build where the raw state was 'armed_custom_bypass'.
        coordinator.async_restore_state() still reverse-maps that legacy
        value for the same reason.
        """
        await super().async_added_to_hass()

        last = await self.async_get_last_state()
        if last is None:
            _LOGGER.debug("No previous state found — starting as disarmed")
            return

        # Prefer 'secure_me_mode' attribute (the true Secure Me state string)
        # over last.state (the HA-canonical AlarmControlPanelState string).
        # Fallback to last.state if the attribute is missing (upgrade path from
        # older Secure Me versions that did not set this attribute).
        secure_me_mode = last.attributes.get("secure_me_mode")
        restored_state = secure_me_mode if secure_me_mode else last.state

        armed_by = last.attributes.get(ATTR_CHANGED_BY)
        last_triggered = last.attributes.get(ATTR_LAST_TRIGGERED)
        bypassed_sensors = last.attributes.get(ATTR_BYPASSED_SENSORS)

        _LOGGER.info(
            "Restoring alarm state: '%s' (source=%s, armed_by=%s, "
            "last_triggered=%s, bypassed=%d)",
            restored_state,
            "secure_me_mode attr" if secure_me_mode else "last.state fallback",
            armed_by, last_triggered,
            len(bypassed_sensors) if bypassed_sensors else 0,
        )
        await self.coordinator.async_restore_state(
            restored_state,
            armed_by,
            last_triggered=last_triggered,
            bypassed_sensors=bypassed_sensors,
        )
