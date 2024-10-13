"""The Strava integration."""

from __future__ import annotations

from datetime import datetime as dt
import logging
import pprint

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from . import config_flow
from .const import (
    DOMAIN,
    GEAR_SERVICE_KEYS,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    SCAN_INTERVAL,
)
from .strava_api import StravaAPI

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.SENSOR]  # , Platform.DATETIME


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Strava from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # OAuth Stuff
    try:
        implementation = (
            await config_entry_oauth2_flow.async_get_config_entry_implementation(
                hass, entry
            )
        )
    except ValueError:
        implementation = config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            entry.data[CONF_CLIENT_ID],
            entry.data[CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        )

        config_flow.OAuth2FlowHandler.async_register_implementation(
            hass, implementation
        )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)

    await session.async_ensure_token_valid()

    # async def async_update_data():
    #    strava = StravaAPI(session)
    #    return await strava.fetch_strava_data()

    coordinator = StravaCoordinator(hass, session)

    #    hass,
    #    _LOGGER,
    #    name="Strava Ride",
    #    update_method=async_update_data,
    #    update_interval=SCAN_INTERVAL,
    # )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class StravaCoordinator(DataUpdateCoordinator):
    """Class to manage strava data fetching and gear management."""

    _device: DeviceInfo

    def __init__(self, hass, session) -> None:
        """Initialize strava coorindator with oauth session."""

        super().__init__(
            hass,
            _LOGGER,
            name="Strava Ride",
            update_interval=SCAN_INTERVAL,
        )

        self._strava_api = StravaAPI(session)
        self._device = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, session.config_entry.data[CONF_CLIENT_ID])},
            manufacturer="Strava",
            model="Ride Statistics",
            name=self.name,
        )

        current_state = self.hass.states.get("datetime.propel_2024_service_dist_1_date")
        pprint.pprint(current_state)

    def get_device(self):
        return self._device

    async def _async_update_data(self):
        return await self._strava_api.fetch_strava_data()

    async def reset_gear_service(self, service_key):
        await self._strava_api.set_gear_service_date(
            service_key, dt.now(tz=dt_util.get_default_time_zone())
        )
        self.async_request_refresh()
