"""DataUpdateCoordinator for Secure Me with state machine and zones."""
# VERSION = "1.2.0"

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
    CONF_FAKE_PRESENCE,
    NOTIFY_ID_FAKE_PRESENCE,
    FAKE_PRESENCE_ON_EN,
    FAKE_PRESENCE_OFF_EN,
    EVENT_FAKE_PRESENCE_CHANGED,
    # v1.2.0: push notification action constants
    PUSH_EVENT,
    PUSH_EVENT_ACTIONS,
    EVENT_ACTION_FORCE_ARM,
    EVENT_ACTION_RETRY_ARM,
    EVENT_ACTION_DISARM,
    EVENT_ACTION_ARM_AWAY,
    EVENT_ACTION_ARM_HOME,
    EVENT_ACTION_ARM_NIGHT,
    EVENT_ACTION_ARM_VACATION,
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


def _normalize_coordinator_config(module_id: str, config: dict) -> dict:
    """Normalize panel-saved config (objects) to module class format (flat strings)."""
    normalized = dict(config)

    def extract_ids(items) -> list[str]:
        if not isinstance(items, list):
            return []
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict) and item.get("entity_id"):
                result.append(item["entity_id"])
        return [e for e in result if e and "." in e]

    if module_id == "camera":
        raw = config.get("cameras", [])
        normalized["cameras"] = extract_ids(raw)
        poe = [
            c["poe_port"] for c in raw
            if isinstance(c, dict) and c.get("poe_port") and "." in str(c["poe_port"])
        ]
        if poe:
            normalized["poe_switches"] = poe
    elif module_id == "lock":
        normalized["locks"] = extract_ids(config.get("locks", []))
    elif module_id == "climate":
        normalized["climates"] = extract_ids(config.get("thermostats", []))
    elif module_id == "lights":
        normalized["lights"] = extract_ids(config.get("lights", []))
    elif module_id == "tts":
        normalized["media_players"] = extract_ids(config.get("entities", []))
        normalized["tts_service"] = config.get("tts_service", "tts.cloud_say")
        normalized["language"] = config.get("language", "da")
        normalized["volume"] = config.get("volume", 0.5)
        normalized["custom_messages"] = config.get("custom_messages", [])
    elif module_id == "siren":
        normalized["lights"] = extract_ids(config.get("lights", []))

    return normalized


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
        self.modules: dict[str, Any] = {}
        self._armed_by: str | None = None
        self._disarmed_by: str | None = None
        self._triggered_by: str | None = None
        self._last_arm_mode: str | None = None  # v1.2.0: remembered for push force-arm

        self._code = config_entry.data.get(CONF_CODE, "")
        exit_delay = config_entry.data.get(CONF_EXIT_DELAY, 30)
        entry_delay = config_entry.data.get(CONF_ENTRY_DELAY, 30)
        trigger_time = config_entry.data.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME)

        self.state_machine = AlarmStateMachine(
            hass,
            exit_delay=exit_delay,
            entry_delay=entry_delay,
            trigger_time=trigger_time,
        )

        self.zone_manager = ZoneManager(hass)
        self.zone_manager.register_trigger_callback(self._zone_triggered)
        self.zone_manager.register_arm_on_close_callback(self._arm_on_close_triggered)

        self._init_modules()

        self.state_machine.add_state_change_callback(self._state_changed)
        self.state_machine.add_countdown_callback(self._countdown_updated)

        # v1.2.0: Register push notification listener
        self._push_unsub = hass.bus.async_listen(
            PUSH_EVENT, self._handle_push_event
        )

        _LOGGER.info(
            "Secure Me coordinator initialized (exit=%ds, entry=%ds)",
            exit_delay, entry_delay,
        )

        self._last_health_event_time: float = 0.0
        self._health_event_interval: float = 5.0
        self._last_countdown: int = -1

    # ── Push notification handler (v1.2.0) ──────────────────────────────────

    @callback
    def _handle_push_event(self, event) -> None:
        """Handle mobile push notification action buttons.

        Allows arm/disarm from HA Companion push notifications without opening the app.
        Action strings match the PUSH_EVENT_ACTIONS constants.
        """
        if not event.data:
            return

        action = (
            event.data.get("actionName")
            if "actionName" in event.data
            else event.data.get("action")
        )

        if action not in PUSH_EVENT_ACTIONS:
            return

        _LOGGER.info("Received push action: %s", action)
        import asyncio
        loop = asyncio.get_event_loop()

        if action == EVENT_ACTION_DISARM:
            loop.create_task(self.async_disarm())

        elif action == EVENT_ACTION_FORCE_ARM:
            # Force-arm in last used mode (or away if unknown)
            mode = self._last_arm_mode or STATE_ALARM_ARMED_AWAY
            loop.create_task(self._arm_by_state(mode, skip_delay=True, force=True))

        elif action == EVENT_ACTION_RETRY_ARM:
            mode = self._last_arm_mode or STATE_ALARM_ARMED_AWAY
            loop.create_task(self._arm_by_state(mode))

        elif action == EVENT_ACTION_ARM_AWAY:
            loop.create_task(self.async_arm_away())

        elif action == EVENT_ACTION_ARM_HOME:
            loop.create_task(self.async_arm_home())

        elif action == EVENT_ACTION_ARM_NIGHT:
            loop.create_task(self.async_arm_night())

        elif action == EVENT_ACTION_ARM_VACATION:
            loop.create_task(self.async_arm_vacation())

    async def _arm_by_state(
        self, state: str, skip_delay: bool = False, force: bool = False
    ) -> bool:
        """Arm in the mode corresponding to an alarm state string."""
        if state == STATE_ALARM_ARMED_AWAY:
            return await self.async_arm_away(skip_delay=skip_delay, force=force)
        if state == STATE_ALARM_ARMED_HOME:
            return await self.async_arm_home(skip_delay=skip_delay)
        if state == STATE_ALARM_ARMED_NIGHT:
            return await self.async_arm_night(skip_delay=skip_delay)
        if state == STATE_ALARM_ARMED_VACATION:
            return await self.async_arm_vacation(skip_delay=skip_delay)
        return False

    # ── arm_on_close callback (v1.2.0) ──────────────────────────────────────

    async def _arm_on_close_triggered(self, entity_id: str) -> None:
        """Auto-arm when an arm_on_close sensor closes (e.g. front door shut)."""
        if self.state_machine.is_armed or self.state_machine.is_arming:
            return
        _LOGGER.info(
            "arm_on_close: sensor %s closed — automatically arming (away)", entity_id
        )
        await self.async_arm_away(auto=True)

    # ── State / countdown callbacks ──────────────────────────────────────────

    async def _state_changed(self, new_state: str, countdown: int) -> None:
        """Handle state machine state change."""
        _LOGGER.info(
            "Coordinator received state change: %s (countdown=%d)", new_state, countdown
        )
        await self.async_request_refresh()

        if new_state == STATE_ALARM_DISARMED:
            self.zone_manager.clear_all_triggers()
            self.hass.bus.async_fire(
                EVENT_ALARM_DISARMED, {"disarmed_by": self._disarmed_by}
            )

        elif new_state in (
            STATE_ALARM_ARMED_AWAY,
            STATE_ALARM_ARMED_HOME,
            STATE_ALARM_ARMED_NIGHT,
            STATE_ALARM_ARMED_VACATION,
        ):
            self._last_arm_mode = new_state
            if len(self.zone_manager._unsubscribe_callbacks) == 0:
                self.zone_manager.start_monitoring()
            self.hass.bus.async_fire(
                EVENT_ALARM_ARMED, {"mode": new_state, "armed_by": self._armed_by}
            )

        elif new_state == STATE_ALARM_TRIGGERED:
            self.hass.bus.async_fire(
                EVENT_ALARM_TRIGGERED, {"triggered_by": self._triggered_by}
            )

    async def _countdown_updated(self, countdown: int) -> None:
        """Handle countdown tick — lightweight update."""
        self._last_countdown = countdown
        if self.data:
            self.data["countdown"] = countdown
        self.async_update_listeners()
        if countdown == 0 or countdown % 5 == 0:
            await self.async_request_refresh()

    async def _zone_triggered(self, zone) -> None:
        """Handle zone trigger."""
        current = self.state_machine.current_state

        if current == STATE_ALARM_ARMING:
            _LOGGER.warning(
                "Zone %s triggered during exit delay — ignoring", zone.zone_id
            )
            return

        if not self.state_machine.is_armed:
            return

        _LOGGER.warning(
            "Zone %s triggered (type=%s, sensors=%s)",
            zone.zone_id, zone.zone_type, zone.open_sensors,
        )
        await self.state_machine.trigger_entry_delay(zone.zone_type)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            data = {
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
                "fake_presence": self.fake_presence,
            }
            now = time.monotonic()
            if now - self._last_health_event_time >= self._health_event_interval:
                self._last_health_event_time = now
                self.hass.bus.async_fire(
                    f"{DOMAIN}_health_updated",
                    {
                        "modules": self.get_module_health(),
                        "health_score": self.get_health_score(),
                    },
                )
            return data
        except Exception as err:
            raise UpdateFailed(f"Error updating coordinator: {err}") from err

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def alarm_state(self) -> str:
        return self.state_machine.current_state

    @property
    def delay_countdown(self) -> int:
        return self.state_machine.countdown

    @property
    def exit_delay(self) -> int:
        return self.state_machine.exit_delay

    @property
    def entry_delay(self) -> int:
        return self.state_machine.entry_delay

    @property
    def code(self) -> str:
        return self._code

    @property
    def armed_by(self) -> str | None:
        return self._armed_by

    @property
    def disarmed_by(self) -> str | None:
        return self._disarmed_by

    @property
    def triggered_by(self) -> str | None:
        return self._triggered_by

    @property
    def open_sensors(self) -> list[str]:
        return self.zone_manager.get_all_open_sensors()

    @property
    def bypassed_zones(self) -> list[str]:
        return []

    @property
    def fake_presence(self) -> bool:
        if hasattr(self, "store") and self.store:
            return self.store.get_fake_presence()
        return False

    # ── Code validation ──────────────────────────────────────────────────────

    def validate_code(self, code: str | None) -> bool:
        """Validate code. Uses bcrypt if store has hashed codes."""
        if not self._code:
            return True
        if not code:
            return False
        # If store is available, use bcrypt authenticate_user
        if hasattr(self, "store") and self.store:
            result = self.store.authenticate_user(code)
            return result is not None
        # Fallback: plaintext comparison (pre-store state)
        return code == self._code

    # ── Arm / Disarm / Trigger ───────────────────────────────────────────────

    async def async_arm_away(
        self,
        code: str | None = None,
        skip_delay: bool = False,
        auto: bool = False,
        force: bool = False,
    ) -> bool:
        """Arm in away mode.

        force=True skips the open-sensor check (used by push FORCE_ARM).
        auto=True respects fake_presence block.
        """
        _LOGGER.info(
            "Arming alarm (away, skip_delay=%s, auto=%s, force=%s)",
            skip_delay, auto, force,
        )
        if auto and self.fake_presence:
            _LOGGER.info("Auto arm blocked — Fake Presence active")
            return False

        if not force:
            all_sensors = [s for z in self.zone_manager.zones.values() for s in z.sensors]
            bypassed = self.zone_manager.get_auto_bypass_sensors(all_sensors)
            if self.zone_manager.check_for_open_sensors(bypass_list=bypassed):
                _LOGGER.warning(
                    "Cannot arm — open sensors: %s", self.zone_manager.get_all_open_sensors()
                )
                return False

        success = await self.state_machine.arm_away(skip_delay)
        if success:
            self._armed_by = "user"
            await self._execute_modules_arm_away()
        await self.async_request_refresh()
        return success

    async def async_arm_home(
        self, code: str | None = None, skip_delay: bool = False
    ) -> bool:
        """Arm in home mode."""
        _LOGGER.info("Arming alarm (home, skip_delay=%s)", skip_delay)
        success = await self.state_machine.arm_home(skip_delay)
        if success:
            self._armed_by = "user"
            await self._execute_modules_arm_home()
        await self.async_request_refresh()
        return success

    async def async_arm_night(
        self, code: str | None = None, skip_delay: bool = False
    ) -> bool:
        """Arm in night mode."""
        _LOGGER.info("Arming alarm (night, skip_delay=%s)", skip_delay)
        success = await self.state_machine.arm_night(skip_delay)
        if success:
            self._armed_by = "user"
            await self._execute_modules_arm_night()
        await self.async_request_refresh()
        return success

    async def async_arm_vacation(
        self, code: str | None = None, skip_delay: bool = False
    ) -> bool:
        """Arm in vacation mode."""
        _LOGGER.info("Arming alarm (vacation, skip_delay=%s)", skip_delay)
        success = await self.state_machine.arm_vacation(skip_delay)
        if success:
            self._armed_by = "user"
            await self._execute_modules_arm_away()
        await self.async_request_refresh()
        return success

    async def async_disarm(self, code: str | None = None) -> bool:
        """Disarm the alarm."""
        _LOGGER.info("Disarming alarm")
        if not self.validate_code(code):
            _LOGGER.warning("Invalid code provided for disarm")
            return False

        if self.state_machine.is_pending:
            success = await self.state_machine.cancel_pending()
        else:
            success = await self.state_machine.disarm()

        if success:
            self._disarmed_by = "user"
            self.zone_manager.stop_monitoring()
            await self._execute_modules_disarm()
        await self.async_request_refresh()
        return success

    async def async_trigger(self, source: str | None = None) -> bool:
        """Trigger the alarm."""
        _LOGGER.warning("Alarm triggered! Source: %s", source or "manual")
        self._triggered_by = source or "manual"
        success = await self.state_machine.trigger_alarm(self._triggered_by)
        if success:
            await self._execute_modules_trigger()
        await self.async_request_refresh()
        return success

    async def async_set_fake_presence(self, active: bool) -> None:
        """Set fake presence and fire notification + event."""
        if not hasattr(self, "store") or not self.store:
            _LOGGER.warning("Cannot set fake presence — store not loaded yet")
            return
        await self.store.async_set_fake_presence(active)
        msg = FAKE_PRESENCE_ON_EN if active else FAKE_PRESENCE_OFF_EN
        try:
            from homeassistant.components.persistent_notification import (
                async_create as pn_create,
            )
            pn_create(
                self.hass,
                message=msg,
                title="Secure Me - Fake Presence",
                notification_id=NOTIFY_ID_FAKE_PRESENCE,
            )
        except Exception as err:
            _LOGGER.warning("Could not create persistent notification: %s", err)
        self.hass.bus.async_fire(EVENT_FAKE_PRESENCE_CHANGED, {"active": active})
        _LOGGER.info("Fake presence set to %s", active)
        await self.async_request_refresh()

    # ── Config ───────────────────────────────────────────────────────────────

    def update_config(self, config_data: dict[str, Any]) -> None:
        """Update configuration."""
        self._code = config_data.get(CONF_CODE, self._code)
        exit_delay = config_data.get(CONF_EXIT_DELAY, self.state_machine.exit_delay)
        entry_delay = config_data.get(CONF_ENTRY_DELAY, self.state_machine.entry_delay)
        trigger_time = config_data.get(CONF_TRIGGER_TIME, DEFAULT_TRIGGER_TIME)
        self.state_machine.update_config(exit_delay, entry_delay, trigger_time)

    # ── Module management ────────────────────────────────────────────────────

    def _init_modules(self, store=None) -> None:
        """Initialize all available modules."""
        if store is not None:
            stored_modules = store.get_modules()
        else:
            stored_modules = {}
        options_modules = self.config_entry.options.get("modules", {})

        def _get_config(mid: str) -> dict:
            return stored_modules.get(mid) or options_modules.get(mid, {})

        for mid in ("camera", "lock", "lights", "climate", "siren", "tts"):
            module_config = _get_config(mid)
            module_classes = {
                "camera": CameraModule,
                "lock": LockModule,
                "lights": LightsModule,
                "climate": ClimateModule,
                "siren": SirenModule,
                "tts": TTSModule,
            }
            self.modules[mid] = module_classes[mid](self.hass, module_config)

        _LOGGER.info("Modules initialized: %s", list(self.modules.keys()))

    async def _execute_modules_arm_away(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm("away")
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_away: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "arm_away", "error": str(err)}
                    )

    async def _execute_modules_arm_home(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm("home")
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_home: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "arm_home", "error": str(err)}
                    )

    async def _execute_modules_arm_night(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_arm("night")
                except Exception as err:
                    _LOGGER.error("Module %s failed on arm_night: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "arm_night", "error": str(err)}
                    )

    async def _execute_modules_disarm(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_disarm()
                except Exception as err:
                    _LOGGER.error("Module %s failed on disarm: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "disarm", "error": str(err)}
                    )

    async def _execute_modules_trigger(self) -> None:
        for mid, module in self.modules.items():
            if module.enabled:
                try:
                    await module.async_trigger()
                except Exception as err:
                    _LOGGER.error("Module %s failed on trigger: %s", mid, err)
                    self.hass.bus.async_fire(
                        EVENT_MODULE_ERROR, {"module": mid, "action": "trigger", "error": str(err)}
                    )

    def enable_module(self, module_id: str) -> bool:
        if module_id not in self.modules:
            return False
        self.modules[module_id].enable()
        self.hass.bus.async_fire(EVENT_MODULE_ENABLED, {"module": module_id})
        return True

    def disable_module(self, module_id: str) -> bool:
        if module_id not in self.modules:
            return False
        self.modules[module_id].disable()
        self.hass.bus.async_fire(EVENT_MODULE_DISABLED, {"module": module_id})
        return True

    def update_module_config(self, module_id: str, config: dict) -> bool:
        """Re-initialize a module with updated configuration."""
        module_classes = {
            "camera": CameraModule, "lock": LockModule, "lights": LightsModule,
            "climate": ClimateModule, "siren": SirenModule, "tts": TTSModule,
        }
        cls = module_classes.get(module_id)
        if not cls:
            return False
        try:
            self.modules[module_id] = cls(self.hass, config)
            return True
        except Exception as err:
            _LOGGER.error("Failed to re-initialize module %s: %s", module_id, err)
            return False

    async def async_load_store_config(self, store) -> None:
        """Load module and sensor configs from store, re-initialize modules."""
        self.store = store
        stored = store.get_modules()
        if stored:
            for module_id, config in stored.items():
                if config:
                    normalized = _normalize_coordinator_config(module_id, config)
                    self.update_module_config(module_id, normalized)

        # v1.2.0: Push sensor configs and groups into zone manager
        sensor_configs = store.get_sensors()
        self.zone_manager.load_sensor_configs(sensor_configs)

        sensor_groups = store.get_sensor_groups()
        if sensor_groups:
            self.zone_manager.load_sensor_groups(sensor_groups)
            _LOGGER.info("Loaded %d sensor groups from store", len(sensor_groups))

    # ── Health ───────────────────────────────────────────────────────────────

    def get_health_score(self) -> int:
        total, available = 0, 0
        for module in self.modules.values():
            if not module.enabled:
                continue
            for eid in self._get_module_entity_ids(module):
                total += 1
                state = self.hass.states.get(eid)
                if state and state.state not in ("unavailable", "unknown"):
                    available += 1
        return round((available / total) * 100) if total > 0 else 100

    def get_module_health(self) -> dict[str, dict]:
        result = {}
        for mid, module in self.modules.items():
            if not module.enabled:
                result[mid] = {"enabled": False, "status": "disabled", "total": 0, "available": 0, "unavailable": []}
                continue
            entities = self._get_module_entity_ids(module)
            unavail = [
                eid for eid in entities
                if not self.hass.states.get(eid)
                or self.hass.states.get(eid).state in ("unavailable", "unknown")
            ]
            result[mid] = {
                "enabled": True,
                "status": "problem" if unavail else "ok",
                "total": len(entities),
                "available": len(entities) - len(unavail),
                "unavailable": unavail,
            }
        return result

    def get_enabled_module_count(self) -> int:
        return sum(1 for m in self.modules.values() if m.enabled)

    @staticmethod
    def _get_module_entity_ids(module) -> list[str]:
        entities: list[str] = []
        for attr in ("poe_switches", "cameras", "recording_entities", "locks", "lights", "climates", "media_players"):
            val = getattr(module, attr, None)
            if isinstance(val, list):
                entities.extend(val)
        for attr in ("door_sensors", "battery_sensors"):
            val = getattr(module, attr, None)
            if isinstance(val, dict):
                entities.extend(val.values())
        for attr in ("gateway_light",):
            val = getattr(module, attr, None)
            if isinstance(val, str) and "." in val:
                entities.append(val)
        if not entities and hasattr(module, "config"):
            for key in ("entities", "cameras", "locks", "climates", "lights", "media_players", "poe_switches"):
                val = module.config.get(key)
                if isinstance(val, list):
                    entities.extend(val)
                elif isinstance(val, dict):
                    entities.extend(val.values())
        return list({e for e in entities if e and isinstance(e, str) and "." in e})

    # ── Shutdown ─────────────────────────────────────────────────────────────

    async def async_shutdown(self) -> None:
        """Shutdown coordinator."""
        _LOGGER.info("Shutting down coordinator")

        # Unregister push event listener
        if hasattr(self, "_push_unsub") and self._push_unsub:
            self._push_unsub()

        if hasattr(self, "modules"):
            for mid, module in self.modules.items():
                try:
                    await module.async_cleanup()
                except Exception as err:
                    _LOGGER.error("Module %s cleanup failed: %s", mid, err)
        if hasattr(self, "zone_manager"):
            try:
                self.zone_manager.stop_monitoring()
            except Exception as err:
                _LOGGER.error("Zone manager cleanup failed: %s", err)
        if hasattr(self, "state_machine"):
            try:
                self.state_machine.cleanup()
            except Exception as err:
                _LOGGER.error("State machine cleanup failed: %s", err)
