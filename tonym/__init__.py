"""The Tony M integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, SCAN_INTERVAL, STRAVA, WEEK, LWEEK, TIME, DIST, ELEV, DELTA

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tony M from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    coordinator = TonymDataUpdateCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class TonymDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Tonym data."""

    # All entities should read data from this coordinator's data
    # attribute, updated by the _async_update_data function

    def __init__(self, hass):
        """Initialize global tonym data updater."""

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data for Tony M."""

        # Create dictionary for ["data"] of coorindator in the format
        coord_data = dict()
        coord_data["name"] = "Tony Myatt"
        coord_data[STRAVA + WEEK + DIST] = 101.4
        coord_data[STRAVA + WEEK + DIST + DELTA] = 90.4
        coord_data[STRAVA + WEEK + TIME] = 10.5

        return coord_data

    def get_device(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "PLC")},
            entry_type=DeviceEntryType.SERVICE,
            name="Tony Myatt Strava",
            manufacturer="Strava",
            configuration_url=f"https://www.strava.com/",
        )
