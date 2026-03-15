"""Notification Dispatcher for Secure Me.

CRITICAL SAFETY ALERTS (smoke + water_leak):
  - Always fired regardless of user toggle
  - Critical push payload (bypasses Do Not Disturb / Silent mode)
  - Sent to ALL configured notify services
  - Fallback to notify.notify if nothing configured
  - Auto-discovers smoke/moisture sensors at startup

User-configurable: armed, disarmed, triggered, arming, pending, low_battery
"""
# VERSION = "1.1.0"

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, Event, callback

from .const import (
    DOMAIN,
    EVENT_ALARM_ARMED,
    EVENT_ALARM_DISARMED,
    EVENT_ALARM_TRIGGERED,
)

_LOGGER = logging.getLogger(__name__)

NOTIF_BATTERY_THRESHOLD = 15


def _get_store(hass: HomeAssistant):
    return hass.data.get(DOMAIN, {}).get("store")


def _build_message(template: str, context: dict[str, str]) -> str:
    for key, value in context.items():
        template = template.replace(f"{{{key}}}", value)
    return template


def _critical_push_data() -> dict[str, Any]:
    """Critical push payload — bypasses Do Not Disturb on iOS and Android."""
    return {
        "push": {
            "sound": {"name": "default", "critical": 1, "volume": 1.0},
            "interruption-level": "critical",
        },
        "ttl": 0,
        "priority": "high",
        "importance": "max",
    }


async def _send_notification(
    hass: HomeAssistant,
    notif: dict[str, Any],
    title: str,
    message: str,
    *,
    critical: bool = False,
) -> None:
    service_target = notif.get("service", "notify.notify")
    try:
        svc_domain, svc_name = service_target.split(".", 1)
    except ValueError:
        _LOGGER.error("Invalid notify service '%s'", service_target)
        return

    service_data: dict[str, Any] = {"title": title, "message": message}
    if critical:
        service_data["data"] = _critical_push_data()
    elif notif.get("actions"):
        service_data["data"] = {"actions": notif["actions"]}

    try:
        await hass.services.async_call(svc_domain, svc_name, service_data, blocking=False)
        _LOGGER.debug("Notification sent via %s (critical=%s): %s", service_target, critical, title)
    except Exception as err:
        _LOGGER.error("Failed to send notification via %s: %s", service_target, err)


async def _send_critical_to_all_services(
    hass: HomeAssistant, store, title: str, message: str
) -> None:
    """Send critical alert to every configured service + notify.notify fallback."""
    services: set[str] = {"notify.notify"}
    if store:
        for notif in store.get_notifications().values():
            svc = notif.get("service")
            if svc:
                services.add(svc)
    for svc in services:
        await _send_notification(hass, {"service": svc}, title, message, critical=True)


def _get_low_batteries(hass: HomeAssistant) -> list[dict[str, Any]]:
    low = []
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != "battery":
            continue
        try:
            level = int(float(state.state))
        except (ValueError, TypeError):
            continue
        if level < NOTIF_BATTERY_THRESHOLD:
            low.append({
                "name": state.attributes.get("friendly_name", state.entity_id),
                "level": level,
                "entity_id": state.entity_id,
            })
    low.sort(key=lambda x: x["level"])
    return low


def _discover_safety_sensors(hass: HomeAssistant) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {"smoke": [], "moisture": []}
    for state in hass.states.async_all("binary_sensor"):
        dc = state.attributes.get("device_class", "")
        if dc in found:
            found[dc].append(state.entity_id)
    return found


async def _dispatch_for_trigger(
    hass: HomeAssistant,
    trigger: str,
    context: dict[str, str],
    title_override: str | None = None,
) -> None:
    store = _get_store(hass)
    if not store:
        return
    for notif in store.get_notifications().values():
        if not notif.get("enabled", True):
            continue
        if notif.get("trigger") != trigger:
            continue
        message = _build_message(notif.get("message", ""), context)
        title = title_override or f"Secure Me: {notif.get('name', 'Alert')}"
        await _send_notification(hass, notif, title, message)


