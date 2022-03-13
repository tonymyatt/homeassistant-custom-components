"""Support for reading numberic values as sensors from S7 PLC."""
from __future__ import annotations
from collections import MutableMapping
from typing import Any, Mapping, cast

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from .const import DOMAIN, STRAVA, WEEK, DIST, TIME, DELTA

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Tonym entities."""
    _LOGGER.debug("Setting up Tonym Sensor PLC entities...")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Now we have told the coorindator about what DB's to load
    # wait until the next update before we start adding entities
    # this will mean DB data is available from the time the entities
    # are loaded into HASS
    await coordinator.async_config_entry_first_refresh()

    new_entities = []
    e = TonymReal(coordinator, "Cycling Last Week Distance", "km", STRAVA + WEEK + DIST)
    e.add_extra_state_attribute("Last Week Delta", "%", STRAVA + WEEK + DIST + DELTA)
    new_entities.append(e)
    e = TonymReal(coordinator, "Cycling Last Week Time", "hrs", STRAVA + WEEK + TIME)
    new_entities.append(e)
    #    print(f"Cycling Last Week Time delta: {weekly_data[monday_last_week]['time']/weekly_data[monday_fortnight]['time']*100:0.0f}%")
    #    print(f"Cycling Last Week Elevation: {weekly_data[monday_last_week]['elevation']:0.0f}m")
    #    print(f"Cycling Last Week Climbing: {weekly_data[monday_last_week]['elevation']/weekly_data[monday_last_week]['distance']/10:0.1f}%")
    #    print(f"Cycling This Week Distance: {weekly_data[monday_this_week]['distance']:0.1f}km")
    #    print(f"Cycling This Week Distance delta: {weekly_data[monday_this_week]['distance']/weekly_data[monday_last_week]['distance']*100:0.0f}%")
    #   print(f"Cycling This Week Time: {weekly_data[monday_this_week]['time']:0.1f}hrs")
    #    print(f"Cycling This Week Time delta: {weekly_data[monday_this_week]['time']/weekly_data[monday_last_week]['time']*100:0.0f}%")
    #    print(f"Cycling This Week Elevation: {weekly_data[monday_this_week]['elevation']:0.0f}m")
    #   print(f"Cycling This Week Climbing: {weekly_data[monday_this_week]['elevation']/weekly_data[monday_this_week]['distance']/10:0.1f}%")

    if new_entities:
        async_add_entities(new_entities)


class TonymReal(CoordinatorEntity, SensorEntity):
    """Implementation of a step7 real sensor."""

    def __init__(self, coordinator, name: str, units: str, data_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._data_id = data_id
        self._state: StateType = None
        self._extra_attributes = dict()

        # Rely on the parent class implementation for these attributes
        self._attr_name = name
        self._attr_native_unit_of_measurement = units
        self._attr_unique_id = f"tonym_{data_id}"
        # self._attr_extra_state_attributes
        self._attr_device_info = coordinator.get_device()

    def add_extra_state_attribute(self, name: str, units: str, data_id: str):
        self._extra_attributes[name] = {"units": units, "data_id": data_id}

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""

        if len(self._extra_attributes) == 0:
            return None

        attrs = dict()
        for key in self._extra_attributes.keys():
            data_id = self._extra_attributes[key]["data_id"]
            units = self._extra_attributes[key]["units"]
            value = self.coordinator.data[data_id]
            attrs[key] = f"{value} {units}"

        return attrs

    @property
    def native_value(self) -> StateType:
        """Return native value for entity."""
        idx = self._data_id

        # Check we have data available and our db index is available
        if not isinstance(self.coordinator.data, MutableMapping):
            return None
        if not self.coordinator.data.get(idx):
            return None

        return self.coordinator.data[idx]
