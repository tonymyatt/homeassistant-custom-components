"""Support for number input to S7 PLC."""
import logging

from homeassistant.components.number import (
    NumberMode,
    NumberEntity,
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
    HA_WATERING_AREAS,
    HAWateringAreaDescription,
)
from .s7comm import S7Word

_LOGGER = logging.getLogger(__name__)

MIN_START_HOURS = 0
MAX_START_HOURS = 23
MIN_RUN_MINS = 0
MAX_RUN_MINS = 1440


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

    # Watering areas
    async_add_entities(
        [
            HaWateringAreaStartTime(coordinator, description)
            for description in HA_WATERING_AREAS
        ]
    )
    async_add_entities(
        [
            HaWateringRunTime(coordinator, description, day)
            for day in INT_TO_DAY_MAP
            for description in HA_WATERING_AREAS
        ]
    )


INT_TO_DAY_MAP = {
    0: "Manual",
    1: "Sunday",
    2: "Monday",
    3: "Tuesday",
    4: "Wednesday",
    5: "Thursday",
    6: "Friday",
    7: "Saturday",
}


class HaWateringRunTime(CoordinatorEntity, NumberEntity):
    """Representation of a watering area daily run time."""

    def __init__(
        self, coordinator, description: HAWateringAreaDescription, day
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._db_number = description.s7datablock

        # Addresses in the DB
        self._s7_run_minutes = S7Word(description.s7datablock, 16 + (day - 1) * 2)

        # Rely on the parent class implementation for these attributes
        self._attr_name = f"{description.name} {day} {INT_TO_DAY_MAP[day]}"
        self._attr_unique_id = f"DB{self._db_number}_{day}_run_mins"
        self._attr_device_info = description.device
        self._attr_icon = "mdi:calendar-clock"
        self._attr_native_max_value = MAX_RUN_MINS
        self._attr_native_min_value = MIN_RUN_MINS
        self._attr_native_unit_of_measurement = "min"

    @property
    def native_value(self) -> int:
        """Return the run time in minutes."""
        return self.coordinator.get_int(self._s7_run_minutes)

    async def async_set_native_value(self, value: float) -> None:
        """Set the run time in minutes."""
        if not value.is_integer():
            raise ValueError(
                f"Can't set the start hour to {value}. Start hour must be an integer."
            )
        await self.coordinator.write_int(self._s7_run_minutes, int(value))


class HaWateringAreaStartTime(CoordinatorEntity, NumberEntity):
    """Representation of a watering area start time."""

    def __init__(self, coordinator, description: HAWateringAreaDescription) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._db_number = description.s7datablock

        # Addresses in the DB
        self._s7_start_hour = S7Word(description.s7datablock, 12)

        # Rely on the parent class implementation for these attributes
        self._attr_name = description.name + " Start Hour"
        self._attr_unique_id = f"DB{self._db_number}_start_hour"
        self._attr_device_info = description.device
        self._attr_icon = "mdi:progress-clock"
        self._attr_native_max_value = MAX_START_HOURS
        self._attr_native_min_value = MIN_START_HOURS
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> int:
        """Return the current start hour."""
        return self.coordinator.get_int(self._s7_start_hour)

    async def async_set_native_value(self, value: float) -> None:
        """Set the start hour."""
        if not value.is_integer():
            raise ValueError(
                f"Can't set the start hour to {value}. Start hour must be an integer."
            )
        await self.coordinator.write_int(self._s7_start_hour, int(value))
