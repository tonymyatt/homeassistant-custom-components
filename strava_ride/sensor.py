"""Support for Strava sensor."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, GEAR_SENSOR_ENTITIES, SUMMARY_ENTITIES, WEEKLY_ENTITIES


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Strava sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            StravaSummarySensor(coordinator, description)
            for description in SUMMARY_ENTITIES
        ],
        False,
    )

    for ha_id, gear in coordinator.data["gear_ids"].items():
        async_add_entities(
            [
                StravaGearSensor(coordinator, gear["name"], ha_id, description)
                for description in GEAR_SENSOR_ENTITIES
            ],
            False,
        )

    async_add_entities(
        [
            StravaWeeklySensor(coordinator, "This Week", "this_week", description)
            for description in WEEKLY_ENTITIES
        ],
        False,
    )

    async_add_entities(
        [
            StravaWeeklySensor(coordinator, "Last Week", "last_week", description)
            for description in WEEKLY_ENTITIES
        ],
        False,
    )


class StravaSummarySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Strava sensor."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, description: SensorEntityDescription
    ) -> None:
        """Initialize the Strava sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{description.name}"
        self._attr_unique_id = f"{description.key}"
        self._attr_device_info = self.coordinator.get_device()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return (
            self.coordinator.data["summary_stats"][self.entity_description.key]
            if self.coordinator.data
            else None
        )


class StravaWeeklySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Strava sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        name: str,
        object: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the Strava sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.object_name = object
        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = f"{object}_{description.key}"
        self._attr_device_info = self.coordinator.get_device()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return (
            getattr(
                self.coordinator.data["weekly_stats"][self.object_name],
                self.entity_description.key,
            )
            if self.coordinator.data
            else None
        )


class StravaGearSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Strava gear sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        name: str,
        object: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the Strava sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.object_name = f"{object}_{description.key}"
        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = f"{object}_{description.key}"
        self._attr_device_info = self.coordinator.get_device(object)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        key = "time"
        if self.device_class == SensorDeviceClass.DISTANCE:
            key = "distance"

        return (
            self.coordinator.data["gear_stats"][self.object_name][key]
            if self.coordinator.data
            else None
        )
