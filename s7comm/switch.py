"""Support for reading switches from S7 PLC."""
from collections.abc import MutableMapping
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
    HA_DEVICE2_ENTITIES,
    HA_WATERING_AREAS,
    HAGenericEntityDescription,
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
            async_add_entities(
                [HaGenericDisableSwitch(coordinator, description, 14, 5, 16)]
            )

    # Device2s
    for description in HA_DEVICE2_ENTITIES:
        if description.disable_switch:
            async_add_entities(
                [
                    HaGenericDisableSwitch(coordinator, description, 10, 3, 12),
                    S7HaDevice2(coordinator, description),
                ]
            )

    # Watering areas
    async_add_entities(
        [
            HaWateringAreaEnableSwitch(coordinator, description)
            for description in HA_WATERING_AREAS
        ]
    )


class HaGenericDisableSwitch(CoordinatorEntity, SwitchEntity):

    # Commands as defined in PLC logic
    DISABLE_CMD = 5
    ENABLE_CMD = 6

    def __init__(
        self,
        coordinator,
        description: HAGenericEntityDescription,
        disable_byte: int,
        disable_bit: int,
        command_byte: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._db_number = description.s7datablock

        # Addresses in the DB
        self._s7_disabled = S7Bool(description.s7datablock, disable_byte, disable_bit)
        self._s7_command = S7Word(description.s7datablock, command_byte)

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


class S7HaDevice2(CoordinatorEntity, SwitchEntity):
    """Home Assistant Device with two states in a S7 PLC."""

    # Commands as defined in PLC logic
    OFF_CMD = 1
    ON_CMD = 2
    RESET_CMD = 3
    AUTO_CMD = 4

    def __init__(self, coordinator, description: HAGenericEntityDescription) -> None:
        """Initialize the cover."""
        super().__init__(coordinator)
        self._db_number = description.s7datablock

        # Addresses in the DB
        self._s7_interlocks = S7Word(description.s7datablock, 2)
        self._s7_available = S7Bool(description.s7datablock, 8, 2)
        self._s7_auto_available = S7Bool(description.s7datablock, 8, 3)
        self._s7_is_automatic = S7Bool(description.s7datablock, 10, 0)
        self._s7_is_on = S7Bool(description.s7datablock, 10, 1)
        self._s7_fault = S7Bool(description.s7datablock, 10, 2)
        self._s7_disabled = S7Bool(description.s7datablock, 10, 3)
        self._s7_command = S7Word(description.s7datablock, 12)
        self._s7_on_tday = S7Word(description.s7datablock, 14)
        self._s7_on_yday = S7Word(description.s7datablock, 16)

        # Rely on the parent class implementation for these attributes
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_device_class = description.device_class
        self._attr_unique_id = f"DB{self._db_number}_device2"
        self._attr_device_info = coordinator.get_device()
        self._attr_extra_state_attributes = {}

    def update_time_attrs(self):
        """Update the on today and yday attributes"""
        self._attr_extra_state_attributes[
            "Time On Today"
        ] = f"{self.coordinator.get_int(self._s7_on_tday)} min"
        self._attr_extra_state_attributes[
            "Time On YDay"
        ] = f"{self.coordinator.get_int(self._s7_on_yday)} min"

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
    def is_on(self) -> bool:
        """Return True if entity is on."""
        self.update_time_attrs()
        return self.coordinator.get_bool(self._s7_is_on)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.coordinator.write_int(self._s7_command, self.ON_CMD)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.coordinator.write_int(self._s7_command, self.OFF_CMD)
