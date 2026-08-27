# VERSION = "1.5.5"
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
# NOTE: this was stuck at "1.5.0" while the file header above had already
# moved to 1.5.1 -- the two markers had drifted apart, meaning the panel's
# cache-busting query param (?v=VERSION) was stale for a full release cycle.
# Keeping both markers in sync going forward.
VERSION = "1.5.5"
PANEL_URL = f"/api/{DOMAIN}-panel"
PANEL_NAME = "secure-me-panel"
PANEL_FOLDER = "frontend"
PANEL_FILENAME = "secure-me-panel.js"
CUSTOM_COMPONENTS = "custom_components"

# Alarm card (custom Lovelace card bundled with the integration)
CARD_URL      = f"/api/{DOMAIN}-alarm-card"
CARD_FILENAME = "secure-me-alarm-card.js"


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

    card_file = os.path.join(panel_dir, CARD_FILENAME)

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

        # v1.5.3: the floorplan image no longer gets a custom static path here.
        # It now lives under config/www/secure_me_floorplan/ and is served
        # natively by HA's built-in /local/ static route -- registered once
        # by HA core itself, not per-integration, so it needs no entry in
        # `paths` and survives every HACS update untouched. See ws_floorplan.py
        # for where the file is written and migrated from the old location.

        await hass.http.async_register_static_paths(paths)
        hass.data[DOMAIN]["_static_registered"] = True
        _LOGGER.info(
            "Secure Me: static path registered %s -> %s", PANEL_URL, panel_file
        )

        # Register alarm card as a Lovelace resource
        await _async_register_lovelace_resources(hass, [
            (f"{CARD_URL}?v={VERSION}", card_file, "alarm card"),
        ])
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


async def _async_register_lovelace_resources(
    hass: HomeAssistant,
    cards: list[tuple[str, str, str]],
) -> None:
    """Register JS files as Lovelace resources (module type).

    Uses the lovelace storage collection directly so the cards appear
    in HA's resource list and are loaded on every dashboard.
    Falls back gracefully if the lovelace component is not available.

    Args:
        cards: list of (url, filepath, label) tuples.
               url      — versioned URL e.g. /api/secure_me-info-card?v=1.3.0
               filepath — absolute path to the JS file (used for existence check)
               label    — human-readable name for logging
    """
    try:
        from homeassistant.components.lovelace import resources as ll_resources  # type: ignore[import]
    except ImportError:
        _LOGGER.warning(
            "Secure Me: lovelace resources module not available — "
            "add cards manually via Settings > Dashboards > Resources"
        )
        return

    try:
        ll = hass.data.get("lovelace")
        if ll is None:
            _LOGGER.debug("Secure Me: lovelace not yet loaded, skipping resource registration")
            return

        # LovelaceData is an object, not a dict — access .resources directly
        resources = getattr(ll, "resources", None)
        if resources is None:
            _LOGGER.debug("Secure Me: lovelace resources collection not available")
            return

        # Load existing resources so we can check for duplicates
        try:
            await resources.async_load()
        except Exception:
            pass

        existing_urls: set[str] = set()
        try:
            for item in resources.async_items():
                existing_urls.add(item.get("url", "").split("?")[0])
        except Exception:
            pass

        for url, fpath, label in cards:
            if not os.path.isfile(fpath):
                _LOGGER.debug("Secure Me: %s not found at %s, skipping", label, fpath)
                continue

            base_url = url.split("?")[0]
            if base_url in existing_urls:
                _LOGGER.debug("Secure Me: %s already in Lovelace resources, skipping", label)
                continue

            try:
                await resources.async_create_item({"res_type": "module", "url": url})
                _LOGGER.info("Secure Me: %s added to Lovelace resources at %s", label, url)
            except Exception as err:
                _LOGGER.warning("Secure Me: could not add %s to Lovelace resources: %s", label, err)

    except Exception as err:
        _LOGGER.warning(
            "Secure Me: Lovelace resource registration failed (%s) — "
            "add cards manually via Settings > Dashboards > Resources",
            err,
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
