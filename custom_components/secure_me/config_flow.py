"""Config flow for Secure Me integration."""
# VERSION = "1.5.4"

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_CODE,
    CONF_EXIT_DELAY,
    CONF_ENTRY_DELAY,
    CONF_TRIGGER_TIME,
    DEFAULT_EXIT_DELAY,
    DEFAULT_ENTRY_DELAY,
    DEFAULT_TRIGGER_TIME,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CODE, default=""): str,
        vol.Optional(CONF_EXIT_DELAY, default=DEFAULT_EXIT_DELAY): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=300)
        ),
        vol.Optional(CONF_ENTRY_DELAY, default=DEFAULT_ENTRY_DELAY): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=300)
        ),
        vol.Optional(CONF_TRIGGER_TIME, default=DEFAULT_TRIGGER_TIME): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=3600)
        ),
    }
)


class SecureMeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Secure Me."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        return self.async_create_entry(
            title="Secure Me",
            data=user_input,
        )
