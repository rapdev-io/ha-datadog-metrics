"""Service actions for sending metrics to datadog (via dogstatsd)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from datadog import initialize
from datadog.dogstatsd.base import statsd
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PREFIX
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .const import LOGGER as _LOGGER

if TYPE_CHECKING:
    from homeassistant.helpers.typing import ConfigType

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8125
DEFAULT_PREFIX = "hass"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Optional(CONF_PREFIX, default=DEFAULT_PREFIX): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the an async service example component."""
    conf = config[DOMAIN]
    host = conf[CONF_HOST]
    port = conf[CONF_PORT]
    prefix = conf[CONF_PREFIX]

    initialize(statsd_host=host, statsd_port=port)

    @callback
    def datadog_metric(call: ServiceCall) -> None:
        """Send metric to dogstatsd."""
        try:
            raw_tags = call.data.get("tags", {})

            if isinstance(raw_tags, dict):
                tags = [f"{k}:{v}" for k, v in raw_tags.items()]
            elif isinstance(raw_tags, list):
                # validate they are formatted in k:v style
                for kv_pair in raw_tags:
                    if len(kv_pair.split(":")) != 2:  # noqa: PLR2004
                        msg = f"improperly formatted tag: {kv_pair}"
                        raise ValueError(msg)
                tags = raw_tags

            metric = f"{prefix}.{call.data['metric']}"

            value = float(call.data["value"])
        except ValueError:
            _LOGGER.warning(
                "Issue preparing dogstatsd metric: %s", call.data, exc_info=True
            )
            return

        statsd.gauge(metric=metric, value=value, tags=tags)

        _LOGGER.debug("Sent metric %s: %s (tags: %s)", metric, value, tags)

    hass.services.async_register(
        DOMAIN,
        "datadog_metric",
        datadog_metric,
        vol.Schema(
            {
                vol.Required("metric"): cv.string,
                vol.Required("value"): vol.Schema(vol.Coerce(float)),
                vol.Optional("tags"): vol.Optional(
                    vol.Schema(vol.Any(dict[str, str], list[str]))
                ),
            }
        ),
    )

    return True
