from typing import Any
import asyncio

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from airtouch3 import (
    AirTouch3,
    AT3AcUnit,
    AT3Group,
    AT3GroupMode,
    AT3AcMode,
    AT3AcFanSpeed,
)

from .const import DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)

AT3_TO_HA_MODE = {
    AT3AcMode.HEAT: HVAC_MODE_HEAT,
    AT3AcMode.COOL: HVAC_MODE_COOL,
    AT3AcMode.AUTO: HVAC_MODE_HEAT_COOL,
    AT3AcMode.DRY: HVAC_MODE_DRY,
    AT3AcMode.FAN: HVAC_MODE_FAN_ONLY,
}

HA_MODE_TO_AT = {value: key for key, value in AT3_TO_HA_MODE.items()}

AT3_TO_HA_FAN_SPEED = {
    AT3AcFanSpeed.QUIET: FAN_DIFFUSE,
    AT3AcFanSpeed.LOW: FAN_LOW,
    AT3AcFanSpeed.MED: FAN_MEDIUM,
    AT3AcFanSpeed.HIGH: FAN_HIGH,
    AT3AcFanSpeed.POWER: FAN_FOCUS,
    AT3AcFanSpeed.AUTO: FAN_AUTO,
}

HA_FAN_SPEED_TO_AT = {value: key for key, value in AT3_TO_HA_FAN_SPEED.items()}

# POWER_ON = 1
# POWER_OFF = 0

AT3_HVAC_MODES = [
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_DRY,
]

# MAP_AC_FAN_MODE = {
#    0: FAN_AUTO,            # AUTO
#    1: FAN_DIFFUSE,         # QUIET
#    2: FAN_LOW,             # LOW
#    3: FAN_MEDIUM,          # MEDIUM
#    4: FAN_HIGH,            # HIGH
#    5: FAN_FOCUS,           # POWERFUL
#    6: "turbo"              # TURBO
# }

# def MAP_VALUE_SEARCH(MAP: dict[int, Any], value: Any) -> int:
#    return next((k for k, v in MAP.items() if v == value), None)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AirTouch 3 climate entities."""
    _LOGGER.debug("Setting up AirTouch climate entities...")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    at3: AirTouch3 = coordinator.at3

    new_entities = []
    for ac_unit in at3.ac_units.values():
        ac_entity = AT3AcUnitClimate(coordinator, ac_unit)
        new_entities.append(ac_entity)
    for group in at3.groups.values():
        if group.temperature != -1:
            group_entity = AT3GroupClimate(coordinator, group)
            new_entities.append(group_entity)

    if new_entities:
        async_add_entities(new_entities)


class AT3GroupClimate(CoordinatorEntity, ClimateEntity):
    def __init__(self, coordinator, group: AT3Group):
        super().__init__(coordinator)
        self._number = group.number
        self._toggle = group.toggle
        self._toggle_mode = group.toggle_mode

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
        return f"at3_{id}_group_{self._number}_climate"

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.coordinator.data["groups"][self._number]["temperature"]

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.coordinator.data["groups"][self._number]["temperature_sp"]

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1.0

    @property
    def hvac_mode(self):
        """Return hvac target hvac state."""
        # there are other power states that aren't 'on' but still count as on (eg. 'Turbo')
        # on and temp control = Auto
        # on and position control = Fan
        # otherwise off
        mode = self.coordinator.data["groups"][self._number]["mode"]
        is_on = self.coordinator.data["groups"][self._number]["is_on"]
        if is_on:
            if mode == AT3GroupMode.TEMPERATURE:
                return HVAC_MODE_AUTO
            else:
                return HVAC_MODE_FAN_ONLY
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return [HVAC_MODE_AUTO, HVAC_MODE_FAN_ONLY, HVAC_MODE_OFF]

    @property
    def supported_features(self):
        """Return the list of supported features."""
        mode = self.coordinator.data["groups"][self._number]["mode"]
        if mode == AT3GroupMode.TEMPERATURE:
            return SUPPORT_TARGET_TEMPERATURE
        return 0

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        is_on = self.coordinator.data["groups"][self._number]["is_on"]
        mode = self.coordinator.data["groups"][self._number]["mode"]
        if hvac_mode == HVAC_MODE_OFF and is_on:
            self._toggle()
        elif hvac_mode == HVAC_MODE_AUTO or hvac_mode == HVAC_MODE_FAN_ONLY:
            if not is_on:
                self._toggle()
            if hvac_mode == HVAC_MODE_AUTO and mode == AT3GroupMode.PERECENT:
                self._toggle_mode()
            if hvac_mode == HVAC_MODE_FAN_ONLY and mode == AT3GroupMode.TEMPERATURE:
                self._toggle_mode()

        await self.coordinator.async_refresh()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None or temp == self.target_temperature:
            return
        # TODO await self._group.toggle temp up or down
        await self.coordinator.async_refresh()


