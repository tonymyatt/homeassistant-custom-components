"""Support for Strava buttons."""

import logging
import pprint
from datetime import datetime

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, GEAR_RESET_ENTITIES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Strava button platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    for ha_id, gear in coordinator.data["gear_ids"].items():
        async_add_entities(
            [
                GearServiceResetCommand(
                    coordinator, gear["name"], ha_id, gear["strava_id"], description
                )
                for description in GEAR_RESET_ENTITIES
            ],
            False,
        )


class GearServiceResetCommand(CoordinatorEntity, ButtonEntity):
    """Strava Gear Service Reset Command"""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        name: str,
        entity_name: str,
        strava_id: str,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the Strava sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.object_name = f"{entity_name}_{description.key}_reset"
        self.gear_service_attr = description.key
        self.gear_strava_id = strava_id
        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = f"{entity_name}_{description.key}_reset"
        self._attr_device_info = self.coordinator.get_device(entity_name)

    async def async_press(self):
        """Handle the button press."""
        await self.coordinator.set_gear_service_date(
            self.gear_strava_id,
            self.gear_service_attr,
            datetime.now(tz=dt_util.get_default_time_zone()),
        )
