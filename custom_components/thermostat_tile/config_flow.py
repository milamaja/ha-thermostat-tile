"""Config flow for Thermostat Tile: one click to add, temperatures under Configure."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig, NumberSelectorMode, TimeSelector

from .const import (
    CONF_ECO_TEMPERATURE,
    CONF_EVENING_END,
    CONF_EVENING_HEAT_TEMPERATURE,
    CONF_EVENING_START,
    CONF_HEAT_TEMPERATURE,
    DEFAULT_EVENING_END,
    DEFAULT_EVENING_START,
    DOMAIN,
    NAME,
)


class ThermostatTileConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add the Thermostat Tile card to the dashboards."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm and create the entry."""
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """The temperatures the Heat and Eco buttons set."""
        return ThermostatTileOptionsFlow()


class ThermostatTileOptionsFlow(OptionsFlow):
    """Heat, evening Heat and Eco temperature; leave a field empty to keep the target as it is."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        unit = self.hass.config.units.temperature_unit
        number = NumberSelector(
            NumberSelectorConfig(min=5, max=35, step=0.5, unit_of_measurement=unit, mode=NumberSelectorMode.BOX)
        )
        schema = vol.Schema(
            {
                vol.Optional(CONF_HEAT_TEMPERATURE): number,
                vol.Optional(CONF_EVENING_HEAT_TEMPERATURE): number,
                vol.Optional(CONF_EVENING_START, default=DEFAULT_EVENING_START): TimeSelector(),
                vol.Optional(CONF_EVENING_END, default=DEFAULT_EVENING_END): TimeSelector(),
                vol.Optional(CONF_ECO_TEMPERATURE): number,
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, self.config_entry.options),
        )
