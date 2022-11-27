"""Support for reading boolean values as digital_sensors from S7 PLC."""
from collections import MutableMapping
from enum import Enum
import logging

from homeassistant.components.cover import (
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverDeviceClass,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .s7comm import S7Bool, S7Comm, S7DWord, S7Word

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Step 7 PLC entities."""
    _LOGGER.debug("Setting up Step7 PLC Digital Sensor entities...")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    coordinator.s7comm.register_db(204, 0, 36)  # Herb Garden Valve
    coordinator.s7comm.register_db(203, 0, 36)  # Orchard Valve
    coordinator.s7comm.register_db(205, 0, 36)  # Downpipe Valve
    coordinator.s7comm.register_db(30, 0, 36)  # Front Yard Valve
    coordinator.s7comm.register_db(31, 0, 36)  # Front Hose Valve
    coordinator.s7comm.register_db(44, 0, 36)  # Front Hose Valve
    coordinator.s7comm.register_db(9, 0, 20)  # Nerrilee Garage Door
    coordinator.s7comm.register_db(10, 0, 20)  # Tony Garage Door

    # Now we have told the coorindator about what DB's to load
    # wait until the next update before we start adding entities
    # this will mean DB data is available from the time the entities
    # are loaded into HASS
    await coordinator.async_config_entry_first_refresh()

    new_entities = []
    entity = S7Valve(coordinator, "Herb Garden Valve", 204)
    new_entities.append(entity)
    entity = S7Valve(coordinator, "Orchard Valve", 203)
    new_entities.append(entity)
    entity = S7Valve(coordinator, "Downpipe Valve", 205)
    new_entities.append(entity)
    entity = S7Valve(coordinator, "Front Garden Valve", 30)
    new_entities.append(entity)
    entity = S7Valve(coordinator, "Front Hose Valve", 31)
    new_entities.append(entity)
    entity = S7Valve(coordinator, "Back Hose Valve", 44)
    new_entities.append(entity)

    entity = S7HaCoverGarage(coordinator, "Nerrilee Garage Door", 9)
    new_entities.append(entity)
    entity = S7HaCoverGarage(coordinator, "Tony Garage Door", 10)
    new_entities.append(entity)

    async_add_entities(new_entities)


class S7Mode(Enum):
    AUTO = 0
    CLOSE = 1
    OPEN = 2


class S7Valve(CoordinatorEntity, CoverEntity):
    """Valve device in a S7 PLC."""

    def __init__(self, coordinator, name: str, db_number: int) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._db_number = db_number
        self._s7_closed = S7Bool(db_number, 14, 5)
        self._s7_opened = S7Bool(db_number, 14, 6)
        self._s7_man_open = S7Bool(db_number, 16, 2)
        self._s7_open_tday = S7DWord(db_number, 20)
        self._s7_open_yday = S7DWord(db_number, 24)
        # self._s7_mode = S7Word(db_number, 16)

        # Rely on the parent class implementation for these attributes
        self._attr_name = name
        self._attr_icon = "mdi:pipe-valve"
        self._attr_device_class = CoverDeviceClass.DAMPER
        self._attr_supported_features = SUPPORT_OPEN | SUPPORT_CLOSE

        self._attr_unique_id = f"DB{self._db_number}_cover"
        self._attr_extra_state_attributes = {
            "S7 Address Closed": str(self._s7_closed),
            "S7 Address Opened": str(self._s7_opened),
            "S7 Address Manual Open": str(self._s7_man_open),
            # TODO "S7 Address Mode": str(self._s7_mode),
            "S7 Address Time Open Today": str(self._s7_open_tday),
            "S7 Address Time Open YDay": str(self._s7_open_yday),
        }
        self._attr_device_info = coordinator.get_device()

    @property
    def is_closed(self):
        """Return if valve is fully closed."""
        db_data = self.coordinator.data[f"DB{self._db_number}"]
        self._attr_extra_state_attributes[
            "Time Open Today"
        ] = f"{self._s7_open_tday.get_dint(db_data)} min"
        self._attr_extra_state_attributes[
            "Time Open YDay"
        ] = f"{self._s7_open_yday.get_dint(db_data)} min"
        return self._s7_closed.get_bool(db_data)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        # if self.mode == S7Mode.AUTO:
        #    return None
        return self._attr_supported_features

    async def async_open_cover(self, **kwargs):
        """Fully open zone vent."""
        await self.coordinator.write_db(self._s7_man_open, True)

    async def async_close_cover(self, **kwargs):
        """Fully close zone vent."""
        await self.coordinator.write_db(self._s7_man_open, False)


class S7HaCoverGarage(CoordinatorEntity, CoverEntity):
    """Home Assistant Cover as Garage in a S7 PLC."""

    # Commands as defined in PLC logic
    CLOSE_CMD = 1
    OPEN_CMD = 2
    RESET_CMD = 3

    def __init__(self, coordinator, name: str, db_number: int) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        # Rely on the parent class implementation for these attributes
        self._attr_name = name
        self._db_number = db_number

        # Addresses in the DB
        self._s7_is_automatic = S7Bool(db_number, 12, 0)
        self._s7_is_opening = S7Bool(db_number, 12, 1)
        self._s7_is_closing = S7Bool(db_number, 12, 2)
        self._s7_is_closed = S7Bool(db_number, 12, 3)
        self._s7_command = S7Word(db_number, 14)
        self._s7_open_tday = S7Word(db_number, 16)
        self._s7_open_yday = S7Word(db_number, 18)

        self._attr_device_class = CoverDeviceClass.GARAGE
        self._attr_unique_id = f"DB{self._db_number}_cover"
        self._attr_device_info = coordinator.get_device()
        self._attr_extra_state_attributes = {}

    def update_time_attrs(self, db_data):
        """Update the time open today and yday attributes"""
        self._attr_extra_state_attributes[
            "Time Open Today"
        ] = f"{self._s7_open_tday.get_int(db_data)} min"
        self._attr_extra_state_attributes[
            "Time Open YDay"
        ] = f"{self._s7_open_yday.get_int(db_data)} min"

    @property
    def is_closed(self):
        """Return if garage is fully closed."""
        db_data = self.coordinator.data[f"DB{self._db_number}"]
        self.update_time_attrs(db_data)
        return self._s7_is_closed.get_bool(db_data)

    @property
    def is_closing(self):
        """Return if garage is closing."""
        db_data = self.coordinator.data[f"DB{self._db_number}"]
        self.update_time_attrs(db_data)
        return self._s7_is_closing.get_bool(db_data)

    @property
    def is_opening(self):
        """Return if garage is opening."""
        db_data = self.coordinator.data[f"DB{self._db_number}"]
        self.update_time_attrs(db_data)
        return self._s7_is_opening.get_bool(db_data)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        db_data = self.coordinator.data[f"DB{self._db_number}"]
        if self._s7_is_automatic.get_bool(db_data):
            return None
        return SUPPORT_OPEN | SUPPORT_CLOSE

    async def async_open_cover(self, **kwargs):
        """Fully open garage."""
        await self.coordinator.write_int(self._s7_command, self.OPEN_CMD)

    async def async_close_cover(self, **kwargs):
        """Fully close garage."""
        await self.coordinator.write_int(self._s7_command, self.CLOSE_CMD)
