"""Services definitions."""

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from datadog import initialize
from datadog.dogstatsd.base import statsd
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .const import LOGGER as _LOGGER


def register_services(hass: HomeAssistant, config: Mapping[str, Any]) -> None:
    """Register datadog service."""
    host = config["host"]
    port = config["port"]
    prefix = config["prefix"]

    initialize(statsd_host=host, statsd_port=port)

    @callback
    def datadog_metric(call: ServiceCall) -> None:
        """Send metric to dogstatsd."""
        try:
            raw_tags = call.data.get("tags", {})
            tags = (
                [f"{k}:{v}" for k, v in raw_tags.items()]
                if isinstance(raw_tags, dict)
                else raw_tags
            )
            for kv_pair in tags:
                if len(kv_pair.split(":")) != 2:  # noqa: PLR2004
                    raise ValueError(f"improperly formatted tag: {kv_pair}")

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
                vol.Required("value"): vol.Coerce(float),
                vol.Optional("tags"): vol.Any({str: str}, [str]),
            }
        ),
    )
