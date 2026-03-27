"""Notification Dispatcher for Secure Me.

SYSTEM NOTIFICATION ARCHITECTURE
=================================

Always-on (cannot be disabled):
  smoke / water_leak — Critical push to ALL users with receive_critical=True.
                       Critical push payload bypasses DND/Silent mode.

User-routed (armed/disarmed):
  armed   — sent only to the user who armed (by user_id match).
  disarmed — sent only to the user who disarmed (by user_id match).
  arming  — sent to the arming user.
  pending — sent to all users with receive_critical=True.
  triggered — sent to ALL users with receive_critical=True.
  low_battery — sent to all users with receive_alerts=True.

Per-notification config:
  channels: ["push"] / ["tts"] / ["push", "tts"]
  service: notify service for push channel

User notification settings (on each user object):
  notify_service: str        — e.g. "notify.mobile_app_flemming"
  receive_critical: bool     — receives triggered/smoke/water/pending alerts
  receive_alerts: bool       — receives low_battery, arm_fail alerts
  receive_own_actions: bool  — receives own arm/disarm confirmations
  tts_quiet_start: int|None  — hour (0-23) start of TTS quiet period
  tts_quiet_end: int|None    — hour (0-23) end of TTS quiet period
"""
# VERSION = "1.3.0"

from __future__ import annotations

import logging
from datetime import datetime
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

CHANNEL_PUSH = "push"
CHANNEL_TTS  = "tts"


def _get_store(hass: HomeAssistant):
    return hass.data.get(DOMAIN, {}).get("store")


def _get_tts_module(hass: HomeAssistant):
    """Get enabled TTS module from coordinator, if any."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        if isinstance(entry_data, dict) and "coordinator" in entry_data:
            tts = entry_data["coordinator"].modules.get("tts")
            if tts and tts.enabled:
                return tts
    return None


def _is_tts_quiet_now(user: dict) -> bool:
    """Return True if current time is within the user's TTS quiet hours."""
    start = user.get("tts_quiet_start")
    end   = user.get("tts_quiet_end")
    if start is None or end is None:
        return False
    now_hour = datetime.now().hour
    if start <= end:
        return start <= now_hour < end
    # Wraps midnight: e.g. 22–07
    return now_hour >= start or now_hour < end


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


async def _send_push(
    hass: HomeAssistant,
    service: str,
    title: str,
    message: str,
    *,
    critical: bool = False,
    actions: list | None = None,
) -> None:
    """Send a push notification via a notify service."""
    try:
        svc_domain, svc_name = service.split(".", 1)
    except ValueError:
        _LOGGER.error("Invalid notify service '%s'", service)
        return

    service_data: dict[str, Any] = {"title": title, "message": message}
    if critical:
        service_data["data"] = _critical_push_data()
    elif actions:
        service_data["data"] = {"actions": actions}

    try:
        await hass.services.async_call(svc_domain, svc_name, service_data, blocking=False)
        _LOGGER.debug("Push sent via %s (critical=%s): %s", service, critical, title)
    except Exception as err:
        _LOGGER.error("Failed to send push via %s: %s", service, err)


async def _send_tts_to_user(
    hass: HomeAssistant,
    user: dict,
    message: str,
    urgent: bool = False,
) -> None:
    """Send TTS announcement, respecting the user's quiet hours."""
    if _is_tts_quiet_now(user):
        _LOGGER.debug(
            "TTS suppressed for user '%s' — quiet hours active", user.get("name", "?")
        )
        return
    tts = _get_tts_module(hass)
    if tts is None:
        _LOGGER.debug("TTS channel requested but TTS module not enabled")
        return
    try:
        await tts.announce_system(message, urgent=urgent)
    except Exception as err:
        _LOGGER.error("TTS system announcement failed: %s", err)


