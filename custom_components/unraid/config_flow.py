"""Adds config flow for unRAID."""
from __future__ import annotations

import asyncio
import logging

from aiohttp.client_exceptions import ClientConnectorError
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import ATTR_NAME, CONF_HOST, CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

class unRAIDFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for unRAID."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize flow."""
        self._errors = {}

    async def async_step_user(self, user_input: ConfigType | None = None):
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._api_key = user_input[CONF_API_KEY]
            try:
                mac = await self.test_credentials(self._host, self._api_key)
            except (ApiError, ClientConnectorError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            except CannotGetMac:
                return self.async_abort(reason="device_unsupported")
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(format_mac(mac))
                self._abort_if_unique_id_configured({CONF_HOST: self._host})

                return self.async_create_entry(
                    title=self._host,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=""): str,
                    vol.Required(CONF_API_KEY, default=""): str,
                }
            ),
            errors=errors,
        )


    async def test_credentials(self, host, api_key):
        """Return true if credentials is valid."""
        try:
            client = UnraidClient(host, api_key)
            # client.poll_graphql('vars')
            return True
        except Exception:  # pylint: disable=broad-except
            pass
        return False
