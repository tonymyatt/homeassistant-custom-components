"""The Air Touch 3 integration."""
from __future__ import annotations
import logging

from airtouch3 import AirTouch3
from airtouch3 import AT3CommsStatus, AT3Command, AT3AcFanSpeed, AT3AcMode

from homeassistant.components.climate import SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.FAN]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Air Touch 3 from a config entry."""
    # Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    hass.data.setdefault(DOMAIN, {})
    host = entry.data[CONF_HOST]
    at3 = AirTouch3(host)
    success = at3.update_status()
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

    CMD = "Command"
    IDX = "Index"
    FAN = "Fan"
    MODE = "Mode"
    CMD_AC_TOGGLE = "AT3AcUnit.toggle"
    CMD_AC_TEMP_INC = "AT3AcUnit.temperature_inc"
    CMD_AC_TEMP_DEC = "AT3AcUnit.temperature_dec"
    CMD_AC_SET_FAN = "AT3AcUnit.set_fan_speed"
    CMD_AC_SET_MODE = "AT3AcUnit.set_mode"
    CMD_GRP_TOGGLE = "AT3Group.toggle"
    CMD_GRP_TOGGLE_MODE = "AT3Group.toggle_mode"
    CMD_GRP_POSN_INC = "AT3Group.position_inc"
    CMD_GRP_POSN_DEC = "AT3Group.position_dec"

    def __init__(self, hass, at3):
        """Initialize global Airtouch data updater."""
        self.at3: AirTouch3 = at3

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    def issue_command(self, cmd, **kwargs):
        print(f"Issuing command {cmd} with args {kwargs}")
        cmd = kwargs.get(self.CMD)
        idx = kwargs.get(self.IDX)
        if cmd is None or idx is None:
            return None

        if cmd == self.CMD_AC_TOGGLE:
            ac_unit = int(idx)
            self.at3.toggle_ac_unit(ac_unit)

        if cmd == self.CMD_AC_TEMP_INC:
            ac_unit = int(idx)
            self.at3.toggle_temperature_ac_unit(ac_unit, AT3Command.INCREMENT)

        if cmd == self.CMD_AC_TEMP_DEC:
            ac_unit = int(idx)
            self.at3.toggle_temperature_ac_unit(ac_unit, AT3Command.DECREMENT)

        if cmd == self.CMD_AC_SET_FAN:
            ac_unit = int(idx)
            speed = AT3AcFanSpeed(kwargs.get(self.FAN))
            self.at3.set_fan_speed_ac_unit(ac_unit, speed)

        if cmd == self.CMD_AC_SET_MODE:
            ac_unit = int(idx)
            mode = AT3AcMode(kwargs.get(self.MODE))
            self.at3.set_mode_ac_unit(ac_unit, mode)

        self.data = self._create_data_dict()

    async def _async_update_data(self):
        """Fetch data from Airtouch3."""
        self.at3.update_status()
        if self.at3.comms_status != AT3CommsStatus.OK:
            raise UpdateFailed("Airtouch connection issue")

        return self._create_data_dict()

    def _create_data_dict(self):

        data = {
            "name": self.at3.name,
            "id": self.at3.id,
            "ac_units": {
                ac.number: {
                    "name": ac.name,
                    "number": ac.number,
                    "brand": ac.brand,
                    "fan_speed": ac.fan_speed,
                    "has_error": ac.has_error,
                    "is_on": ac.is_on,
                    "mode": ac.mode,
                    "temperature": ac.temperature,
                    "temperature_sp": ac.temperature_sp,
                }
                for ac in self.at3.ac_units.values()
            },
            "groups": {
                gr.number: {
                    "name": gr.name,
                    "number": gr.number,
                    "is_on": gr.is_on,
                    "mode": gr.mode,
                    "open_percent": gr.open_percent,
                    "temperature": gr.temperature,
                    "temperature_sp": gr.temperature_sp,
                }
                for gr in self.at3.groups.values()
            },
            "sensors": {
                se.name: {
                    "name": se.name,
                    "temperature": se.temperature,
                    "available": se.available,
                    "low_battery": se.low_battery,
                }
                for se in self.at3.sensors.values()
            },
        }

        return data
