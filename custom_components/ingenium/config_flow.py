"""Config flow for Ingenium integration."""
import json
import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_HOST
from ingeniumpy import IngeniumAPI

from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA_FIRST = vol.Schema({
    vol.Optional("mode", default="remote"): vol.In(["remote", "local"])
})

DATA_SCHEMA_LOCAL = vol.Schema({
    CONF_HOST: str
})

DATA_SCHEMA_REMOTE = vol.Schema({
    CONF_USERNAME: str,
    CONF_PASSWORD: str
})


async def validate_input(hass: core.HomeAssistant, data: Dict[str, Any]):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data[CONF_USERNAME], data[CONF_PASSWORD]
    # )

    api = IngeniumAPI()

    if CONF_USERNAME in data and CONF_PASSWORD in data:
        api.remote(data[CONF_USERNAME], data[CONF_PASSWORD])
    elif CONF_HOST in data:
        api.local(data[CONF_HOST])
    else:
        raise InvalidAuth

    try:
        result = await api.load(just_login=True, hass_integration=False)
    except TypeError:
        result = await api.load(just_login=True)
    if not result:
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": data[CONF_USERNAME] if CONF_USERNAME in data else data[CONF_HOST]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ingenium."""

    VERSION = 1

    async def async_step_user(self, user_input: Dict[str, Any] = None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            if "mode" in user_input:
                schema = DATA_SCHEMA_REMOTE if user_input["mode"] == "remote" else DATA_SCHEMA_LOCAL
                return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

            if CONF_HOST in user_input or (CONF_USERNAME in user_input and CONF_PASSWORD in user_input):
                try:
                    info = await validate_input(self.hass, user_input)

                    return self.async_create_entry(title=info["title"], data=user_input)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except InvalidAuth:
                    errors["base"] = "invalid_auth"
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA_FIRST, errors=errors)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
