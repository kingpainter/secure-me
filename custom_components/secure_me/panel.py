# VERSION = "1.3.0"
"""Panel registration for Secure Me.

Follows the Energy Hub pattern:
- Static HTTP path registered only ONCE per HA session (_static_registered guard).
  aiohttp cannot remove routes after registration, so double-registration on
  config-entry reload must be prevented here.
- sidebar_title and sidebar_icon are passed in from the caller so they can
  be driven by config-entry options in a future Options Flow.
"""
from __future__ import annotations

import os
import logging

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    DEFAULT_SIDEBAR_TITLE,
    DEFAULT_SIDEBAR_ICON,
)

_LOGGER = logging.getLogger(__name__)

# Panel configuration
VERSION = "1.3.0"
PANEL_URL = f"/api/{DOMAIN}-panel"
PANEL_NAME = "secure-me-panel"
PANEL_FOLDER = "frontend"
PANEL_FILENAME = "secure-me-panel.js"
CUSTOM_COMPONENTS = "custom_components"

# Alarm card (custom Lovelace card bundled with the integration)
CARD_URL      = f"/api/{DOMAIN}-alarm-card"
CARD_FILENAME = "secure-me-alarm-card.js"

# Info card (persons, weather, alarm status, lock)
INFO_CARD_URL      = f"/api/{DOMAIN}-info-card"
INFO_CARD_FILENAME = "secure-me-info-card.js"


async def async_register_panel(
    hass: HomeAssistant,
    sidebar_title: str = DEFAULT_SIDEBAR_TITLE,
    sidebar_icon: str = DEFAULT_SIDEBAR_ICON,
    require_admin: bool = False,
) -> None:
    """Register the Secure Me sidebar panel.

    Serves the JS file as a static HTTP endpoint (once per HA session),
    then registers the panel via panel_custom.
    """
    hass.data.setdefault(DOMAIN, {})

    root_dir = hass.config.path(CUSTOM_COMPONENTS, DOMAIN)
    panel_dir = os.path.join(root_dir, PANEL_FOLDER)
    panel_file = os.path.join(panel_dir, PANEL_FILENAME)

    card_file      = os.path.join(panel_dir, CARD_FILENAME)
    info_card_file = os.path.join(panel_dir, INFO_CARD_FILENAME)

    if not os.path.isfile(panel_file):
        _LOGGER.error(
            "Secure Me: panel JS not found at %s — "
            "make sure %s exists inside custom_components/secure_me/frontend/",
            panel_file,
            PANEL_FILENAME,
        )
        return

    # Cache busting via file mtime
    try:
        cache_bust = int(os.path.getmtime(panel_file))
    except OSError:
        cache_bust = 0

    # ── Register static HTTP paths (once per HA session) ─────────────────
    # aiohttp routes cannot be removed, so this must only run once.
    if not hass.data[DOMAIN].get("_static_registered", False):
        paths = [StaticPathConfig(PANEL_URL, panel_file, cache_headers=False)]
        # Alarm control card
        if os.path.isfile(card_file):
            paths.append(StaticPathConfig(CARD_URL, card_file, cache_headers=False))
            _LOGGER.info("Secure Me: alarm card registered at %s", CARD_URL)
        else:
            _LOGGER.debug("Secure Me: alarm card JS not found at %s, skipping", card_file)
        # Info card
        if os.path.isfile(info_card_file):
            paths.append(StaticPathConfig(INFO_CARD_URL, info_card_file, cache_headers=False))
            _LOGGER.info("Secure Me: info card registered at %s", INFO_CARD_URL)
        else:
            _LOGGER.debug("Secure Me: info card JS not found at %s, skipping", info_card_file)
        await hass.http.async_register_static_paths(paths)
        hass.data[DOMAIN]["_static_registered"] = True
        _LOGGER.info(
            "Secure Me: static path registered %s -> %s", PANEL_URL, panel_file
        )

        # Register both cards as Lovelace extra modules
        for url, fpath, label in [
            (CARD_URL,      card_file,      "alarm card"),
            (INFO_CARD_URL, info_card_file, "info card"),
        ]:
            if os.path.isfile(fpath):
                try:
                    versioned = f"{url}?v={VERSION}"
                    frontend.async_register_extra_module_url(hass, versioned)
                    _LOGGER.info("Secure Me: %s registered as Lovelace module at %s", label, versioned)
                except Exception as err:
                    _LOGGER.warning("Secure Me: could not register %s as Lovelace module: %s", label, err)
    else:
        _LOGGER.debug(
            "Secure Me: static path %s already registered, skipping", PANEL_URL
        )

    # ── Register sidebar panel via panel_custom ────────────────────────────
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name=PANEL_NAME,
        frontend_url_path=DOMAIN,
        module_url=f"{PANEL_URL}?v={VERSION}&m={cache_bust}",
        sidebar_title=sidebar_title,
        sidebar_icon=sidebar_icon,
        require_admin=require_admin,
        config={},
    )

    hass.data[DOMAIN]["_panel_registered"] = True
    _LOGGER.info(
        "Secure Me: panel '%s' (%s) registered at /%s",
        sidebar_title,
        sidebar_icon,
        DOMAIN,
    )


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the Secure Me panel from the sidebar.

    Only removes the sidebar entry — static HTTP path persists
    (aiohttp limitation) and is guarded by _static_registered.
    """
    hass.data.setdefault(DOMAIN, {})

    if hass.data[DOMAIN].get("_panel_registered", False):
        frontend.async_remove_panel(hass, DOMAIN)
        hass.data[DOMAIN]["_panel_registered"] = False
        _LOGGER.debug("Secure Me: panel removed from sidebar")
    else:
        _LOGGER.debug("Secure Me: panel was not registered, skipping removal")
