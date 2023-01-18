from dataclasses import dataclass
from enum import Enum
from datetime import timedelta
from typing import Final
from homeassistant.helpers.entity import EntityDescription
from homeassistant.components.sensor import SensorStateClass, SensorEntityDescription
from homeassistant.components.cover import CoverDeviceClass
from homeassistant.components.binary_sensor import (
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import (
    LENGTH_MILLIMETERS,
    ELECTRIC_POTENTIAL_VOLT,
    TEMP_CELSIUS,
)
from .s7comm import S7Addr

"""Constants for the Step7 PLC integration."""

DOMAIN = "s7comm"
SCAN_INTERVAL: Final = timedelta(seconds=1)


@dataclass
class S7Interlocks:
    description: str = "Unknown"
    number: int = None

    @property
    def name(self) -> str:
        return f"Interlock {self.number}"


@dataclass
class S7SensorEntityDescription(SensorEntityDescription):
    """A class that describes s7 sensor entities."""

    s7datablock: int = None
    s7address: int = None
    s7datatype: str = None


@dataclass
class HAGenericEntityDescription(EntityDescription):
    """A class that describes S7 device objects."""

    s7datablock: int = None
    s7readbytes: int = None
    disable_switch: bool = False


@dataclass
class HAWateringAreaDescription(EntityDescription):
    """A class that describes S7 Water Area objects."""

    s7datablock: int = None
    s7readbytes: int = None

    @property
    def device(self) -> DeviceInfo:
        """Return the HA device for this object"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.key)},
            name=self.name,
            manufacturer="Siemens S7/1200",
            model="Watering Area",
        )


interlock_template = [
    S7Interlocks(number=1),
    S7Interlocks(number=2),
    S7Interlocks(number=3),
    S7Interlocks(number=4),
    S7Interlocks(number=5),
    S7Interlocks(number=6),
    S7Interlocks(number=7),
    S7Interlocks(number=8),
    S7Interlocks(number=9),
    S7Interlocks(number=10),
    S7Interlocks(number=11),
    S7Interlocks(number=12),
    S7Interlocks(number=13),
    S7Interlocks(number=14),
    S7Interlocks(number=15),
    S7Interlocks(number=16),
]

HA_WATERING_AREAS: tuple[HAWateringAreaDescription] = (
    HAWateringAreaDescription(
        key="watering_herb",
        name="Watering Herb Garden",
        s7datablock=45,
        s7readbytes=30,
    ),
    HAWateringAreaDescription(
        key="watering_back_tap",
        name="Watering Back Tap",
        s7datablock=46,
        s7readbytes=30,
    ),
    HAWateringAreaDescription(
        key="watering_orchard",
        name="Watering Orchard",
        s7datablock=48,
        s7readbytes=30,
    ),
    HAWateringAreaDescription(
        key="watering_front_yard",
        name="Watering Front Yard",
        s7datablock=8,
        s7readbytes=30,
    ),
    HAWateringAreaDescription(
        key="watering_front_tap",
        name="Watering Front Tap",
        s7datablock=49,
        s7readbytes=30,
    ),
)

HA_COVER_ENTITIES: tuple[HAGenericEntityDescription] = (
    HAGenericEntityDescription(
        key="nerrilee_garage_door",
        name="Nerrilee Garage Door",
        device_class=CoverDeviceClass.GARAGE,
        s7datablock=9,
        s7readbytes=22,
    ),
    HAGenericEntityDescription(
        key="tony_garage_door",
        name="Tony Garage Door",
        device_class=CoverDeviceClass.GARAGE,
        s7datablock=10,
        s7readbytes=22,
        disable_switch=True,
    ),
    HAGenericEntityDescription(
        key="tank_to_orchard_valve",
        name="Tank to Orchard Valve",
        device_class=CoverDeviceClass.DAMPER,
        icon="mdi:pipe-valve",
        s7datablock=11,
        s7readbytes=22,
        disable_switch=True,
    ),
    HAGenericEntityDescription(
        key="herb_garden_valve",
        name="Herb Garden Valve",
        device_class=CoverDeviceClass.DAMPER,
        icon="mdi:pipe-valve",
        s7datablock=12,
        s7readbytes=22,
        disable_switch=True,
    ),
    HAGenericEntityDescription(
        key="downpipe_drain_valve",
        name="Downpipe Drain Valve",
        device_class=CoverDeviceClass.DAMPER,
        icon="mdi:pipe-valve",
        s7datablock=16,
        s7readbytes=22,
        disable_switch=True,
    ),
    HAGenericEntityDescription(
        key="watering_mains_valve",
        name="Watering Mains Valve",
        device_class=CoverDeviceClass.DAMPER,
        icon="mdi:pipe-valve",
        s7datablock=18,
        s7readbytes=22,
        disable_switch=True,
    ),
    HAGenericEntityDescription(
        key="back_tap_valve",
        name="Back Tap Valve",
        device_class=CoverDeviceClass.DAMPER,
        icon="mdi:pipe-valve",
        s7datablock=20,
        s7readbytes=22,
        disable_switch=True,
    ),
    HAGenericEntityDescription(
        key="front_yard_valve",
        name="Front Yard Valve",
        device_class=CoverDeviceClass.DAMPER,
        icon="mdi:pipe-valve",
        s7datablock=25,
        s7readbytes=22,
        disable_switch=True,
    ),
    HAGenericEntityDescription(
        key="front_tap_valve",
        name="Front Tap Valve",
        device_class=CoverDeviceClass.DAMPER,
        icon="mdi:pipe-valve",
        s7datablock=26,
        s7readbytes=22,
        disable_switch=True,
    ),
)

HA_DEVICE2_ENTITIES: tuple[HAGenericEntityDescription] = (
    HAGenericEntityDescription(
        key="watering_pump",
        name="Watering Pump",
        icon="mdi:pump",
        s7datablock=28,
        s7readbytes=18,
        disable_switch=True,
    ),
)

STATUS_BINARY_ENTITIES: tuple[BinarySensorEntityDescription] = (
    BinarySensorEntityDescription(
        key="CPU_STATE",
        name="S7 CPU Status",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:play-pause",
    ),
    BinarySensorEntityDescription(
        key="COMMS_STATUS",
        name="S7 Communication Fail",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert",
    ),
)

SENSOR_REAL_ENTITIES: tuple[S7SensorEntityDescription] = (
    S7SensorEntityDescription(
        key="rain_today",
        name="Rain Today",
        native_unit_of_measurement=LENGTH_MILLIMETERS,
        icon="mdi:ruler",
        state_class=SensorStateClass.TOTAL_INCREASING,
        s7datablock=40,
        s7address=30,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="rain_month",
        name="Rain Month",
        native_unit_of_measurement=LENGTH_MILLIMETERS,
        icon="mdi:ruler",
        state_class=SensorStateClass.TOTAL_INCREASING,
        s7datablock=40,
        s7address=34,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="rain_month",
        name="Rain Year",
        native_unit_of_measurement=LENGTH_MILLIMETERS,
        icon="mdi:ruler",
        state_class=SensorStateClass.TOTAL_INCREASING,
        s7datablock=40,
        s7address=38,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="rain_yesterday",
        name="Rain Yesterday",
        native_unit_of_measurement=LENGTH_MILLIMETERS,
        icon="mdi:ruler",
        state_class=SensorStateClass.TOTAL_INCREASING,
        s7datablock=40,
        s7address=42,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="rain_lastmonth",
        name="Rain Last Month",
        native_unit_of_measurement=LENGTH_MILLIMETERS,
        icon="mdi:ruler",
        state_class=SensorStateClass.TOTAL_INCREASING,
        s7datablock=40,
        s7address=46,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="rain_lastyear",
        name="Rain Last Year",
        native_unit_of_measurement=LENGTH_MILLIMETERS,
        icon="mdi:ruler",
        state_class=SensorStateClass.TOTAL_INCREASING,
        s7datablock=40,
        s7address=50,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="tank_level",
        name="Tank Level",
        native_unit_of_measurement="%",
        icon="mdi:ruler",
        state_class=SensorStateClass.MEASUREMENT,
        s7datablock=202,
        s7address=42,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="camper_trailer_battery_voltage",
        name="Camper Trailer Battery Voltage",
        native_unit_of_measurement=ELECTRIC_POTENTIAL_VOLT,
        icon="mdi:ruler",
        state_class=SensorStateClass.MEASUREMENT,
        s7datablock=60,
        s7address=42,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="outside_temperature",
        name="Outside Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        icon="mdi:ruler",
        state_class=SensorStateClass.MEASUREMENT,
        s7datablock=22,
        s7address=42,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="outside_temperature_rate_of_change",
        name="Outside Temperature Rate of Change",
        native_unit_of_measurement="°C/h",
        icon="mdi:ruler",
        state_class=SensorStateClass.MEASUREMENT,
        s7datablock=32,
        s7address=12,
        s7datatype="real",
    ),
    S7SensorEntityDescription(
        key="tank_pump_flow_calc",
        name="Tank Pump Calculated Flow",
        native_unit_of_measurement="L/s",
        icon="mdi:waves-arrow-right",
        state_class=SensorStateClass.MEASUREMENT,
        s7datablock=19,
        s7address=42,
        s7datatype="real",
    ),
)
