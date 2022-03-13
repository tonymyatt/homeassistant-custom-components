"""AirTouch 4 component to control of AirTouch 4 Climate Devices."""
from __future__ import annotations

import logging

from airtouch3 import AT3AcFanSpeed
from airtouch3 import AT3AcMode

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE
AT_TO_HA_STATE = {
    "Heat": HVAC_MODE_HEAT,
    "Cool": HVAC_MODE_COOL,
    "Auto": HVAC_MODE_AUTO,
    "Dry": HVAC_MODE_DRY,
    "Fan": HVAC_MODE_FAN_ONLY,
}

HA_STATE_TO_AT = {
    HVAC_MODE_HEAT: "Heat",
    HVAC_MODE_COOL: "Cool",
    HVAC_MODE_AUTO: "Auto",
    HVAC_MODE_DRY: "Dry",
    HVAC_MODE_FAN_ONLY: "Fan",
    HVAC_MODE_OFF: "Off",
}

AT_TO_HA_FAN_SPEED = {
    "Quiet": FAN_DIFFUSE,
    "Low": FAN_LOW,
    "Medium": FAN_MEDIUM,
    "High": FAN_HIGH,
    "Powerful": FAN_FOCUS,
    "Auto": FAN_AUTO,
}

AT_GROUP_MODES = [HVAC_MODE_OFF, HVAC_MODE_FAN_ONLY]

HA_FAN_SPEED_TO_AT = {value: key for key, value in AT_TO_HA_FAN_SPEED.items()}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Airtouch 3."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    at3 = coordinator.at3
    info = coordinator.data
    entities: list[ClimateEntity] = [
        AirtouchGroup(coordinator, group.number) for group in at3.groups.values()
    ]
    entities.extend(AirtouchAC(coordinator, ac.number) for ac in at3.acUnits.values())

    print("Found entities %s", entities)

    _LOGGER.debug("Found entities %s", entities)

    async_add_entities(entities)


