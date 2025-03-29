"""Tests for config_flow.py"""

import pytest

from custom_components.rapdev.config_flow import DatadogConfigFlow
from custom_components.rapdev.const import DOMAIN

from homeassistant.data_entry_flow import FlowResultType

DEFAULT_INPUT = {
    "host": "localhost",
    "port": 8125,
    "prefix": "hass",
}


@pytest.mark.asyncio
async def test_user_step_shows_form() -> None:
    """Test that the user step shows a form when no input is given."""
    flow = DatadogConfigFlow()
    result = await flow.async_step_user(user_input=None)

    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert "data_schema" in result


@pytest.mark.asyncio
async def test_user_step_creates_entry() -> None:
    """Test that the user step creates an entry with valid input."""
    flow = DatadogConfigFlow()
    result = await flow.async_step_user(user_input=DEFAULT_INPUT)

    assert result.get("type") == FlowResultType.CREATE_ENTRY
    assert result.get("title") == "Datadog"
    assert result.get("data") == DEFAULT_INPUT
