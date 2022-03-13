"""The Step7 PLC integration."""
from __future__ import annotations
import logging

from homeassistant.components.sensor import SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .s7comm import S7Comm, S7Addr

_LOGGER = logging.getLogger(__name__)

# Sensor for numerics, binary sensor for booleans
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.COVER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Step7 PLC from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]

    s7comm = S7Comm(host)
    s7comm.get_cpu_state()
    if not s7comm.comms_status:
        raise ConfigEntryNotReady

    coordinator = S7CommDataUpdateCoordinator(hass, s7comm)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class S7CommDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching S7 PLC data."""

    # All entities should read data from this coordinator's data
    # attribute, updated by the _async_update_data function

    def __init__(self, hass, s7comm: S7Comm):
        """Initialize global s7comm data updater."""
        self.s7comm: S7Comm = s7comm

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def write_db(self, s7addr: S7Addr, value):
        # TODO Implementation required
        print(f"Write {s7addr.type} {s7addr.db} {s7addr.byte} {s7addr.bit} set to "+str(value))

    async def _async_update_data(self):
        """Fetch data from Step 7 CPU."""

        # Update and make sure we are still connected at end of update
        self.s7comm.update_dbs()
        if not self.s7comm.comms_status:
            raise UpdateFailed("Step7 PLC connection issue")

        # Create dictionary for ["data"] of coorindator in the format
        # ["data"] = ["CPU_STATE": "Run/Stop", "DB0": bin_data]
        coord_data = {"CPU_STATE": self.s7comm.get_cpu_state()}
        db_data = self.s7comm.get_db_data()
        for db_number in db_data:
            coord_data[f"DB{db_number}"] = db_data[db_number]["data"]

        return coord_data

    def get_device(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "PLC")},
            name="Home PLC",
            manufacturer="Siemens",
            model="S7/1200",
        )
