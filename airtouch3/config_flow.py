"""Config flow for Air Touch 3."""
from airtouch3 import AirTouch3
from airtouch3 import AT3CommsStatus
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_flow
from homeassistant.const import CONF_HOST

from .const import DOMAIN

DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class AirtouchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Airtouch3 config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        errors = {}

        host = user_input[CONF_HOST]
        self._async_abort_entries_match({CONF_HOST: host})

        at3 = AirTouch3(host)
        at3.UpdateStatus()
        airtouch_has_groups = bool(
            at3.comms_status == AT3CommsStatus.OK and len(at3.groups) > 0
        )

        if at3.comms_status != AT3CommsStatus.OK:
            errors["base"] = "cannot_connect"
        elif not airtouch_has_groups:
            errors["base"] = "no_units"

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors=errors
            )

        return self.async_create_entry(
            title=user_input[CONF_HOST],
            data={
                CONF_HOST: user_input[CONF_HOST],
            },
        )
