"""The Tony M integration."""
from __future__ import annotations
import logging
from homeassistant.components.tonym.strava_tonym import StravaTonym

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
        self._strava_tonym = StravaTonym()

    async def _async_update_data(self):
        """Fetch data for Tony M."""

        # Create dictionary for ["data"] of coorindator in the format
        coord_data = dict()
        coord_data["name"] = "Tony Myatt"

        self._strava_tonym.read_strava()
        stats = self._strava_tonym.calc_weekly_strava_stats()

        # print(f"Cycling Last Week Distance: {last_week.distance:0.1f}km")
        # print(f"Cycling Last Week Distance delta: {last_week.distance_delta:0.0f}%")
        # print(f"Cycling Last Week Time: {last_week.time:0.1f}hrs")
        # print(f"Cycling Last Week Time delta: {last_week.time_delta:0.0f}%")
        # print(f"Cycling Last Week Elevation: {last_week.elevation:0.0f}m")
        # print(f"Cycling Last Week Climbing: {last_week.climbing:0.1f}%")

        # print(f"Cycling This Week Distance: {this_week.distance:0.1f}km")
        # print(f"Cycling This Week Distance delta: {this_week.distance_delta:0.0f}%")
        # print(f"Cycling This Week Time: {this_week.time:0.1f}hrs")
        # print(f"Cycling This Week Time delta: {this_week.time_delta:0.0f}%")
        # print(f"Cycling This Week Elevation: {this_week.elevation:0.0f}m")
        # print(f"Cycling This Week Climbing: {this_week.climbing:0.1f}%")

        coord_data[STRAVA + WEEK + DIST] = stats["this_week"].distance
        coord_data[STRAVA + WEEK + DIST + DELTA] = stats["this_week"].distance_delta
        coord_data[STRAVA + WEEK + TIME] = stats["this_week"].time

        coord_data[STRAVA + LWEEK + DIST] = stats["last_week"].distance
        coord_data[STRAVA + LWEEK + DIST + DELTA] = stats["last_week"].distance_delta
        coord_data[STRAVA + LWEEK + TIME] = stats["last_week"].time

        return coord_data

    def get_device(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "PLC")},
            entry_type=DeviceEntryType.SERVICE,
            name="Tony Myatt Strava",
            manufacturer="Strava",
            configuration_url=f"https://www.strava.com/",
        )
