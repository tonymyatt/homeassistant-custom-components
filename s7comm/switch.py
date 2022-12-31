"""Support for reading switches from S7 PLC."""
from collections import MutableMapping
from enum import Enum
import logging

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    HA_COVER_ENTITIES,
    HA_WATERING_AREAS,
    HACoverEntityDescription,
    HAWateringAreaDescription,
)
from .s7comm import S7Bool, S7Comm, S7DWord, S7Word

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Step 7 PLC entities."""
    _LOGGER.debug("Setting up Step7 PLC Switch entities...")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Now we have told the coorindator about what DB's to load
    # wait until the next update before we start adding entities
    # this will mean DB data is available from the time the entities
    # are loaded into HASS
    coordinator.register_dbs()
    await coordinator.async_config_entry_first_refresh()

    # Covers
    for description in HA_COVER_ENTITIES:
        if description.disable_switch:
            async_add_entities([HaCoverDisableSwitch(coordinator, description)])

    # Watering areas
    async_add_entities(
        [
            HaWateringAreaEnableSwitch(coordinator, description)
            for description in HA_WATERING_AREAS
        ]
    )


class HaCoverDisableSwitch(CoordinatorEntity, SwitchEntity):

    # Commands as defined in PLC logic
    DISABLE_CMD = 5
    ENABLE_CMD = 6

    def __init__(self, coordinator, description: HACoverEntityDescription) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._db_number = description.s7datablock

        # Addresses in the DB
        self._s7_disabled = S7Bool(description.s7datablock, 14, 5)
        self._s7_command = S7Word(description.s7datablock, 16)

        # Rely on the parent class implementation for these attributes
        self._attr_name = description.name + " Disabled"
        self._attr_unique_id = f"DB{self._db_number}_sw_disabled"
        self._attr_device_info = coordinator.get_device()
        self._attr_icon = "mdi:close-circle-outline"

    @property
    def is_on(self):
        """Return true if device is on."""
        return self.coordinator.get_bool(self._s7_disabled)

    async def async_turn_on(self, **kwargs):
        """Turn the device to disabled (on)."""
        await self.coordinator.write_int(self._s7_command, self.DISABLE_CMD)

    async def async_turn_off(self, **kwargs):
        """Turn the device to enabled (off)."""
        await self.coordinator.write_int(self._s7_command, self.ENABLE_CMD)


class HaWateringAreaEnableSwitch(CoordinatorEntity, SwitchEntity):

    # Commands as defined in PLC logic
    DISABLE_CMD = 2
    ENABLE_CMD = 3

    def __init__(self, coordinator, description: HAWateringAreaDescription) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._db_number = description.s7datablock

        # Addresses in the DB
        self._s7_area_avail = S7Bool(description.s7datablock, 0, 0)
        self._s7_source_avail = S7Bool(description.s7datablock, 0, 1)
        self._s7_enabled = S7Bool(description.s7datablock, 8, 0)
        self._s7_command = S7Word(description.s7datablock, 10)

        # Rely on the parent class implementation for these attributes
        self._attr_name = description.name
        self._attr_unique_id = f"DB{self._db_number}_sw_enabled"
        self._attr_device_info = description.device
        self._attr_icon = "mdi:water-check"
        self._attr_extra_state_attributes = {}

    def update_time_attrs(self):
        """Update the time open today and yday attributes"""

        area_avail = self.coordinator.get_bool(self._s7_area_avail)
        source_avail = self.coordinator.get_bool(self._s7_source_avail)
        enabled = self.coordinator.get_bool(self._s7_enabled)
        self._attr_extra_state_attributes["Status"] = "Ready"
        if not source_avail:
            self._attr_extra_state_attributes["Status"] = "Source Unavailable"
        if not area_avail:
            self._attr_extra_state_attributes["Status"] = "Outlet(s) Unavailable"
        if not enabled:
            self._attr_extra_state_attributes["Status"] = "Disabled"

    @property
    def is_on(self):
        """Return true if device is on."""
        self.update_time_attrs()
        return self.coordinator.get_bool(self._s7_enabled)

    async def async_turn_on(self, **kwargs):
        """Turn the device to disabled (on)."""
        await self.coordinator.write_int(self._s7_command, self.ENABLE_CMD)

    async def async_turn_off(self, **kwargs):
        """Turn the device to enabled (off)."""
        await self.coordinator.write_int(self._s7_command, self.DISABLE_CMD)