async def _dispatch_to_user(
    hass: HomeAssistant,
    notif: dict,
    user: dict | None,
    title: str,
    message: str,
    *,
    critical: bool = False,
) -> None:
    """Dispatch a notification to a specific user via configured channels.

    If user is None, falls back to the notify service on the notif config.
    """
    channels = notif.get("channels", [CHANNEL_PUSH])
    if isinstance(channels, str):
        channels = [channels]

    # Determine push service — user's personal service takes priority
    push_service = (
        (user.get("notify_service") if user else None)
        or notif.get("service", "notify.notify")
    )

    if CHANNEL_PUSH in channels:
        await _send_push(
            hass, push_service, title, message,
            critical=critical,
            actions=notif.get("actions"),
        )

    if CHANNEL_TTS in channels and message:
        await _send_tts_to_user(hass, user or {}, message, urgent=critical)


async def _dispatch_for_trigger(
    hass: HomeAssistant,
    trigger: str,
    context: dict[str, str],
    *,
    title_override: str | None = None,
    urgent: bool = False,
    acting_user_id: str | None = None,
    broadcast: bool = False,
) -> None:
    """Route notifications for a trigger.

    acting_user_id: if set, only notify that specific user (arm/disarm).
    broadcast: if True, notify all users with receive_critical=True (triggered).
    Falls back to notification-level service if no user has a notify_service.
    """
    store = _get_store(hass)
    if not store:
        return

    users = store.get_users()

    for notif in store.get_notifications().values():
        if not notif.get("enabled", True):
            continue
        if notif.get("trigger") != trigger:
            continue

        message = _build_message(notif.get("message", ""), context)
        title = title_override or f"Secure Me: {notif.get('name', 'Alert')}"

        if broadcast:
            # Send to all users with receive_critical=True
            sent_to_any = False
            for user in users.values():
                if not user.get("enabled", True):
                    continue
                if not user.get("receive_critical", True):
                    continue
                await _dispatch_to_user(hass, notif, user, title, message, critical=urgent)
                sent_to_any = True

            # Fallback if no users configured
            if not sent_to_any:
                await _dispatch_to_user(hass, notif, None, title, message, critical=urgent)

        elif acting_user_id:
            # Send only to the user who performed the action
            user = users.get(acting_user_id)
            if user and user.get("enabled", True) and user.get("receive_own_actions", True):
                await _dispatch_to_user(hass, notif, user, title, message)
            else:
                # Fallback to notification service if user not found or disabled
                await _dispatch_to_user(hass, notif, None, title, message)

        else:
            # No user context — use notification's own service
            await _dispatch_to_user(hass, notif, None, title, message, critical=urgent)


async def _send_critical_to_all_users(
    hass: HomeAssistant,
    store,
    title: str,
    message: str,
) -> None:
    """Send critical alert to all users with receive_critical=True.
    Falls back to notify.notify if no users configured.
    """
    users = store.get_users() if store else {}
    sent = False
    for user in users.values():
        if not user.get("enabled", True):
            continue
        if not user.get("receive_critical", True):
            continue
        svc = user.get("notify_service", "notify.notify")
        await _send_push(hass, svc, title, message, critical=True)
        sent = True

    if not sent:
        await _send_push(hass, "notify.notify", title, message, critical=True)


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