class NotificationDispatcher:
    """Secure Me notification dispatcher.

    Safety rules (smoke + water_leak):
      - ALWAYS fires, toggle is ignored
      - Critical push payload — bypasses DND/Silent
      - Sent to all configured services, fallback to notify.notify
      - Auto-discovers sensors at startup, registers new ones via events
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsubs: list = []
        self._smoke_sensors: set[str] = set()
        self._moisture_sensors: set[str] = set()

    @callback
    def async_setup(self) -> None:
        hass = self.hass

        # Auto-discover safety sensors at startup
        discovered = _discover_safety_sensors(hass)
        self._smoke_sensors = set(discovered["smoke"])
        self._moisture_sensors = set(discovered["moisture"])

        if self._smoke_sensors:
            _LOGGER.info(
                "Secure Me: %d smoke sensor(s) monitored (critical): %s",
                len(self._smoke_sensors), ", ".join(sorted(self._smoke_sensors)),
            )
        if self._moisture_sensors:
            _LOGGER.info(
                "Secure Me: %d moisture sensor(s) monitored (critical): %s",
                len(self._moisture_sensors), ", ".join(sorted(self._moisture_sensors)),
            )
        if not self._smoke_sensors and not self._moisture_sensors:
            _LOGGER.info(
                "Secure Me: No smoke/moisture sensors found at startup — "
                "will auto-register any added later."
            )

        # Alarm events
        self._unsubs.append(hass.bus.async_listen(EVENT_ALARM_TRIGGERED, self._on_triggered))
        self._unsubs.append(hass.bus.async_listen(EVENT_ALARM_ARMED, self._on_armed))
        self._unsubs.append(hass.bus.async_listen(EVENT_ALARM_DISARMED, self._on_disarmed))
        self._unsubs.append(hass.bus.async_listen(f"{DOMAIN}_arming", self._on_arming))
        self._unsubs.append(hass.bus.async_listen(f"{DOMAIN}_pending", self._on_pending))

        # Sensor state changes — listen to all state_changed events via bus.
        # async_track_state_change_event does NOT accept None as entity_ids.
        self._unsubs.append(
            hass.bus.async_listen("state_changed", self._on_sensor_state_change)
        )

        _LOGGER.info("Secure Me NotificationDispatcher active")

    def async_unload(self) -> None:
        for unsub in self._unsubs:
            try:
                unsub()
            except Exception:
                pass
        self._unsubs.clear()
        _LOGGER.debug("Secure Me NotificationDispatcher unloaded")

    # ── Alarm handlers ──────────────────────────────────────────

    async def _on_triggered(self, event: Event) -> None:
        triggered_by = event.data.get("triggered_by") or "unknown"
        await _dispatch_for_trigger(
            self.hass, "triggered",
            {"state": "triggered", "triggered_by": triggered_by},
            title_override="ALERT: Secure Me Alarm Triggered",
        )

    async def _on_armed(self, event: Event) -> None:
        await _dispatch_for_trigger(
            self.hass, "armed",
            {"state": event.data.get("mode", "armed"), "armed_by": event.data.get("armed_by") or "system"},
        )

    async def _on_disarmed(self, event: Event) -> None:
        disarmed_by = event.data.get("disarmed_by") or "system"
        await _dispatch_for_trigger(
            self.hass, "disarmed",
            {"state": "disarmed", "disarmed_by": disarmed_by, "armed_by": disarmed_by},
        )

    async def _on_arming(self, event: Event) -> None:
        await _dispatch_for_trigger(self.hass, "arming", {"state": "arming"})

    async def _on_pending(self, event: Event) -> None:
        await _dispatch_for_trigger(self.hass, "pending", {"state": "pending"})

    # ── Sensor state handler ─────────────────────────────────────

    async def _on_sensor_state_change(self, event: Event) -> None:
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None:
            return

        entity_id = new_state.entity_id
        device_class = new_state.attributes.get("device_class", "")
        new_val = new_state.state
        old_val = old_state.state if old_state else None

        # Auto-register newly discovered safety sensors
        if device_class == "smoke" and entity_id not in self._smoke_sensors:
            self._smoke_sensors.add(entity_id)
            _LOGGER.info("Secure Me: New smoke sensor registered (critical): %s", entity_id)
        elif device_class == "moisture" and entity_id not in self._moisture_sensors:
            self._moisture_sensors.add(entity_id)
            _LOGGER.info("Secure Me: New moisture sensor registered (critical): %s", entity_id)

        # Only act on fresh transition TO "on"
        if new_val != "on" or old_val == "on":
            return

        sensor_name = new_state.attributes.get("friendly_name", entity_id)

        if device_class == "smoke":
            await self._fire_smoke_alert(sensor_name, entity_id)
        elif device_class == "moisture":
            await self._fire_moisture_alert(sensor_name, entity_id)

    # ── Critical safety alert senders ───────────────────────────

    async def _fire_smoke_alert(self, sensor_name: str, entity_id: str) -> None:
        """Critical fire/smoke alert — always fires, toggle ignored."""
        store = _get_store(self.hass)
        title = f"FIRE ALERT: {sensor_name}"
        default_message = (
            f"FIRE ALERT: Smoke detected by {sensor_name}. Evacuate immediately!"
        )
        context = {"sensor": sensor_name, "entity_id": entity_id}

        _LOGGER.critical("Secure Me FIRE ALERT: %s (%s)", sensor_name, entity_id)

        user_notifs = []
        if store:
            for notif in store.get_notifications().values():
                if notif.get("trigger") == "smoke":
                    # Critical: ignore enabled toggle
                    user_notifs.append(notif)

        if user_notifs:
            for notif in user_notifs:
                msg = _build_message(notif.get("message", default_message), context)
                await _send_notification(self.hass, notif, title, msg, critical=True)
        else:
            # Fallback: no smoke notification configured, send to all services anyway
            await _send_critical_to_all_services(self.hass, store, title, default_message)

    async def _fire_moisture_alert(self, sensor_name: str, entity_id: str) -> None:
        """Critical water-leak alert — always fires, toggle ignored."""
        store = _get_store(self.hass)
        title = f"WATER LEAK: {sensor_name}"
        default_message = (
            f"WATER LEAK detected by {sensor_name}. Shut off water supply immediately!"
        )
        context = {"sensor": sensor_name, "entity_id": entity_id}

        _LOGGER.critical("Secure Me WATER LEAK: %s (%s)", sensor_name, entity_id)

        user_notifs = []
        if store:
            for notif in store.get_notifications().values():
                if notif.get("trigger") == "water_leak":
                    user_notifs.append(notif)

        if user_notifs:
            for notif in user_notifs:
                msg = _build_message(notif.get("message", default_message), context)
                await _send_notification(self.hass, notif, title, msg, critical=True)
        else:
            await _send_critical_to_all_services(self.hass, store, title, default_message)

    # ── Low battery ──────────────────────────────────────────────

    async def dispatch_low_battery(self) -> None:
        store = _get_store(self.hass)
        if not store:
            return

        low = _get_low_batteries(self.hass)
        if not low:
            sensor_list = "No sensors below threshold."
            count = "0"
        else:
            sensor_list = "\n".join(f"  {b['name']}: {b['level']}%" for b in low)
            count = str(len(low))

        for notif in store.get_notifications().values():
            if not notif.get("enabled", True):
                continue
            if notif.get("trigger") != "low_battery":
                continue
            msg = _build_message(notif.get("message", ""), {"sensor_list": sensor_list, "count": count})
            title = f"Secure Me: {notif.get('name', 'Low Battery Alert')}"
            await _send_notification(self.hass, notif, title, msg)

    # ── Introspection ────────────────────────────────────────────

    def get_monitored_sensors(self) -> dict[str, list[str]]:
        return {
            "smoke": sorted(self._smoke_sensors),
            "moisture": sorted(self._moisture_sensors),
        }


def async_setup_dispatcher(hass: HomeAssistant) -> NotificationDispatcher:
    dispatcher = NotificationDispatcher(hass)
    dispatcher.async_setup()
    return dispatcher