class AT3AcUnitClimate(CoordinatorEntity, ClimateEntity):

    # Climate entity defined attributes
    _attr_fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_hvac_modes = AT3_HVAC_MODES
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_target_temperature_step = 1.0

    def __init__(self, coordinator, ac_unit: AT3AcUnit):
        super().__init__(coordinator)
        self._number = ac_unit.number
        self._temperature_inc = ac_unit.temperature_inc
        self._temperature_dec = ac_unit.temperature_dec
        self._toggle = ac_unit.toggle
        self._set_mode = ac_unit.set_mode
        self._set_fan_speed = ac_unit.set_fan_speed

        ac_id = self.coordinator.data["id"]

        self._attr_name = self.coordinator.data["ac_units"][self._number]["name"]
        self._attr_unique_id = f"at3_{ac_id}_ac_{self._number}"

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
    def current_temperature(self):
        """Return the current temperature."""
        return self.coordinator.data["ac_units"][self._number]["temperature"]

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.coordinator.data["ac_units"][self._number]["temperature_sp"]

    @property
    def supported_features(self):
        """Return the list of supported features."""
        mode = self.coordinator.data["ac_units"][self._number]["mode"]

        # Dry, no features
        if mode == AT3AcMode.DRY:
            return 0

        # Fan only
        if mode == AT3AcMode.FAN:
            return SUPPORT_FAN_MODE

        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

    @property
    def hvac_mode(self):
        """Return hvac target hvac state."""
        ac_data = self.coordinator.data["ac_units"][self._number]
        if not ac_data["is_on"]:
            return HVAC_MODE_OFF

        return AT3_TO_HA_MODE[ac_data["mode"]]

    @property
    def fan_mode(self):
        """Return fan mode of the AC this group belongs to."""
        ac_data = self.coordinator.data["ac_units"][self._number]
        return AT3_TO_HA_FAN_SPEED[ac_data["fan_speed"]]

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        if hvac_mode == HVAC_MODE_OFF:
            await self.async_turn_off()
        else:
            mode = self._set_mode(HA_MODE_TO_AT[hvac_mode])
            if mode is not None:
                self.coordinator.data["ac_units"][self._number]["mode"] = mode
            await self.async_turn_on()
        await self.coordinator.async_refresh()

    async def async_set_fan_mode(self, fan_mode):
        # TODO Need to write the fan mode
        fan = self._set_fan_speed(HA_FAN_SPEED_TO_AT[fan_mode])
        if fan is not None:
            self.coordinator.data["ac_units"][self._number]["fan_speed"] = fan
        await self.coordinator.async_refresh()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None or temp == self.target_temperature:
            return

        ac_data = self.coordinator.data["ac_units"][self._number]
        temp_sp = ac_data["temperature_sp"]
        count = 0
        # Max 20 adjustements should get us to setpoint
        while count < 20:
            if temp_sp == temp:
                break
            elif temp > temp_sp:
                temp_sp = self._temperature_inc()
            elif temp < temp_sp:
                temp_sp = self._temperature_dec()

            if temp_sp is not None:
                self.coordinator.data["ac_units"][self._number][
                    "temperature_sp"
                ] = temp_sp
            else:
                break

            await asyncio.sleep(0.05)
            count = count + 1

        await self.coordinator.async_refresh()

    async def async_turn_on(self):
        """Turn on."""
        ac_data = self.coordinator.data["ac_units"][self._number]
        if not ac_data["is_on"]:
            is_on = self._toggle()
            if is_on is not None:
                self.coordinator.data["ac_units"][self._number]["is_on"] = is_on

        await self.coordinator.async_refresh()

    async def async_turn_off(self):
        """Turn off."""
        ac_data = self.coordinator.data["ac_units"][self._number]
        if ac_data["is_on"]:
            is_on = self._toggle()
            if is_on is not None:
                self.coordinator.data["ac_units"][self._number]["is_on"] = is_on

        await self.coordinator.async_refresh()
