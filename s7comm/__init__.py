"""The Step7 PLC integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL, HA_COVER_ENTITIES, HA_WATERING_AREAS
from .s7comm import S7Addr, S7Comm, S7Bool, S7Word

_LOGGER = logging.getLogger(__name__)

# Sensor for numerics, binary sensor for booleans
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.SWITCH,
    Platform.NUMBER,
]


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

    def get_bool(self, s7addr: S7Bool):
        """Read the boolean value of the supplied S7Addr"""
        db_data = self.data[f"DB{s7addr.db}"]
        return s7addr.get_bool(db_data)

    def get_int(self, s7addr: S7Word):
        """Read the integer value of the supplied S7Addr"""
        db_data = self.data[f"DB{s7addr.db}"]
        return s7addr.get_int(db_data)

    async def write_int(self, s7addr: S7Addr, value: int):
        """Write the given integer to the S7Addr"""
        self.s7comm.write_int(s7addr, value)

    def register_dbs(self):
        # Register all the cover entities with the s7comm driver, this might happen in mutiple entities but
        # better to do muitple times as no garrantee of the order of setup of the entities
        [
            self.s7comm.register_db(desc.s7datablock, 0, desc.s7readbytes)
            for desc in HA_COVER_ENTITIES
        ]
        [
            self.s7comm.register_db(desc.s7datablock, 0, desc.s7readbytes)
            for desc in HA_WATERING_AREAS
        ]

    async def _async_update_data(self):
        """Fetch data from Step 7 CPU."""

        coord_data = {}

        # Update and make sure we are still connected at end of update
        self.s7comm.update_dbs()

        coord_data["COMMS_STATUS"] = self.s7comm.comms_status == False
        if not self.s7comm.comms_status:
            raise UpdateFailed("Step7 PLC connection issue")

        # Create dictionary for ["data"] of coorindator in the format
        coord_data["CPU_STATE"] = self.s7comm.get_cpu_state() == "Run"
        db_data = self.s7comm.get_db_data()
        for db_number in db_data:
            coord_data[f"DB{db_number}"] = db_data[db_number]["data"]

        return coord_data

    def get_device(self):
        return DeviceInfo(
            identifiers={(DOMAIN, "PLC")},
            name="Home PLC",
            manufacturer="Siemens S7/1200",
            model="tonym",
        )