class NotificationDispatcher:
    """Secure Me notification dispatcher.

    Routing rules:
    - armed/disarmed/arming → only the acting user (by user_id)
    - triggered/pending/smoke/water_leak → all users with receive_critical=True
    - low_battery → all users with receive_alerts=True
    - TTS respects per-user quiet hours

    Always-on: smoke/water_leak fire regardless of notification toggle.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsubs: list = []
        self._smoke_sensors: set[str] = set()
        self._moisture_sensors: set[str] = set()

    @callback
    def async_setup(self) -> None:
        hass = self.hass

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
            _LOGGER.info("Secure Me: No smoke/moisture sensors found at startup")

        self._unsubs.append(hass.bus.async_listen(EVENT_ALARM_TRIGGERED, self._on_triggered))
        self._unsubs.append(hass.bus.async_listen(EVENT_ALARM_ARMED,     self._on_armed))
        self._unsubs.append(hass.bus.async_listen(EVENT_ALARM_DISARMED,  self._on_disarmed))
        self._unsubs.append(hass.bus.async_listen(f"{DOMAIN}_arming",    self._on_arming))
        self._unsubs.append(hass.bus.async_listen(f"{DOMAIN}_pending",   self._on_pending))
        self._unsubs.append(hass.bus.async_listen("state_changed",       self._on_sensor_state_change))

        _LOGGER.info("Secure Me NotificationDispatcher active")

    def async_unload(self) -> None:
        for unsub in self._unsubs:
            try:
                unsub()
            except Exception:
                pass
        self._unsubs.clear()

    # ── Alarm handlers ──────────────────────────────────────────────────────

    async def _on_triggered(self, event: Event) -> None:
        triggered_by = event.data.get("triggered_by") or "unknown"
        await _dispatch_for_trigger(
            self.hass, "triggered",
            {"state": "triggered", "triggered_by": triggered_by},
            title_override="ALERT: Secure Me Alarm Triggered",
            urgent=True,
            broadcast=True,
        )

    async def _on_armed(self, event: Event) -> None:
        armed_by     = event.data.get("armed_by") or "system"
        armed_by_id  = event.data.get("armed_by_id")
        mode         = event.data.get("mode", "armed")
        await _dispatch_for_trigger(
            self.hass, "armed",
            {"state": mode, "armed_by": armed_by},
            acting_user_id=armed_by_id,
        )

    async def _on_disarmed(self, event: Event) -> None:
        disarmed_by    = event.data.get("disarmed_by") or "system"
        disarmed_by_id = event.data.get("disarmed_by_id")
        await _dispatch_for_trigger(
            self.hass, "disarmed",
            {"state": "disarmed", "disarmed_by": disarmed_by, "armed_by": disarmed_by},
            acting_user_id=disarmed_by_id,
        )

    async def _on_arming(self, event: Event) -> None:
        armed_by_id = event.data.get("armed_by_id")
        await _dispatch_for_trigger(
            self.hass, "arming",
            {"state": "arming"},
            acting_user_id=armed_by_id,
        )

    async def _on_pending(self, event: Event) -> None:
        """Entry delay — broadcast to all critical users."""
        await _dispatch_for_trigger(
            self.hass, "pending",
            {"state": "pending"},
            broadcast=True,
            urgent=True,
        )

    # ── Sensor state handler ─────────────────────────────────────────────────

    async def _on_sensor_state_change(self, event: Event) -> None:
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None:
            return

        entity_id   = new_state.entity_id
        device_class = new_state.attributes.get("device_class", "")
        new_val     = new_state.state
        old_val     = old_state.state if old_state else None

        if device_class == "smoke" and entity_id not in self._smoke_sensors:
            self._smoke_sensors.add(entity_id)
            _LOGGER.info("Secure Me: New smoke sensor registered (critical): %s", entity_id)
        elif device_class == "moisture" and entity_id not in self._moisture_sensors:
            self._moisture_sensors.add(entity_id)
            _LOGGER.info("Secure Me: New moisture sensor registered (critical): %s", entity_id)

        if new_val != "on" or old_val == "on":
            return

        sensor_name = new_state.attributes.get("friendly_name", entity_id)

        if device_class == "smoke":
            await self._fire_smoke_alert(sensor_name, entity_id)
        elif device_class == "moisture":
            await self._fire_moisture_alert(sensor_name, entity_id)

    # ── Critical safety alerts ───────────────────────────────────────────────

    async def _fire_smoke_alert(self, sensor_name: str, entity_id: str) -> None:
        """Always-on critical alert — ignores notification toggle."""
        store = _get_store(self.hass)
        title = f"FIRE ALERT: {sensor_name}"
        default_message = f"FIRE ALERT: Smoke detected by {sensor_name}. Evacuate immediately!"
        context = {"sensor": sensor_name, "entity_id": entity_id}

        _LOGGER.critical("Secure Me FIRE ALERT: %s (%s)", sensor_name, entity_id)

        user_notifs = [
            n for n in (store.get_notifications().values() if store else [])
            if n.get("trigger") == "smoke"
        ]

        if user_notifs:
            for notif in user_notifs:
                msg = _build_message(notif.get("message", default_message), context)
                # Always broadcast critical to all receive_critical users
                channels = notif.get("channels", [CHANNEL_PUSH])
                users = store.get_users() if store else {}
                sent = False
                for user in users.values():
                    if not user.get("enabled", True) or not user.get("receive_critical", True):
                        continue
                    svc = user.get("notify_service") or notif.get("service", "notify.notify")
                    await _send_push(self.hass, svc, title, msg, critical=True)
                    if CHANNEL_TTS in channels:
                        await _send_tts_to_user(self.hass, user, msg, urgent=True)
                    sent = True
                if not sent:
                    await _send_push(self.hass, notif.get("service", "notify.notify"), title, msg, critical=True)
        else:
            await _send_critical_to_all_users(self.hass, store, title, default_message)

    async def _fire_moisture_alert(self, sensor_name: str, entity_id: str) -> None:
        """Always-on critical alert — ignores notification toggle."""
        store = _get_store(self.hass)
        title = f"WATER LEAK: {sensor_name}"
        default_message = f"WATER LEAK detected by {sensor_name}. Shut off water supply immediately!"
        context = {"sensor": sensor_name, "entity_id": entity_id}

        _LOGGER.critical("Secure Me WATER LEAK: %s (%s)", sensor_name, entity_id)

        user_notifs = [
            n for n in (store.get_notifications().values() if store else [])
            if n.get("trigger") == "water_leak"
        ]

        if user_notifs:
            for notif in user_notifs:
                msg = _build_message(notif.get("message", default_message), context)
                channels = notif.get("channels", [CHANNEL_PUSH])
                users = store.get_users() if store else {}
                sent = False
                for user in users.values():
                    if not user.get("enabled", True) or not user.get("receive_critical", True):
                        continue
                    svc = user.get("notify_service") or notif.get("service", "notify.notify")
                    await _send_push(self.hass, svc, title, msg, critical=True)
                    if CHANNEL_TTS in channels:
                        await _send_tts_to_user(self.hass, user, msg, urgent=True)
                    sent = True
                if not sent:
                    await _send_push(self.hass, notif.get("service", "notify.notify"), title, msg, critical=True)
        else:
            await _send_critical_to_all_users(self.hass, store, title, default_message)

    # ── Low battery ──────────────────────────────────────────────────────────

    async def dispatch_low_battery(self) -> None:
        store = _get_store(self.hass)
        if not store:
            return

        low = _get_low_batteries(self.hass)
        sensor_list = "\n".join(f"  {b['name']}: {b['level']}%" for b in low) if low else "No sensors below threshold."
        count = str(len(low))

        users = store.get_users()

        for notif in store.get_notifications().values():
            if not notif.get("enabled", True):
                continue
            if notif.get("trigger") != "low_battery":
                continue

            msg = _build_message(notif.get("message", ""), {"sensor_list": sensor_list, "count": count})
            title = f"Secure Me: {notif.get('name', 'Low Battery Alert')}"
            channels = notif.get("channels", [CHANNEL_PUSH])

            # Send to all users with receive_alerts=True
            sent = False
            for user in users.values():
                if not user.get("enabled", True):
                    continue
                if not user.get("receive_alerts", True):
                    continue
                svc = user.get("notify_service") or notif.get("service", "notify.notify")
                if CHANNEL_PUSH in channels:
                    await _send_push(self.hass, svc, title, msg)
                if CHANNEL_TTS in channels and msg:
                    await _send_tts_to_user(self.hass, user, msg)
                sent = True

            if not sent:
                if CHANNEL_PUSH in channels:
                    await _send_push(self.hass, notif.get("service", "notify.notify"), title, msg)

    # ── Introspection ─────────────────────────────────────────────────────────

    def get_monitored_sensors(self) -> dict[str, list[str]]:
        return {
            "smoke": sorted(self._smoke_sensors),
            "moisture": sorted(self._moisture_sensors),
        }


def async_setup_dispatcher(hass: HomeAssistant) -> NotificationDispatcher:
    dispatcher = NotificationDispatcher(hass)
    dispatcher.async_setup()
    return dispatcher
