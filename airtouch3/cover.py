import asyncio
from homeassistant.components.cover import (
    ATTR_POSITION,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    CoverDeviceClass,
    CoverEntity,
)

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from airtouch3 import AirTouch3, AT3Group, AT3GroupMode

from .const import DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the AirTouch 3 zone entities."""
    _LOGGER.debug("Setting up AirTouch group entities...")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    at3: AirTouch3 = coordinator.at3

    new_devices = []
    for group in at3.groups.values():
        group_entity = AirTouchGroupEntityAsCover(coordinator, group)
        new_devices.append(group_entity)

    if new_devices:
        async_add_devices(new_devices)


class AirTouchGroupEntityAsCover(CoordinatorEntity, CoverEntity):
    def __init__(self, coordinator, group: AT3Group):
        super().__init__(coordinator)
        self._number = group.number
        self._position_dec = group.position_dec
        self._position_inc = group.position_inc
        self._toggle = group.toggle

        at3_id = coordinator.data["id"]
        self._attr_unique_id = f"at3_{at3_id}_group_ascover_{self._number}"
        self._attr_device_class = CoverDeviceClass.DAMPER

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
    def is_closed(self):
        """Return if valve is fully closed."""
        return not self.coordinator.data["groups"][self._number]["is_on"]

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        mode = self.coordinator.data["groups"][self._number]["mode"]
        if mode != AT3GroupMode.PERECENT:
            return None
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_SET_POSITION

    @property
    def current_cover_position(self) -> int:
        """Return current position of cover."""

        return self.coordinator.data["groups"][self._number]["open_percent"]

    async def async_set_cover_position(self, **kwargs):
        """Set the speed percentage of the fan."""
        percentage = kwargs[ATTR_POSITION]

        if percentage == self.current_cover_position:
            return

        position = self.coordinator.data["groups"][self._number]["open_percent"]
        # Turn off when zero position given
        if percentage == 0:
            await self.async_close_cover()
        # Turn on if position given and currently off
        if percentage != 0 and position == 0:
            await self.async_open_cover()

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

        await self.coordinator.async_refresh()

    async def async_open_cover(self, **kwargs):
        """Fully open zone vent."""
        if self.is_closed:
            is_on = self._toggle()
            if is_on != None:
                self.coordinator.data["groups"][self._number]["is_on"] = is_on
                args = {ATTR_POSITION: 100}
                await self.async_set_cover_position(**args)
        await self.coordinator.async_refresh()

    async def async_close_cover(self, **kwargs):
        """Fully close zone vent."""
        if not self.is_closed:
            is_on = self._toggle()
            if is_on != None:
                self.coordinator.data["groups"][self._number]["is_on"] = is_on
                self.coordinator.data["groups"][self._number]["open_percent"] = 0
        await self.coordinator.async_refresh()
