import asyncio

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.fan import FanEntity
from homeassistant.components.fan import (
    SUPPORT_SET_SPEED,
    SUPPORT_PRESET_MODE,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from types import SimpleNamespace

from airtouch3 import AirTouch3, AT3Group, AT3GroupMode

from .const import DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)


class PRESETS(SimpleNamespace):
    POSITION = "Position"
    TEMP = "Temperature"


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the AirTouch 3 zone entities."""
    _LOGGER.debug("Setting up AirTouch group entities...")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    at3: AirTouch3 = coordinator.at3

    new_devices = []
    for group in at3.groups.values():
        group_entity = AirTouchGroupEntity(coordinator, group)
        new_devices.append(group_entity)

    if new_devices:
        async_add_devices(new_devices)


class AirTouchGroupEntity(CoordinatorEntity, FanEntity):
    def __init__(self, coordinator, group: AT3Group):
        super().__init__(coordinator)
        self._number = group.number
        self._position_dec = group.position_dec
        self._position_inc = group.position_inc
        self._toggle = group.toggle

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.data["id"])},
            name=self.coordinator.data["name"],
            manufacturer="Polyaire",
            model="Airtouch 3",
        )

    @property
    def name(self):
        """Return the name for this device."""
        return self.coordinator.data["groups"][self._number]["name"]

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        id = self.coordinator.data["id"]
        return f"at3_{id}_group_{self._number}"

    @property
    def is_on(self):
        """Return true if the entity is on."""
        return self.coordinator.data["groups"][self._number]["is_on"]

    @property
    def percentage(self):
        """Return the current speed percentage."""
        return self.coordinator.data["groups"][self._number]["open_percent"]

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return 20

    # TODO Not needed because these are captured in standard
    # attributes @property
    # def extra_state_attributes(self):
    #    """Return the state attributes."""
    #    attrs = {
    #        "Percent": str(self._group.open_percent),
    #        "Mode": str(self._group.mode),
    #    }
    #    return attrs

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_PRESET_MODE | (
            self.preset_mode == PRESETS.POSITION and SUPPORT_SET_SPEED
        )

    @property
    def preset_mode(self):
        """Return preset mode."""
        mode = self.coordinator.data["groups"][self._number]["mode"]
        if mode == AT3GroupMode.TEMPERATURE:
            return PRESETS.TEMP
        return PRESETS.POSITION

    @property
    def preset_modes(self):
        """Return preset modes."""
        temp = self.coordinator.data["groups"][self._number]["temperature"]
        if temp == -1:
            return 0
        return [PRESETS.POSITION, PRESETS.TEMP]

    async def async_set_percentage(self, percentage):
        """Set the speed percentage of the fan."""
        if percentage == self.percentage or self.preset_mode != PRESETS.POSITION:
            return

        position = self.coordinator.data["groups"][self._number]["open_percent"]
        # Turn off when zero position given
        if percentage == 0:
            await self.async_turn_off()
        # Turn on if position given and currently off
        if percentage != 0 and position == 0:
            await self.async_turn_on()

        # Max 20 adjustements of percentage in one go should get from
        # 0% to 100% or 100% to 0%
        count = 0
        while count < 20:
            if percentage == position:
                break
            elif percentage > position:
                position = self._position_inc()
            elif percentage < position:
                position = self._position_dec()

            if position:
                self.coordinator.data["groups"][self._number]["open_percent"] = position
            else:
                break

            await asyncio.sleep(0.05)
            count = count + 1

        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Set the preset mode of the fan."""
        if preset_mode == self.preset_mode:
            return
        control_type = (
            AT3GroupMode.PERECENT
            if preset_mode == PRESETS.POSITION
            else AT3GroupMode.TEMPERATURE
        )
        # TODO Toggle the control type - needs to be implemented
        # Result of this is the mode change will never occur even
        # if the user asks for it
        self.async_write_ha_state()

    async def async_turn_on(
        self, speed=None, percentage=None, preset_mode=None, **kwargs
    ):
        """Turn on the fan."""
        if not self.is_on:
            is_on = self._toggle()
            if is_on is not None:
                self.coordinator.data["groups"][self._number]["is_on"] = is_on
                await self.async_set_percentage(100)
        if percentage is not None:
            await self.async_set_percentage(percentage)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        if self.is_on:
            is_on = self._toggle()
            if is_on != None:
                self.coordinator.data["groups"][self._number]["is_on"] = is_on
                self.coordinator.data["groups"][self._number]["open_percent"] = 0
        self.async_write_ha_state()
