"""Tests for services.py"""

import pytest
from typing import Any

from custom_components.rapdev.services import register_services
from custom_components.rapdev.const import DOMAIN


class DummyServiceCall:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data


class DummyServices:
    def __init__(self) -> None:
        self.registered = {}

    def async_register(
        self, domain: str, name: str, callback: Any, schema: Any
    ) -> None:
        self.registered[(domain, name)] = callback


class DummyHass:
    def __init__(self) -> None:
        self.services = DummyServices()


@pytest.fixture
def hass() -> DummyHass:
    return DummyHass()


@pytest.fixture
def config() -> dict[str, Any]:
    return {"host": "localhost", "port": 8125, "prefix": "hass"}


@pytest.mark.asyncio
async def test_register_services_and_send_metric(
    hass: DummyHass, config: dict[str, Any], monkeypatch: pytest.MonkeyPatch
):
    """Test metric is sent correctly."""
    called = {}

    def fake_gauge(metric: str, value: float, tags: list[str]) -> None:
        called["metric"] = metric
        called["value"] = value
        called["tags"] = tags

    monkeypatch.setattr("datadog.dogstatsd.base.statsd.gauge", fake_gauge)

    register_services(hass, config)  # type: ignore

    assert (DOMAIN, "datadog_metric") in hass.services.registered
    service = hass.services.registered[(DOMAIN, "datadog_metric")]

    service(
        DummyServiceCall(
            {
                "metric": "cpu.usage",
                "value": "75",
                "tags": {"host": "node1", "env": "prod"},
            }
        )
    )

    assert called["metric"] == "hass.cpu.usage"
    assert called["value"] == 75.0
    assert sorted(called["tags"]) == sorted(["host:node1", "env:prod"])


@pytest.mark.asyncio
async def test_metric_with_invalid_tag_format(
    hass: DummyHass,
    config: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
    """Test invalid tags (missing colon) log a warning and do not call gauge."""
    called = False

    def fake_gauge(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("datadog.dogstatsd.base.statsd.gauge", fake_gauge)

    register_services(hass, config)  # type: ignore
    service = hass.services.registered[(DOMAIN, "datadog_metric")]

    service(
        DummyServiceCall(
            {
                "metric": "disk.usage",
                "value": "55",
                "tags": ["badtag"],
            }
        )
    )

    assert not called
    assert "Issue preparing dogstatsd metric" in caplog.text


@pytest.mark.asyncio
async def test_metric_with_invalid_value(
    hass: DummyHass,
    config: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
    """Test invalid value logs a warning and does not call gauge."""
    called = False

    def fake_gauge(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("datadog.dogstatsd.base.statsd.gauge", fake_gauge)

    register_services(hass, config)  # type: ignore
    service = hass.services.registered[(DOMAIN, "datadog_metric")]

    service(
        DummyServiceCall(
            {
                "metric": "net.latency",
                "value": "not_a_number",
                "tags": {"host": "x"},
            }
        )
    )

    assert not called
    assert "Issue preparing dogstatsd metric" in caplog.text
