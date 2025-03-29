"""Config flow."""

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8125
DEFAULT_PREFIX = "hass"


class DatadogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Datadog Metrics integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Mapping[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Config flow."""
        if user_input is not None:
            return self.async_create_entry(title="Datadog", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "host",
                        default=DEFAULT_HOST,
                        msg="host message",
                        description="host description",
                    ): str,
                    vol.Required("port", default=DEFAULT_PORT): int,
                    vol.Required("prefix", default=DEFAULT_PREFIX): str,
                }
            ),
        )
