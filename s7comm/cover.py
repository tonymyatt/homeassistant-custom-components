"""Support for reading covers from S7 PLC."""
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
from homeassistant.const import STATE_ON, STATE_OFF
from .const import DOMAIN, HA_COVER_ENTITIES, HACoverEntityDescription
from .s7comm import S7Bool, S7Comm, S7DWord, S7Word

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Step 7 PLC entities."""
    _LOGGER.debug("Setting up Step7 PLC Cover entities...")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Now we have told the coorindator about what DB's to load
    # wait until the next update before we start adding entities
    # this will mean DB data is available from the time the entities
    # are loaded into HASS
    coordinator.register_dbs()
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [S7HaCover(coordinator, description) for description in HA_COVER_ENTITIES]
    )


class S7HaCover(CoordinatorEntity, CoverEntity):
    """Home Assistant Cover in a S7 PLC."""

    # Commands as defined in PLC logic
    CLOSE_CMD = 1
    OPEN_CMD = 2
    RESET_CMD = 3
    AUTO_CMD = 4

    # def __init__(self, coordinator, name: str, db_number: int) -> None:
    def __init__(self, coordinator, description: HACoverEntityDescription) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._db_number = description.s7datablock
        self._mod_run_stop = description.mod_run_stop

        # Addresses in the DB
        self._s7_interlocks = S7Word(description.s7datablock, 2)
        self._s7_available = S7Bool(description.s7datablock, 12, 5)
        self._s7_auto_available = S7Bool(description.s7datablock, 12, 6)
        self._s7_is_automatic = S7Bool(description.s7datablock, 14, 0)
        self._s7_is_opening = S7Bool(description.s7datablock, 14, 1)
        self._s7_is_closing = S7Bool(description.s7datablock, 14, 2)
        self._s7_is_closed = S7Bool(description.s7datablock, 14, 3)
        self._s7_fault = S7Bool(description.s7datablock, 14, 4)
        self._s7_disabled = S7Bool(description.s7datablock, 14, 5)
        self._s7_command = S7Word(description.s7datablock, 16)
        self._s7_open_tday = S7Word(description.s7datablock, 18)
        self._s7_open_yday = S7Word(description.s7datablock, 20)

        # Rely on the parent class implementation for these attributes
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class
        self._attr_unique_id = f"DB{self._db_number}_cover"
        self._attr_device_info = coordinator.get_device()
        self._attr_extra_state_attributes = {}

    def update_time_attrs(self):
        """Update the time open today and yday attributes"""
        strOnStr = "Open"
        if self._mod_run_stop:
            strOnStr = "Running"
        self._attr_extra_state_attributes[
            f"Time {strOnStr} Today"
        ] = f"{self.coordinator.get_int(self._s7_open_tday)} min"
        self._attr_extra_state_attributes[
            f"Time {strOnStr} YDay"
        ] = f"{self.coordinator.get_int(self._s7_open_yday)} min"

        disabled = self.coordinator.get_bool(self._s7_disabled)
        available = self.coordinator.get_bool(self._s7_available)
        auto = self.coordinator.get_bool(self._s7_is_automatic)
        interlocked = self.coordinator.get_int(self._s7_interlocks) != 0
        self._attr_extra_state_attributes["Status"] = "None"
        if available:
            self._attr_extra_state_attributes["Status"] = "User Control"
        if available and auto:
            self._attr_extra_state_attributes["Status"] = "Automatic"
        if disabled:
            self._attr_extra_state_attributes["Status"] = "Disabled"
        if interlocked:
            self._attr_extra_state_attributes["Status"] = "Interlocked"

    @property
    def state(self):
        """Override the super class implemenation for state when there is a mod run_stop (likely to be a pump)"""
        if self._mod_run_stop:
            if (closed := self.is_closed) is None:
                return None
            return STATE_OFF if closed else STATE_ON

        return super().state

    @property
    def is_closed(self):
        """Return if cover is fully closed."""
        self.update_time_attrs()
        return self.coordinator.get_bool(self._s7_is_closed)

    @property
    def is_closing(self):
        """Return if cover is closing."""
        self.update_time_attrs()
        return self.coordinator.get_bool(self._s7_is_closing)

    @property
    def is_opening(self):
        """Return if cover is opening."""
        self.update_time_attrs()
        return self.coordinator.get_bool(self._s7_is_opening)

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        avail = self.coordinator.get_bool(self._s7_available)
        auto = self.coordinator.get_bool(self._s7_is_automatic)
        open = not self.is_closed
        if not avail or (auto and open):
            return None
        return SUPPORT_OPEN | SUPPORT_CLOSE

    async def async_open_cover(self, **kwargs):
        """Fully open cover."""
        await self.coordinator.write_int(self._s7_command, self.OPEN_CMD)

    async def async_close_cover(self, **kwargs):
        """Fully close cover."""
        await self.coordinator.write_int(self._s7_command, self.CLOSE_CMD)
