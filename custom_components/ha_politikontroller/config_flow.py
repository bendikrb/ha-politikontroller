"""Config flow to configure the Politikontroller events integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from politikontroller_py.models.api import PoliceControlTypeEnum
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_RADIUS,
    CONF_USERNAME,
    UnitOfLength,
)
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
)
from homeassistant.util.unit_conversion import DistanceConverter

from .const import CONF_TYPE_FILTER, DEFAULT_RADIUS_IN_M, DOMAIN

if TYPE_CHECKING:
    from collections.abc import Mapping

    from homeassistant.data_entry_flow import FlowResult

# noinspection PyUnresolvedReferences
ENTRY_TYPES = [t.name.lower() for t in PoliceControlTypeEnum]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_LOCATION): selector.LocationSelector(
            selector.LocationSelectorConfig(radius=True, icon="mdi:police-badge")
        ),
    }
)

_LOGGER = logging.getLogger(__name__)


# noinspection PyTypeChecker
class PolitikontrollerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Politikontroller events config flow."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the start of the config flow."""
        if not user_input:
            suggested_values: Mapping[str, Any] = {
                CONF_LOCATION: {
                    CONF_LATITUDE: self.hass.config.latitude,
                    CONF_LONGITUDE: self.hass.config.longitude,
                    CONF_RADIUS: DEFAULT_RADIUS_IN_M,
                }
            }
            data_schema = self.add_suggested_values_to_schema(
                DATA_SCHEMA, suggested_values
            )
            return self.async_show_form(
                step_id="user",
                data_schema=data_schema,
            )

        username: str = user_input[CONF_USERNAME]
        password: str = user_input[CONF_PASSWORD]
        location: dict[str, Any] = user_input[CONF_LOCATION]
        latitude: float = location[CONF_LATITUDE]
        longitude: float = location[CONF_LONGITUDE]
        self._async_abort_entries_match(
            {
                CONF_USERNAME: username,
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: longitude,
            }
        )
        return self.async_create_entry(
            title=f"{username} ({latitude}, {longitude})",
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: longitude,
                CONF_RADIUS: DistanceConverter.convert(
                    location[CONF_RADIUS],
                    UnitOfLength.METERS,
                    UnitOfLength.KILOMETERS,
                ),
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


# noinspection PyTypeChecker
class OptionsFlow(config_entries.OptionsFlow):
    """Politikontroller config flow options handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = vol.Schema(
            {
                vol.Optional(
                    CONF_TYPE_FILTER,
                    default=self.config_entry.options.get(
                        CONF_TYPE_FILTER, []
                    ),
                ): SelectSelector(SelectSelectorConfig(
                    multiple=True,
                    options=ENTRY_TYPES,
                    translation_key=CONF_TYPE_FILTER,
                ))
            }
        )

        return self.async_show_form(step_id="init", data_schema=options)
