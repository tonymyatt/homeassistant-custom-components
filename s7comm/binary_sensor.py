"""Support for reading boolean values as digital_sensors from S7 PLC."""
from collections.abc import MutableMapping
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, STATUS_BINARY_ENTITIES
from .s7comm import s7_bool

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Step 7 PLC entities."""
    _LOGGER.debug("Setting up Step7 PLC Digital Sensor entities...")
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    coordinator.s7comm.register_db(252, 0, 18)  # Front Deck Motion
    coordinator.s7comm.register_db(150, 0, 18)  # PLC Cabinet Open

    # Now we have told the coorindator about what DB's to load
    # wait until the next update before we start adding entities
    # this will mean DB data is available from the time the entities
    # are loaded into HASS
    await coordinator.async_config_entry_first_refresh()

    MOTION = BinarySensorDeviceClass.MOTION
    DOOR = BinarySensorDeviceClass.DOOR

    new_entities = []
    entity = S7Bool(coordinator, MOTION, "Front Deck Motion", 252, 14, 0)
    new_entities.append(entity)
    entity = S7Bool(coordinator, DOOR, "PLC Cabinet", 150, 14, 0, True)
    async_add_entities(new_entities)

    async_add_entities(
        [
            S7StatusBinaryEntity(coordinator, description)
            for description in STATUS_BINARY_ENTITIES
        ]
    )


class S7Bool(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor representing a boolean in a S7 PLC."""

    def __init__(
        self,
        coordinator,
        dev_class: BinarySensorDeviceClass,
        name: str,
        db_number: int,
        byte: int,
        bit: int,
        invert: bool = False,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_class = dev_class
        self._byte = byte
        self._bit = bit
        self._db_number = db_number
        self._invert = invert

        # Rely on the parent class implementation for these attributes
        self._attr_name = name
        self._attr_unique_id = f"DB{self._db_number}.DBX{self._byte}.{self._bit}"
        self._attr_extra_state_attributes = {"S7 address": self._attr_unique_id}
        self._attr_device_info = coordinator.get_device()

    @property
    def is_on(self):
        """Return native value for entity."""
        idx = f"DB{self._db_number}"

        # Check we have data available and our db index is available
        if not isinstance(self.coordinator.data, MutableMapping):
            return None
        if not self.coordinator.data.get(idx):
            return None

        db_data = self.coordinator.data[idx]
        bool_value = s7_bool(db_data, self._byte, self._bit)
        bool_value = not bool_value if self._invert else bool_value
        return bool_value


class S7StatusBinaryEntity(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor representing a S7 binary."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator, description: BinarySensorEntityDescription):
        """Initialize an S7 binary."""
        super().__init__(coordinator)
        self.entity_description = description

        # Rely on the parent class implementation for these attributes
        self._attr_name = description.name
        self._attr_device_class = description.device_class
        self._attr_unique_id = description.key
        self._attr_device_info = coordinator.get_device()

    @property
    def is_on(self):

        if not isinstance(self.coordinator.data, MutableMapping):
            return None
        if self.coordinator.data.get(self._attr_unique_id) is None:
            return None

        """Return if key from coorindator."""
        return self.coordinator.data[self._attr_unique_id]