class AirtouchAC(CoordinatorEntity, ClimateEntity):
    """Representation of an AirTouch 3 ac."""

    _attr_supported_features = SUPPORT_FAN_MODE
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, coordinator, ac_number):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._ac_number = ac_number
        self._at3 = coordinator.at3
        self._ac_unit = coordinator.at3.acUnits[ac_number]

    @callback
    def _handle_coordinator_update(self):
        self._ac_unit = self._at3.acUnits[self._ac_number]
        return super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._at3.id)},
            name=self._at3.name,
            manufacturer="Polyaire",
            model="Airtouch 3",
        )

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return f"ac_{self._ac_number}"

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._ac_unit.temperature

    @property
    def name(self):
        """Return the name of the climate device."""
        return f"AC {self._ac_unit.name}"

    @property
    def fan_mode(self):
        """Return fan mode of the AC this group belongs to."""
        return AT_TO_HA_FAN_SPEED[self._ac_unit.fan_speed]

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        airtouch_fan_speeds = [AT3AcFanSpeed.LOW, AT3AcFanSpeed.MED, AT3AcFanSpeed.HIGH]
        return [AT_TO_HA_FAN_SPEED[speed] for speed in airtouch_fan_speeds]

    @property
    def hvac_mode(self):
        """Return hvac target hvac state."""
        if not self._ac_unit.is_on:
            return HVAC_MODE_OFF

        return AT_TO_HA_STATE[self._ac_unit.mode]

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        airtouch_modes = [
            AT3AcMode.AUTO,
            AT3AcMode.HEAT,
            AT3AcMode.DRY,
            AT3AcMode.FAN,
            AT3AcMode.COOL,
        ]
        modes = [AT_TO_HA_STATE[mode] for mode in airtouch_modes]
        modes.append(HVAC_MODE_OFF)
        return modes

    # async def async_set_hvac_mode(self, hvac_mode):
    #    """Set new operation mode."""
    #    if hvac_mode not in HA_STATE_TO_AT:
    #        raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")

    #    if hvac_mode == HVAC_MODE_OFF:
    #        return await self.async_turn_off()
    #    await self._airtouch.SetCoolingModeForAc(
    #        self._ac_number, HA_STATE_TO_AT[hvac_mode]
    #    )
    #    # in case it isn't already, unless the HVAC mode was off, then the ac should be on
    #    await self.async_turn_on()
    #    self._unit = self._airtouch.GetAcs()[self._ac_number]
    #    _LOGGER.debug("Setting operation mode of %s to %s", self._ac_number, hvac_mode)
    #    self.async_write_ha_state()

    # async def async_set_fan_mode(self, fan_mode):
    #    """Set new fan mode."""
    #    if fan_mode not in self.fan_modes:
    #        raise ValueError(f"Unsupported fan mode: {fan_mode}")
    #
    #    _LOGGER.debug("Setting fan mode of %s to %s", self._ac_number, fan_mode)
    #    await self._airtouch.SetFanSpeedForAc(
    #        self._ac_number, HA_FAN_SPEED_TO_AT[fan_mode]
    #    )
    #    self._unit = self._airtouch.GetAcs()[self._ac_number]
    #    self.async_write_ha_state()

    async def async_turn_on(self):
        """Turn on."""
        _LOGGER.debug("Turning %s on", self.unique_id)
        if not self._ac_unit.is_on:
            await self._ac_unit.Toggle()

        self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn off."""
        _LOGGER.debug("Turning %s off", self.unique_id)
        if self._ac_unit.is_on:
            await self._ac_unit.Toggle()


class AirtouchGroup(CoordinatorEntity, ClimateEntity):
    """Representation of an AirTouch 4 group."""

    _attr_supported_features = SUPPORT_TARGET_TEMPERATURE
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_hvac_modes = AT_GROUP_MODES

    def __init__(self, coordinator, group_number):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._group_number = group_number
        self._at3 = coordinator.at3
        self._group = coordinator.at3.groups[group_number]

    @callback
    def _handle_coordinator_update(self):
        self._group = self._at3.groups[self._group_number]
        return super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._at3.id)},
            name=self._at3.name,
            manufacturer="Polyaire",
            model="Airtouch 3",
        )

    @property
    def unique_id(self):
        """Return unique ID for this device."""
        return self._group_number

    @property
    def min_temp(self):
        """Return Minimum Temperature for AC of this group."""
        return 20

    @property
    def max_temp(self):
        """Return Max Temperature for AC of this group."""
        return 40

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._group.name

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._group.temperature

    @property
    def target_temperature(self):
        """Return the temperature we are trying to reach."""
        return self._group.temperature_sp

    @property
    def hvac_mode(self):
        """Return hvac target hvac state."""
        # there are other power states that aren't 'on' but still count as on (eg. 'Turbo')
        if not self._group.is_on:
            return HVAC_MODE_OFF

        return HVAC_MODE_FAN_ONLY

    # async def async_set_hvac_mode(self, hvac_mode):
    #    """Set new operation mode."""
    #    if hvac_mode not in HA_STATE_TO_AT:
    #        raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")
    #
    #    if hvac_mode == HVAC_MODE_OFF:
    #        return await self.async_turn_off()
    # _LOGGER.debug(
    #    "Setting operation mode of %s to %s", self._ac_unit.name, hvac_mode
    # )
    #    self.async_write_ha_state()

    # @property
    # def fan_mode(self):
    #    """Return fan mode of the AC this group belongs to."""
    #    return AT_TO_HA_FAN_SPEED[self._airtouch.acs[self._unit.BelongsToAc].AcFanSpeed]

    # @property
    # def fan_modes(self):
    #    """Return the list of available fan modes."""
    #    airtouch_fan_speeds = self._airtouch.GetSupportedFanSpeedsByGroup(
    #        self._group_number
    #    )
    #    return [AT_TO_HA_FAN_SPEED[speed] for speed in airtouch_fan_speeds]

    # async def async_set_temperature(self, **kwargs):
    #    """Set new target temperatures."""
    #    temp = kwargs.get(ATTR_TEMPERATURE)

    #    _LOGGER.debug("Setting temp of AC %s to %s", self._ac_unit.name, str(temp))
    # self._unit = await self._airtouch.SetGroupToTemperature(
    #    self._group_number, int(temp)
    # )
    #    self.async_write_ha_state()

    # async def async_set_fan_mode(self, fan_mode):
    #    """Set new fan mode."""
    #    if fan_mode not in self.fan_modes:
    #        raise ValueError(f"Unsupported fan mode: {fan_mode}")
    #
    #    _LOGGER.debug("Setting fan mode of %s to %s", self._group_number, fan_mode)
    #    self._unit = await self._airtouch.SetFanSpeedByGroup(
    #        self._group_number, HA_FAN_SPEED_TO_AT[fan_mode]
    #    )
    #    self.async_write_ha_state()

    async def async_turn_on(self):
        """Turn on."""
        _LOGGER.debug("Turning %s on", self.unique_id)
        if not self._group.is_on:
            await self._group.Toggle()

        self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn off."""
        _LOGGER.debug("Turning %s off", self.unique_id)
        if self._group.is_on:
            await self._group.Toggle()

        self.async_write_ha_state()
