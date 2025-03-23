"""__init__.py tests."""

from collections.abc import Callable
from typing import Any

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PREFIX

from custom_components.rapdev import DOMAIN, async_setup


class DummyServicesRegistry:
    """A dummy services registry to simulate Home Assistant's service registration."""

    def __init__(self) -> None:
        """Initialize the dummy services registry."""
        self.registered_services: dict[tuple[str, str], Callable] = {}

    def async_register(
        self,
        domain: str,
        service: str,
        callback: Callable,
        schema: Any,  # noqa: ARG002
    ) -> None:
        """
        Simulate asynchronous service registration by storing the callback.

        Args:
            domain (str): The domain under which the service is registered.
            service (str): The service name.
            callback (Callable): The callback to be executed.
            schema (Any): The validation schema for the service call.

        """
        self.registered_services[(domain, service)] = callback


class DummyHass:
    """A dummy Home Assistant instance for testing purposes."""

    def __init__(self) -> None:
        """Initialize the dummy Home Assistant instance."""
        self.data: dict[Any, Any] = {}
        self.services = DummyServicesRegistry()


class DummyServiceCall:
    """A dummy ServiceCall object to simulate a service call in Home Assistant."""

    def __init__(self, data: dict[str, Any]) -> None:
        """
        Initialize the dummy ServiceCall.

        Args:
            data (dict[str, Any]): The data associated with the service call.
        """
        self.data = data


@pytest.fixture
def hass() -> DummyHass:
    """
    Provide a dummy Home Assistant instance.

    Returns:
        DummyHass: A dummy Home Assistant instance.
    """
    return DummyHass()


@pytest.fixture
def config() -> dict[str, Any]:
    """
    Provide a default configuration for the tests.

    Returns:
        dict[str, Any]: A configuration dictionary.
    """
    return {
        DOMAIN: {
            CONF_HOST: "localhost",
            CONF_PORT: 8125,
            CONF_PREFIX: "hass",
        }
    }


@pytest.mark.asyncio
async def test_async_setup_registers_service(
    hass: DummyHass, config: dict[str, Any]
) -> None:
    """
    Test that async_setup returns True and registers the datadog_metric service.

    Args:
        hass (DummyHass): The dummy Home Assistant instance.
        config (dict[str, Any]): The configuration dictionary.
    """
    result = await async_setup(hass, config)  # type: ignore
    assert result is True
    assert (DOMAIN, "datadog_metric") in hass.services.registered_services


