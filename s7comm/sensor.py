"""Support for reading numberic values as sensors from S7 PLC."""
from __future__ import annotations
from collections import MutableMapping
from typing import Any, cast

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

from .const import DOMAIN
from .s7comm import S7Comm, s7_real

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Step 7 PLC entities."""
    _LOGGER.debug("Setting up Step7 Sensor PLC entities...")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    coordinator.s7comm.register_db(40, 0, 54)  # Rain Counter
    coordinator.s7comm.register_db(202, 0, 120)  # Tank Level
    coordinator.s7comm.register_db(60, 0, 120)  # Camper Trailer Batt Voltage
    coordinator.s7comm.register_db(22, 0, 120)  # Outside temp
    coordinator.s7comm.register_db(32, 0, 16)  # Outside temp ROC

    # Now we have told the coorindator about what DB's to load
    # wait until the next update before we start adding entities
    # this will mean DB data is available from the time the entities
    # are loaded into HASS
    await coordinator.async_config_entry_first_refresh()

    new_entities = []
    e = Step7Real(coordinator, "Rain Today", "mm", 40, 30)
    new_entities.append(e)
    e = Step7Real(coordinator, "Rain Yesterday", "mm", 40, 42)
    new_entities.append(e)
    e = Step7Real(coordinator, "Tank Level", "%", 202, 42)
    new_entities.append(e)
    e = Step7Real(coordinator, "Camper Trailer Battery Voltage", "V", 60, 42)
    new_entities.append(e)
    e = Step7Real(coordinator, "Outside Temperature", "°C", 22, 42)
    new_entities.append(e)
    e = Step7Real(coordinator, "Outside Temperature Rate of Change", "°C/h", 32, 12)
    new_entities.append(e)

    if new_entities:
        async_add_entities(new_entities)


class Step7CpuStatus(CoordinatorEntity, SensorEntity):
    """Implementation of a step7 CPU Run Status."""

    pass


class Step7Real(CoordinatorEntity, SensorEntity):
    """Implementation of a step7 real sensor."""

    def __init__(
        self, coordinator, name: str, units: str, db_number: int, offset: int
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._offset = offset
        self._db_number = db_number
        self._state: StateType = None

        # Rely on the parent class implementation for these attributes
        self._attr_name = name
        self._attr_native_unit_of_measurement = units
        self._attr_unique_id = f"DB{self._db_number}.REAL{self._offset}"
        self._attr_extra_state_attributes = {"S7 address": self._attr_unique_id}
        self._attr_device_info = coordinator.get_device()

    @property
    def native_value(self) -> StateType:
        """Return native value for entity."""
        idx = f"DB{self._db_number}"

        # Check we have data available and our db index is available
        if not isinstance(self.coordinator.data, MutableMapping):
            return None
        if not self.coordinator.data.get(idx):
            return None

        db_data = self.coordinator.data[idx]
        value = s7_real("{0:.1f}", db_data, self._offset)
        return cast(StateType, value)
