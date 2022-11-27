from dataclasses import dataclass
from datetime import timedelta
from typing import Final
from homeassistant.components.sensor import SensorStateClass, SensorEntityDescription
from homeassistant.components.binary_sensor import (
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)
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
class S7SensorEntityDescription(SensorEntityDescription):
    """A class that describes s7 sensor entities."""

    s7datablock: int = None
    s7address: int = None
    s7datatype: str = None


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
)
