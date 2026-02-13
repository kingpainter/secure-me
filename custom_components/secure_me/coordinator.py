"""DataUpdateCoordinator for Secure Me with state machine and zones."""
# VERSION = "0.3.0"

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    STATE_MACHINE_UPDATE_INTERVAL,
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMED_VACATION,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    CONF_CODE,
    CONF_EXIT_DELAY,
    CONF_ENTRY_DELAY,
    CONF_TRIGGER_TIME,
    DEFAULT_TRIGGER_TIME,
    MODULE_CAMERA,
    MODULE_LOCK,
    MODULE_LIGHTS,
    MODULE_CLIMATE,
    MODULE_SIREN,
    MODULE_TTS,
    EVENT_ALARM_ARMED,
    EVENT_ALARM_DISARMED,
    EVENT_ALARM_TRIGGERED,
    EVENT_MODULE_ENABLED,
    EVENT_MODULE_DISABLED,
    EVENT_MODULE_ERROR,
)
from .state_machine import AlarmStateMachine
from .zones import ZoneManager
from .module_manager import ModuleManager
from .modules import (
    CameraModule,
    ClimateModule,
    LightsModule,
    LockModule,
    SirenModule,
    TTSModule,
)

_LOGGER = logging.getLogger(__name__)


class SecureMeCoordinator(DataUpdateCoordinator):
    """Secure Me coordinator with state machine and zone management."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=STATE_MACHINE_UPDATE_INTERVAL),
        )
        
        self.config_entry = config_entry
        
        # Initialize modules dict early to avoid AttributeError in async_shutdown
        self.modules: dict[str, Any] = {}
        
        # Track who armed/disarmed (initialize early)
        self._armed_by: str | None = None
        self._disarmed_by: str | None = None
        self._triggered_by: str | None = None
        
        # Get config
        self._code = config_entry.data.get(CONF_CODE, "")
        exit_delay = config_entry.data.get(CONF_EXIT_DELAY, 30)
        entry_delay = config_entry.data.get(CONF_ENTRY_DELAY, 30)
        trigger_time = config_entry.data.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME)
        
        # Initialize state machine
        self.state_machine = AlarmStateMachine(
            hass,
            exit_delay=exit_delay,
            entry_delay=entry_delay,
            trigger_time=trigger_time,
        )
        
        # Initialize zone manager
        self.zone_manager = ZoneManager(hass)
        self.zone_manager.register_trigger_callback(self._zone_triggered)
        
        # Initialize modules
        self._init_modules()
        
        # Register callbacks
        self.state_machine.add_state_change_callback(self._state_changed)
        self.state_machine.add_countdown_callback(self._countdown_updated)
        
        _LOGGER.info(
            "Secure Me coordinator initialized (exit=%ds, entry=%ds)",
            exit_delay,
            entry_delay,
        )

    async def _state_changed(self, new_state: str, countdown: int) -> None:
        """Handle state machine state change."""
        _LOGGER.info("Coordinator received state change: %s (countdown=%d)", new_state, countdown)
        
        # Request refresh to update entities
        await self.async_request_refresh()
        
        # Fire events for state changes
        if new_state == STATE_ALARM_DISARMED:
            # Clear zone triggers when disarmed
            self.zone_manager.clear_all_triggers()
            self.hass.bus.async_fire(EVENT_ALARM_DISARMED, {
                "disarmed_by": self._disarmed_by,
            })
        
        elif new_state in [STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_HOME, 
                           STATE_ALARM_ARMED_NIGHT, STATE_ALARM_ARMED_VACATION]:
            # Start monitoring zones when armed
            if not self.zone_manager._unsubscribe_callbacks:
                self.zone_manager.start_monitoring()
            self.hass.bus.async_fire(EVENT_ALARM_ARMED, {
                "mode": new_state,
                "armed_by": self._armed_by,
            })
        
        elif new_state == STATE_ALARM_TRIGGERED:
            self.hass.bus.async_fire(EVENT_ALARM_TRIGGERED, {
                "triggered_by": self._triggered_by,
            })

    async def _countdown_updated(self, countdown: int) -> None:
        """Handle countdown update."""
        # Request refresh to update countdown in entities
        await self.async_request_refresh()

    async def _zone_triggered(self, zone) -> None:
        """Handle zone trigger."""
        if not self.state_machine.is_armed:
            return
        
        _LOGGER.warning(
            "Zone %s triggered (type=%s, sensors=%s)",
            zone.zone_id,
            zone.zone_type,
            zone.open_sensors,
        )
        
        # Trigger entry delay or immediate alarm based on zone type
        await self.state_machine.trigger_entry_delay(zone.zone_type)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            return {
                "state": self.state_machine.current_state,
                "countdown": self.state_machine.countdown,
                "armed_by": self._armed_by,
                "disarmed_by": self._disarmed_by,
                "triggered_by": self._triggered_by,
                "open_sensors": self.zone_manager.get_all_open_sensors(),
                "triggered_zones": len(self.zone_manager.get_triggered_zones()),
                "code_valid": bool(self._code),
                "is_armed": self.state_machine.is_armed,
                "is_arming": self.state_machine.is_arming,
                "is_pending": self.state_machine.is_pending,
            }
        except Exception as err:
            raise UpdateFailed(f"Error updating coordinator: {err}") from err

    @property
    def alarm_state(self) -> str:
        """Return current alarm state."""
        return self.state_machine.current_state

    @property
    def delay_countdown(self) -> int:
        """Return current delay countdown (seconds)."""
        return self.state_machine.countdown

    @property
    def exit_delay(self) -> int:
        """Return configured exit delay."""
        return self.state_machine.exit_delay

    @property
    def entry_delay(self) -> int:
        """Return configured entry delay."""
        return self.state_machine.entry_delay

    @property
    def code(self) -> str:
        """Return configured code."""
        return self._code

    @property
    def armed_by(self) -> str | None:
        """Return who armed the system."""
        return self._armed_by

    @property
    def disarmed_by(self) -> str | None:
        """Return who disarmed the system."""
        return self._disarmed_by

    @property
    def triggered_by(self) -> str | None:
        """Return what triggered the alarm."""
        return self._triggered_by

    @property
    def open_sensors(self) -> list[str]:
        """Return list of open sensors."""
        return self.zone_manager.get_all_open_sensors()

    @property
    def bypassed_zones(self) -> list[str]:
        """Return list of bypassed zones."""
        # TODO: Implement zone bypass in Phase 2
        return []

    def validate_code(self, code: str | None) -> bool:
        """Validate provided code."""
        if not self._code:
            # No code configured = always valid
            return True
        if not code:
            # Code required but not provided
            return False
        return code == self._code

    async def async_arm_away(self, code: str | None = None, skip_delay: bool = False) -> bool:
        """Arm the alarm in away mode."""
        _LOGGER.info("Arming alarm (away mode, skip_delay=%s)", skip_delay)
        
        # Check for open sensors before arming
        if self.zone_manager.check_for_open_sensors():
            open_sensors = self.zone_manager.get_all_open_sensors()
            _LOGGER.warning("Cannot arm - open sensors: %s", open_sensors)
            # TODO: Allow bypass in Phase 2
            return False
        
        success = await self.state_machine.arm_away(skip_delay)
        if success:
            self._armed_by = "user"
            # Execute modules for arm_away
            await self._execute_modules_arm_away()
        
        await self.async_request_refresh()
        return success

    async def async_arm_home(self, code: str | None = None, skip_delay: bool = False) -> bool:
        """Arm the alarm in home mode."""
        _LOGGER.info("Arming alarm (home mode, skip_delay=%s)", skip_delay)
        
        success = await self.state_machine.arm_home(skip_delay)
        if success:
            self._armed_by = "user"
            # Execute modules for arm_home
            await self._execute_modules_arm_home()
        
        await self.async_request_refresh()
        return success

    async def async_arm_night(self, code: str | None = None, skip_delay: bool = False) -> bool:
        """Arm the alarm in night mode."""
        _LOGGER.info("Arming alarm (night mode, skip_delay=%s)", skip_delay)
        
        success = await self.state_machine.arm_night(skip_delay)
        if success:
            self._armed_by = "user"
            # Execute modules for arm_night
            await self._execute_modules_arm_night()
        
        await self.async_request_refresh()
        return success

    async def async_arm_vacation(self, code: str | None = None, skip_delay: bool = False) -> bool:
        """Arm the alarm in vacation mode."""
        _LOGGER.info("Arming alarm (vacation mode, skip_delay=%s)", skip_delay)
        
        success = await self.state_machine.arm_vacation(skip_delay)
        if success:
            self._armed_by = "user"
            # Execute modules for vacation (same as away)
            await self._execute_modules_arm_away()
        
        await self.async_request_refresh()
        return success

    async def async_disarm(self, code: str | None = None) -> bool:
        """Disarm the alarm."""
        _LOGGER.info("Disarming alarm")
        
        # Validate code
        if not self.validate_code(code):
            _LOGGER.warning("Invalid code provided for disarm")
            return False
        
        # If pending, cancel pending (disarm during entry delay)
        if self.state_machine.is_pending:
            success = await self.state_machine.cancel_pending()
        else:
            success = await self.state_machine.disarm()
        
        if success:
            self._disarmed_by = "user"
            # Stop monitoring zones
            self.zone_manager.stop_monitoring()
            # Execute modules for disarm
            await self._execute_modules_disarm()
        
        await self.async_request_refresh()
        return success

    async def async_trigger(self, source: str | None = None) -> bool:
        """Trigger the alarm."""
        _LOGGER.warning("Alarm triggered! Source: %s", source or "manual")
        
        self._triggered_by = source or "manual"
        success = await self.state_machine.trigger_alarm(self._triggered_by)
        
        if success:
            # Execute modules for trigger
            await self._execute_modules_trigger()
        
        await self.async_request_refresh()
        return success

    def update_config(self, config_data: dict[str, Any]) -> None:
        """Update configuration."""
        _LOGGER.info("Updating coordinator configuration")
        
        self._code = config_data.get(CONF_CODE, self._code)
        exit_delay = config_data.get(CONF_EXIT_DELAY, self.state_machine.exit_delay)
        entry_delay = config_data.get(CONF_ENTRY_DELAY, self.state_machine.entry_delay)
        trigger_time = config_data.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME)
        
        self.state_machine.update_config(exit_delay, entry_delay, trigger_time)
        
        _LOGGER.info(
            "Configuration updated (exit=%ds, entry=%ds)",
            exit_delay,
            entry_delay,
        )

    def _init_modules(self) -> None:
        """Initialize all available modules."""
        _LOGGER.info("Initializing modules")
        
        # Get module config from options (if any)
        module_config = self.config_entry.options.get("modules", {})
        
        # Camera module
        self.modules[MODULE_CAMERA] = CameraModule(
            self.hass,
            module_config.get(MODULE_CAMERA, {})
        )
        
        # Lock module
        self.modules[MODULE_LOCK] = LockModule(
            self.hass,
            module_config.get(MODULE_LOCK, {})
        )
        
        # Lights module
        self.modules[MODULE_LIGHTS] = LightsModule(
            self.hass,
            module_config.get(MODULE_LIGHTS, {})
        )
        
        # Climate module
        self.modules[MODULE_CLIMATE] = ClimateModule(
            self.hass,
            module_config.get(MODULE_CLIMATE, {})
        )
        
        # Siren module
        self.modules[MODULE_SIREN] = SirenModule(
            self.hass,
            module_config.get(MODULE_SIREN, {})
        )
        
        # TTS module
        self.modules[MODULE_TTS] = TTSModule(
            self.hass,
            module_config.get(MODULE_TTS, {})
        )
        
        _LOGGER.info("Modules initialized: %s", list(self.modules.keys()))

    async def _execute_modules_arm_away(self) -> None:
        """Execute all modules on arm away."""
        _LOGGER.info("Executing modules for arm_away")
        
        for module_id, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm_away()
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_away: %s", module_id, err)
                    self.hass.bus.async_fire(EVENT_MODULE_ERROR, {
                        "module": module_id, "action": "arm_away", "error": str(err),
                    })

    async def _execute_modules_arm_home(self) -> None:
        """Execute all modules on arm home."""
        _LOGGER.info("Executing modules for arm_home")
        
        for module_id, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm_home()
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_home: %s", module_id, err)
                    self.hass.bus.async_fire(EVENT_MODULE_ERROR, {
                        "module": module_id, "action": "arm_home", "error": str(err),
                    })

    async def _execute_modules_arm_night(self) -> None:
        """Execute all modules on arm night."""
        _LOGGER.info("Executing modules for arm_night")
        
        for module_id, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm_night()
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_night: %s", module_id, err)
                    self.hass.bus.async_fire(EVENT_MODULE_ERROR, {
                        "module": module_id, "action": "arm_night", "error": str(err),
                    })

    async def _execute_modules_disarm(self) -> None:
        """Execute all modules on disarm."""
        _LOGGER.info("Executing modules for disarm")
        
        for module_id, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_disarm()
                except Exception as err:
                    _LOGGER.error("Module %s failed on disarm: %s", module_id, err)
                    self.hass.bus.async_fire(EVENT_MODULE_ERROR, {
                        "module": module_id, "action": "disarm", "error": str(err),
                    })

    async def _execute_modules_trigger(self) -> None:
        """Execute all modules on trigger."""
        _LOGGER.warning("Executing modules for TRIGGER")
        
        for module_id, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_trigger()
                except Exception as err:
                    _LOGGER.error("Module %s failed on trigger: %s", module_id, err)
                    self.hass.bus.async_fire(EVENT_MODULE_ERROR, {
                        "module": module_id, "action": "trigger", "error": str(err),
                    })

    def enable_module(self, module_id: str) -> bool:
        """Enable a module."""
        if module_id not in self.modules:
            _LOGGER.error("Module %s not found", module_id)
            return False
        
        self.modules[module_id].enable()
        _LOGGER.info("Module %s enabled", module_id)
        self.hass.bus.async_fire(EVENT_MODULE_ENABLED, {"module": module_id})
        return True

    def disable_module(self, module_id: str) -> bool:
        """Disable a module."""
        if module_id not in self.modules:
            _LOGGER.error("Module %s not found", module_id)
            return False
        
        self.modules[module_id].disable()
        _LOGGER.info("Module %s disabled", module_id)
        self.hass.bus.async_fire(EVENT_MODULE_DISABLED, {"module": module_id})
        return True

    # ─── Health Methods ───

    def get_health_score(self) -> int:
        """Calculate system health score (0-100).

        Based on entity availability across all enabled modules.
        Returns 100 if no entities are configured.
        """
        total = 0
        available = 0

        for module in self.modules.values():
            if not module.enabled:
                continue
            entities = self._get_module_entity_ids(module)
            for eid in entities:
                total += 1
                state = self.hass.states.get(eid)
                if state and state.state not in ("unavailable", "unknown"):
                    available += 1

        if total == 0:
            return 100
        return round((available / total) * 100)

    def get_module_health(self) -> dict[str, dict]:
        """Get health status for each module.

        Returns dict mapping module_id to health info:
            enabled, status ('ok'/'problem'/'disabled'),
            total entities, available count, unavailable list.
        """
        result = {}
        for mod_id, module in self.modules.items():
            if not module.enabled:
                result[mod_id] = {
                    "enabled": False,
                    "status": "disabled",
                    "total": 0,
                    "available": 0,
                    "unavailable": [],
                }
                continue

            entities = self._get_module_entity_ids(module)
            unavail = []
            for eid in entities:
                state = self.hass.states.get(eid)
                if not state or state.state in ("unavailable", "unknown"):
                    unavail.append(eid)

            result[mod_id] = {
                "enabled": True,
                "status": "problem" if unavail else "ok",
                "total": len(entities),
                "available": len(entities) - len(unavail),
                "unavailable": unavail,
            }
        return result

    def get_enabled_module_count(self) -> int:
        """Return count of enabled modules."""
        return sum(1 for m in self.modules.values() if m.enabled)

    @staticmethod
    def _get_module_entity_ids(module) -> list[str]:
        """Extract all entity IDs from a module's configuration."""
        entities: list[str] = []
        # List attributes
        for attr in ("poe_switches", "cameras", "recording_entities",
                     "locks", "lights", "climates", "media_players"):
            val = getattr(module, attr, None)
            if isinstance(val, list):
                entities.extend(val)
        # Dict attributes (maps lock -> sensor, etc.)
        for attr in ("door_sensors", "battery_sensors"):
            val = getattr(module, attr, None)
            if isinstance(val, dict):
                entities.extend(val.values())
        # Single entity attributes
        for attr in ("gateway_light",):
            val = getattr(module, attr, None)
            if isinstance(val, str) and "." in val:
                entities.append(val)
        return entities

    async def async_shutdown(self) -> None:
        """Shutdown coordinator."""
        _LOGGER.info("Shutting down coordinator")
        
        # Cleanup modules (if initialized)
        if hasattr(self, 'modules'):
            for module_id, module in self.modules.items():
                try:
                    await module.async_cleanup()
                except Exception as err:
                    _LOGGER.error("Module %s cleanup failed: %s", module_id, err)
        
        # Stop zone monitoring (if initialized)
        if hasattr(self, 'zone_manager'):
            try:
                self.zone_manager.stop_monitoring()
            except Exception as err:
                _LOGGER.error("Zone manager cleanup failed: %s", err)
        
        # Cleanup state machine (if initialized)
        if hasattr(self, 'state_machine'):
            try:
                self.state_machine.cleanup()
            except Exception as err:
                _LOGGER.error("State machine cleanup failed: %s", err)
