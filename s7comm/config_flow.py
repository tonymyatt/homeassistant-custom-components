"""Config flow for Air Touch 3."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST

from .const import DOMAIN
from .s7comm import S7Comm

DATA_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class S7CommConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an S7Comm config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        errors = {}

        # Ask the user for the host name
        host = user_input[CONF_HOST]
        self._async_abort_entries_match({CONF_HOST: host})

        # Connect to the S7 PLC and request an update
        s7comm = S7Comm(host)
        s7comm.get_cpu_state()

        # Check if we connected, if not, error message
        if not s7comm.comms_status:
            errors["base"] = "cannot_connect"

        # Show errors to user, exiting
        if errors:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors=errors
            )

        # All good and connected, create entry
        return self.async_create_entry(
            title="Step 7 PLC (" + user_input[CONF_HOST] + ")",
            data={
                CONF_HOST: user_input[CONF_HOST],
            },
        )
