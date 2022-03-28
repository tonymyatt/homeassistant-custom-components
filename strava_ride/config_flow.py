"""Config flow for Strava Home Assistant."""
from __future__ import annotations

# generic imports
import logging
from typing import Any
import voluptuous as vol

# HASS imports
from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.network import get_url, NoURLAvailableError
from homeassistant.data_entry_flow import FlowResult

# custom module imports
from .const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    CONF_CALLBACK_URL,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Strava."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        return self.async_create_entry(
            title="Strava Integration", data={"Source": "Strava"}
        )


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Strava Home Assistant OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": "activity:read",
            "approval_prompt": "force",
            "response_type": "code",
        }

    async def async_step_renew_webhook_subscription(self, data):
        _LOGGER.debug("renew webhook subscription")
        return

    async def async_step_get_oauth_info(self, user_input=None):
        """Ask user to provide Strava API Credentials"""
        data_schema = {
            vol.Required(CONF_CLIENT_ID): str,
            vol.Required(CONF_CLIENT_SECRET): str,
        }

        assert self.hass is not None

        if self.hass.config_entries.async_entries(self.DOMAIN):
            return self.async_abort(reason="already_configured")

        try:
            get_url(self.hass, allow_internal=False, allow_ip=False)
        except NoURLAvailableError:
            return self.async_abort(reason="no_public_url")

        if user_input is not None:
            config_entry_oauth2_flow.async_register_implementation(
                self.hass,
                DOMAIN,
                config_entry_oauth2_flow.LocalOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                    OAUTH2_AUTHORIZE,
                    OAUTH2_TOKEN,
                ),
            )
            return await self.async_step_pick_implementation()

        return self.async_show_form(
            step_id="get_oauth_info", data_schema=vol.Schema(data_schema)
        )

    async def async_oauth_create_entry(self, data: dict) -> dict:
        data[
            CONF_CALLBACK_URL
        ] = f"{get_url(self.hass, allow_internal=False, allow_ip=False)}/api/strava/webhook"
        data[CONF_CLIENT_ID] = self.flow_impl.client_id
        data[CONF_CLIENT_SECRET] = self.flow_impl.client_secret

        return self.async_create_entry(title=self.flow_impl.name, data=data)

    async_step_user = async_step_get_oauth_info
