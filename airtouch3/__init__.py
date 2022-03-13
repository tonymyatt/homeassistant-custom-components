"""The Air Touch 3 integration."""
from __future__ import annotations
import logging

from airtouch3 import AirTouch3
from airtouch3 import AT3CommsStatus

from homeassistant.components.climate import SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Air Touch 3 from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    hass.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]
    at3 = AirTouch3(host)
    success = at3.UpdateStatus()
    if not success:
        raise ConfigEntryNotReady
    coordinator = AT3DataUpdateCoordinator(hass, at3)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class AT3DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Airtouch3 data."""

    def __init__(self, hass, at3):
        """Initialize global Airtouch data updater."""
        self.at3 = at3

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from Airtouch3."""
        self.at3.UpdateStatus()
        self.at3.PrintStatus()
        if self.at3.comms_status != AT3CommsStatus.OK:
            raise UpdateFailed("Airtouch connection issue")
        return {
            "acs": [
                {
                    "number": ac.number,
                    "name": ac.name,
                    "is_on": ac.is_on,
                    "mode": ac.mode,
                    "temperature": ac.temperature,
                }
                for ac in self.at3.acUnits.values()
            ],
            "groups": [
                {
                    "number": group.number,
                    "name": group.name,
                    "is_on": group.is_on,
                    "mode": group.mode,
                    "percent": group.open_percent,
                    "temperature": group.temperature,
                }
                for group in self.at3.groups.values()
            ],
        }
