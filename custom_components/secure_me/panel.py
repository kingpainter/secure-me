# VERSION = "1.2.0"
"""Panel registration for Secure Me."""
from __future__ import annotations

import os
import logging

from homeassistant.components import frontend, panel_custom
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Panel configuration
VERSION = "1.2.0"
PANEL_URL = f"/api/{DOMAIN}-panel"
PANEL_ICON = "mdi:shield-lock"
PANEL_NAME = "secure-me-panel"
PANEL_TITLE = "Secure Me"
PANEL_FOLDER = "frontend"
PANEL_FILENAME = "secure-me-panel.js"
CUSTOM_COMPONENTS = "custom_components"
INTEGRATION_FOLDER = DOMAIN


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the Secure Me panel (Alarmo-style)."""
    root_dir = os.path.join(hass.config.path(CUSTOM_COMPONENTS), INTEGRATION_FOLDER)
    panel_dir = os.path.join(root_dir, PANEL_FOLDER)
    view_url = os.path.join(panel_dir, PANEL_FILENAME)

    # Cache busting based on file modification time
    try:
        cache_bust = int(os.path.getmtime(view_url))
    except OSError:
        _LOGGER.warning("Panel file not found: %s", view_url)
        cache_bust = 0

    # Register static path — use compat import that works across HA versions
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths(
            [StaticPathConfig(PANEL_URL, view_url, cache_headers=False)]
        )
    except ImportError:
        # Older HA versions use a different signature
        hass.http.register_static_path(PANEL_URL, view_url, cache_headers=False)

    _LOGGER.info("Panel static path registered: %s", PANEL_URL)

    # Register custom panel
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name=PANEL_NAME,
        frontend_url_path=DOMAIN,
        module_url=f"{PANEL_URL}?v={VERSION}&m={cache_bust}",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=False,
        config={},
        config_panel_domain=DOMAIN,
    )

    _LOGGER.info("Panel '%s' registered in sidebar at /%s", PANEL_TITLE, DOMAIN)


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Unregister the Secure Me panel."""
    frontend.async_remove_panel(hass, DOMAIN)
    _LOGGER.debug("Panel removed from sidebar")