@pytest.mark.asyncio
async def test_datadog_metric_with_dict_tags(
    hass: DummyHass, config: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Test that a valid service call with tags as a dict converts tags properly and
    calls statsd.gauge with the correct parameters.

    Args:
        hass (DummyHass): The dummy Home Assistant instance.
        config (dict[str, Any]): The configuration dictionary.
        monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.
    """
    await async_setup(hass, config)  # type: ignore
    service_callback = hass.services.registered_services[(DOMAIN, "datadog_metric")]

    called_params: dict[str, Any] = {}

    def fake_gauge(metric: str, value: float, tags: list[str]) -> None:
        """
        Fake gauge function to capture the parameters passed.

        Args:
            metric (str): The metric name.
            value (float): The value of the metric.
            tags (list[str]): The tags associated with the metric.
        """
        called_params["metric"] = metric
        called_params["value"] = value
        called_params["tags"] = tags

    monkeypatch.setattr("datadog.dogstatsd.base.statsd.gauge", fake_gauge)

    service_call = DummyServiceCall(
        {
            "metric": "cpu_usage",
            "value": "75",  # string that should convert to float 75.0
            "tags": {"host": "server1", "env": "prod"},
        }
    )
    service_callback(service_call)

    assert called_params["metric"] == "hass.cpu_usage"
    assert called_params["value"] == 75.0
    assert sorted(called_params["tags"]) == sorted(["host:server1", "env:prod"])


@pytest.mark.asyncio
async def test_datadog_metric_with_list_tags(
    hass: DummyHass, config: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Test that a valid service call with tags provided as a list (with proper k:v format)
    is passed directly to statsd.gauge.

    Args:
        hass (DummyHass): The dummy Home Assistant instance.
        config (dict[str, Any]): The configuration dictionary.
        monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.
    """
    await async_setup(hass, config)  # type: ignore
    service_callback = hass.services.registered_services[(DOMAIN, "datadog_metric")]

    called_params: dict[str, Any] = {}

    def fake_gauge(metric: str, value: float, tags: list[str]) -> None:
        """
        Fake gauge function to capture the parameters passed.

        Args:
            metric (str): The metric name.
            value (float): The value of the metric.
            tags (list[str]): The tags associated with the metric.
        """
        called_params["metric"] = metric
        called_params["value"] = value
        called_params["tags"] = tags

    monkeypatch.setattr("datadog.dogstatsd.base.statsd.gauge", fake_gauge)

    service_call = DummyServiceCall(
        {
            "metric": "memory_usage",
            "value": "45",
            "tags": ["host:server2", "env:staging"],
        }
    )
    service_callback(service_call)

    assert called_params["metric"] == "hass.memory_usage"
    assert called_params["value"] == 45.0  # noqa: PLR2004
    assert sorted(called_params["tags"]) == sorted(["host:server2", "env:staging"])


@pytest.mark.asyncio
async def test_datadog_metric_invalid_tag_format(
    hass: DummyHass,
    config: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test that a service call with improperly formatted list tags (without colon)
    results in no call to statsd.gauge and a warning being logged.

    Args:
        hass (DummyHass): The dummy Home Assistant instance.
        config (dict[str, Any]): The configuration dictionary.
        monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.
        caplog (pytest.LogCaptureFixture): The fixture for capturing log output.
    """
    await async_setup(hass, config)  # type: ignore
    service_callback = hass.services.registered_services[(DOMAIN, "datadog_metric")]

    gauge_called = False

    def fake_gauge(metric: str, value: float, tags: list[str]) -> None:
        """
        Fake gauge function that sets a flag when called.

        Args:
            metric (str): The metric name.
            value (float): The value of the metric.
            tags (list[str]): The tags associated with the metric.
        """
        nonlocal gauge_called
        gauge_called = True

    monkeypatch.setattr("datadog.dogstatsd.base.statsd.gauge", fake_gauge)

    service_call = DummyServiceCall(
        {
            "metric": "disk_usage",
            "value": "55",
            "tags": ["hostserver3"],
        }
    )
    service_callback(service_call)

    assert gauge_called is False
    assert "Issue preparing dogstatsd metric" in caplog.text


@pytest.mark.asyncio
async def test_datadog_metric_invalid_value(
    hass: DummyHass,
    config: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Test that a service call with an invalid (non-numeric) value does not call statsd.gauge
    and logs a warning.

    Args:
        hass (DummyHass): The dummy Home Assistant instance.
        config (dict[str, Any]): The configuration dictionary.
        monkeypatch (pytest.MonkeyPatch): The monkeypatch fixture.
        caplog (pytest.LogCaptureFixture): The fixture for capturing log output.
    """
    await async_setup(hass, config)  # type: ignore
    service_callback = hass.services.registered_services[(DOMAIN, "datadog_metric")]

    gauge_called = False

    def fake_gauge(metric: str, value: float, tags: list[str]) -> None:
        """
        Fake gauge function that sets a flag when called.

        Args:
            metric (str): The metric name.
            value (float): The value of the metric.
            tags (list[str]): The tags associated with the metric.
        """
        nonlocal gauge_called
        gauge_called = True

    monkeypatch.setattr("datadog.dogstatsd.base.statsd.gauge", fake_gauge)

    service_call = DummyServiceCall(
        {
            "metric": "network_latency",
            "value": "not_a_number",
            "tags": {"host": "server4"},
        }
    )
    service_callback(service_call)

    assert gauge_called is False
    assert "Issue preparing dogstatsd metric" in caplog.text
