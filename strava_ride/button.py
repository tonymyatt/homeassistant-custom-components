"""Support for Strava buttons."""

import logging
import pprint

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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

    for ha_id, name in coordinator.data["gear_ids"].items():
        async_add_entities(
            [
                GearServiceResetCommand(coordinator, name, ha_id, description)
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
        object: str,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the Strava sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self.object_name = f"{object}_{description.key}_reset"
        self.gear_service_key = f"{object}_{description.key}"
        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = f"{object}_{description.key}_reset"
        self._attr_device_info = self.coordinator.get_device()

    async def async_press(self):
        """Handle the button press."""
        await self.coordinator.reset_gear_service(self.gear_service_key)
