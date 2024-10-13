"""Support for Strava buttons."""

from datetime import datetime
import logging

from dateutil.parser import parse as dt_parse

from homeassistant.components.datetime import DateTimeEntity, DateTimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, GEAR_DATETIME_ENTITIES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Strava datetime platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    for ha_id, gear in coordinator.data["gear_ids"].items():
        async_add_entities(
            [
                GearServiceDateTime(
                    coordinator, gear["name"], ha_id, gear["strava_id"], description
                )
                for description in GEAR_DATETIME_ENTITIES
            ],
            False,
        )


class GearServiceDateTime(CoordinatorEntity, DateTimeEntity, RestoreEntity):
    """Strava Gear Last Service Datetime"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        name: str,
        entity_name: str,
        strava_id: str,
        description: DateTimeEntityDescription,
    ) -> None:
        """Initialize the Strava sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.object_name = f"{entity_name}_{description.key}"
        self.gear_service_attr = description.key
        self.gear_strava_id = strava_id
        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = f"{entity_name}_{description.key}"
        self._attr_device_info = self.coordinator.get_device(entity_name)

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the entity."""
        return (
            self.coordinator.data["gear_stats"][self.object_name]["service_date"]
            if self.coordinator.data
            else None
        )

    async def async_set_value(self, value: datetime) -> None:
        """Change the date/time."""
        await self.coordinator.set_gear_service_date(
            self.gear_strava_id,
            self.gear_service_attr,
            value,
        )

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not state:
            return

        # Parse the stored date and update with the coorindator
        prev_date = dt_parse(state.state)

        await self.coordinator.set_gear_service_date(
            self.gear_strava_id, self.gear_service_attr, prev_date
        )
