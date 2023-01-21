"""Support for number input to S7 PLC."""
import logging

from homeassistant.components.button import (
    ButtonEntity,
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
from .s7comm import S7Bool, S7Comm, S7DWord, S7Word

_LOGGER = logging.getLogger(__name__)

MAN_START_CMD = 1
FORCE_AUTO_CMD = 4


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Step 7 PLC entities."""
    _LOGGER.debug("Setting up Step7 PLC Button entities")
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
            S7WateringCmdEntity(
                coordinator,
                description,
                "Equipment to Automatic",
                FORCE_AUTO_CMD,
            )
            for description in HA_WATERING_AREAS
        ]
    )
    async_add_entities(
        [
            S7WateringCmdEntity(
                coordinator,
                description,
                "Manual Start",
                MAN_START_CMD,
            )
            for description in HA_WATERING_AREAS
        ]
    )


class S7IntCommandEntity(CoordinatorEntity, ButtonEntity):
    """Home Assistant Command as integer in a S7 PLC."""

    def __init__(
        self,
        coordinator,
        name: str,
        db_number: int,
        byte: int,
        command: int,
        device=None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._command = command
        self._s7_command = S7Word(db_number, byte)

        # Rely on the parent class implementation for these attributes
        self._attr_name = name
        addr = f"DB{db_number}.DBW{byte}"
        self._attr_unique_id = f"{addr}_write_{command}"
        self._attr_extra_state_attributes = {"S7 address": addr}
        if device is None:
            self._attr_device_info = coordinator.get_device()
        else:
            self._attr_device_info = device

    async def async_press(self):
        """Handle the button press."""
        await self.coordinator.write_int(self._s7_command, self._command)


class S7WateringCmdEntity(S7IntCommandEntity):
    """Home Assistant Command as integer in a S7 PLC Watering block."""

    CMD_S7_BYTE = 10

    def __init__(
        self,
        coordinator,
        description: HAWateringAreaDescription,
        command_str: str,
        command: int,
    ) -> None:
        super().__init__(
            coordinator,
            f"{description.name} {command_str}",
            description.s7datablock,
            self.CMD_S7_BYTE,
            command,
            description.device,
        )
