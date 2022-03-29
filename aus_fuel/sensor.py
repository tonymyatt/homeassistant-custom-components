"""Support for Australian Fuel Price sensor."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .aus_fuel_api import AusFuelPrice

from .const import DOMAIN
import pprint


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Australian Fuel Price sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            AusFuelPriceSensor(coordinator, key, fuel_entry)
            for (key, fuel_entry) in coordinator.data["prices"].items()
        ]
    )


class AusFuelPriceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Australian Fuel Price sensor."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, key: str, price_entry: AusFuelPrice
    ) -> None:
        """Initialize the Aus Fueld Price sensor."""
        super().__init__(coordinator)
        self.price_entry = price_entry
        self.price_id = key
        self._attr_name = f"{price_entry.name} {price_entry.fuel_type}"
        self._attr_unique_id = key
        self._attr_native_unit_of_measurement = "c/L"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_extra_state_attributes = {
            "name": price_entry.name,
            "address": price_entry.address,
            "brand": price_entry.brand,
            "latitude": price_entry.latitude,
            "longitude": price_entry.longitude,
        }
        if "Diesel" in price_entry.fuel_type:
            self._attr_icon = "mdi:truck"
        elif "E10" in price_entry.fuel_type:
            self._attr_icon = "mdi:gas-station-outline"
        else:
            self._attr_icon = "mdi:gas-station"

    @property
    def device_info(self):
        """Return the device info."""
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, self.price_entry.name)},
            manufacturer=self.price_entry.brand,
            model=self.price_entry.address,
            name=self.price_entry.name,
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return (
            getattr(self.coordinator.data["prices"][self.price_id], "price")
            if self.coordinator.data
            else None
        )
