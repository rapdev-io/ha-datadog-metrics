"""Tests for custom_components.rapdev.__init__"""

import pytest
from typing import Any

from custom_components.rapdev import async_setup, async_setup_entry, async_unload_entry
from custom_components.rapdev.const import DOMAIN


class FakeConfigEntry:
    """Minimal mock of ConfigEntry for vanilla pytest."""

    def __init__(self, data: dict[str, Any], entry_id: str = "test_entry_id") -> None:
        self.data = data
        self.entry_id = entry_id
        self.title = "Test Entry"
        self.domain = DOMAIN


class DummyServices:
    def __init__(self) -> None:
        self.registered = []

    def async_register(
        self, domain: str, name: str, callback: Any, schema: Any
    ) -> None:
        self.registered.append((domain, name))


class DummyHass:
    def __init__(self) -> None:
        self.data = {}
        self.services = DummyServices()


@pytest.fixture
def config_entry() -> FakeConfigEntry:
    return FakeConfigEntry(
        data={
            "host": "localhost",
            "port": 8125,
            "prefix": "hass",
        }
    )


@pytest.fixture
def hass() -> DummyHass:
    return DummyHass()


@pytest.mark.asyncio
async def test_async_setup_returns_true(hass: DummyHass) -> None:
    result = await async_setup(hass, {})  # type: ignore
    assert result is True


@pytest.mark.asyncio
async def test_async_setup_entry_stores_data_and_registers_service(
    hass: DummyHass, config_entry: FakeConfigEntry, monkeypatch: pytest.MonkeyPatch
) -> None:
    called_config = {}

    def fake_register_services(hass_arg, config_arg):
        nonlocal called_config
        called_config = config_arg

    # Patch the local reference *before* importing the function
    import custom_components.rapdev.__init__ as rapdev_init

    monkeypatch.setattr(rapdev_init, "register_services", fake_register_services)

    # Now import the function after patch
    result = await rapdev_init.async_setup_entry(hass, config_entry)  # type: ignore

    assert result is True
    assert DOMAIN in hass.data
    assert config_entry.entry_id in hass.data[DOMAIN]

    stored = hass.data[DOMAIN][config_entry.entry_id]
    assert stored == config_entry.data

    assert called_config == config_entry.data


@pytest.mark.asyncio
async def test_async_unload_entry_removes_stored_entry(
    hass: DummyHass, config_entry: FakeConfigEntry
) -> None:
    # Pre-populate hass.data
    hass.data[DOMAIN] = {
        config_entry.entry_id: {
            "host": "localhost",
            "port": 8125,
            "prefix": "hass",
        }
    }

    result = await async_unload_entry(hass, config_entry)  # type: ignore
    assert result is True
    assert config_entry.entry_id not in hass.data[DOMAIN]
