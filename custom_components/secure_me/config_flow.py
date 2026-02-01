"""Config flow for Secure Me integration."""
# VERSION = "0.0.1"

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CODE,
    CONF_ENTRY_DELAY,
    CONF_EXIT_DELAY,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_EXIT_DELAY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SecureMeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Secure Me."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate code
            if len(user_input[CONF_CODE]) < 4:
                errors[CONF_CODE] = "code_too_short"
            else:
                # Create entry
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title="Secure Me",
                    data=user_input,
                )

        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_CODE): str,
                vol.Optional(
                    CONF_EXIT_DELAY, default=DEFAULT_EXIT_DELAY
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=120)),
                vol.Optional(
                    CONF_ENTRY_DELAY, default=DEFAULT_ENTRY_DELAY
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return SecureMeOptionsFlow(config_entry)


class SecureMeOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Secure Me."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values
        current_code = self.config_entry.data.get(CONF_CODE, "")
        current_exit = self.config_entry.data.get(CONF_EXIT_DELAY, DEFAULT_EXIT_DELAY)
        current_entry = self.config_entry.data.get(CONF_ENTRY_DELAY, DEFAULT_ENTRY_DELAY)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_CODE, default=current_code): str,
                    vol.Optional(CONF_EXIT_DELAY, default=current_exit): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=120)
                    ),
                    vol.Optional(CONF_ENTRY_DELAY, default=current_entry): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=60)
                    ),
                }
            ),
        )
