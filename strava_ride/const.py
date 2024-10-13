"""Constants for the Strava integration."""

from datetime import timedelta

from homeassistant.components.datetime import DateTimeEntityDescription
from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTime

DOMAIN = "strava_ride"

SCAN_INTERVAL = timedelta(minutes=10)

# OAuth Specs
OAUTH2_AUTHORIZE = "https://www.strava.com/oauth/authorize"
OAUTH2_TOKEN = "https://www.strava.com/oauth/token"

MAX_NB_ACTIVITIES = 200

GEAR_SERVICE_KEYS: tuple[str] = (
    "service_dist_1",
    "service_dist_2",
    "service_dist_3",
    "service_dist_4",
    "service_dist_5",
    "service_time_1",
    "service_time_2",
    "service_time_3",
)

GEAR_RESET_ENTITIES: tuple[ButtonEntityDescription] = (
    ButtonEntityDescription(
        key="service_dist_1",
        name="Chain Serviced",
        icon="mdi:autorenew",
    ),
    ButtonEntityDescription(
        key="service_dist_2",
        name="Front Tyre Changed",
        icon="mdi:autorenew",
    ),
    ButtonEntityDescription(
        key="service_dist_3",
        name="Rear Tyre Changed",
        icon="mdi:autorenew",
    ),
    ButtonEntityDescription(
        key="service_dist_4",
        name="Shop Service Completed",
        icon="mdi:autorenew",
        entity_registry_enabled_default=False,
    ),
    ButtonEntityDescription(
        key="service_dist_5",
        name="Spare Distance Service Completed",
        icon="mdi:autorenew",
        entity_registry_enabled_default=False,
    ),
    ButtonEntityDescription(
        key="service_time_1",
        name="Minor Service Completed",
        icon="mdi:autorenew",
    ),
    ButtonEntityDescription(
        key="service_time_2",
        name="Major Service Completed",
        icon="mdi:autorenew",
    ),
    ButtonEntityDescription(
        key="service_time_3",
        name="Shop Service Completed",
        icon="mdi:autorenew",
    ),
)

GEAR_DATETIME_ENTITIES: tuple[DateTimeEntityDescription] = (
    DateTimeEntityDescription(
        key="service_dist_1_date",
        name="Chain Last Service",
        icon="mdi:calendar-check",
    ),
    DateTimeEntityDescription(
        key="service_dist_2_date",
        name="Front Tyre Last Change",
        icon="mdi:calendar-check",
    ),
    DateTimeEntityDescription(
        key="service_dist_3_date",
        name="Rear Tyre Last Change",
        icon="mdi:calendar-check",
    ),
    DateTimeEntityDescription(
        key="service_dist_4_date",
        name="Shop Service Distance",
        icon="mdi:calendar-check",
        entity_registry_enabled_default=False,
    ),
    DateTimeEntityDescription(
        key="service_dist_5_date",
        name="Spare Distance",
        icon="mdi:calendar-check",
        entity_registry_enabled_default=False,
    ),
    DateTimeEntityDescription(
        key="service_time_1_date",
        name="Minor Service Time",
        icon="mdi:calendar-check",
    ),
    DateTimeEntityDescription(
        key="service_time_2_date",
        name="Major Service Time",
        icon="mdi:calendar-check",
    ),
    DateTimeEntityDescription(
        key="service_time_3_date",
        name="Shop Service Time",
        icon="mdi:calendar-check",
    ),
)

GEAR_SENSOR_ENTITIES: tuple[SensorEntityDescription] = (
    SensorEntityDescription(
        key="distance",
        name="Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:ruler",
        device_class=SensorDeviceClass.DISTANCE,
    ),
    SensorEntityDescription(
        key="service_dist_1",
        name="Chain Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:link-variant",
        device_class=SensorDeviceClass.DISTANCE,
    ),
    SensorEntityDescription(
        key="service_dist_2",
        name="Front Tyre Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:tire",
        device_class=SensorDeviceClass.DISTANCE,
    ),
    SensorEntityDescription(
        key="service_dist_3",
        name="Rear Tyre Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:tire",
        device_class=SensorDeviceClass.DISTANCE,
    ),
    SensorEntityDescription(
        key="service_dist_4",
        name="Shop Service Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:bike",
        device_class=SensorDeviceClass.DISTANCE,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="service_dist_5",
        name="Spare Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:bike",
        device_class=SensorDeviceClass.DISTANCE,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="service_time_1",
        name="Minor Service Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer-cog-outline",
        # device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="service_time_2",
        name="Major Service Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:wrench-clock-outline",
        # evice_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="service_time_3",
        name="Shop Service Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:wrench-clock-outline",
        # device_class=SensorDeviceClass.DURATION,
    ),
)

WEEKLY_ENTITIES: tuple[SensorEntityDescription] = (
    SensorEntityDescription(
        key="distance",
        name="Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:ruler",
    ),
    SensorEntityDescription(
        key="distance_delta",
        name="Distance Delta",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:ruler-square-compass",
    ),
    SensorEntityDescription(
        key="time",
        name="Moving Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer",
    ),
    SensorEntityDescription(
        key="time_delta",
        name="Moving Time Delta",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:clock-start",
    ),
    SensorEntityDescription(
        key="elevation",
        name="Elevation Gain",
        native_unit_of_measurement=UnitOfLength.METERS,
        icon="mdi:elevation-rise",
    ),
    SensorEntityDescription(
        key="climbing",
        name="Climbing",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:slope-uphill",
    ),
)

SUMMARY_ENTITIES: tuple[SensorEntityDescription] = (
    SensorEntityDescription(
        key="all_ride_totals_count", name="Ride All Time Count", icon="mdi:numeric"
    ),
    SensorEntityDescription(
        key="all_ride_totals_distance",
        name="Ride All Time Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:ruler",
    ),
    SensorEntityDescription(
        key="all_ride_totals_elapsed_time",
        name="Ride All-Time Elapsed Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="all_ride_totals_elevation_gain",
        name="Ride All-Time Elevation Gain",
        native_unit_of_measurement=UnitOfLength.METERS,
        icon="mdi:elevation-rise",
    ),
    SensorEntityDescription(
        key="all_ride_totals_moving_time",
        name="Ride All-Time Moving Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer",
    ),
    SensorEntityDescription(
        key="biggest_climb_elevation_gain",
        name="Ride Biggest Elevation Gain",
        native_unit_of_measurement=UnitOfLength.METERS,
        icon="mdi:elevation-rise",
    ),
    SensorEntityDescription(
        key="biggest_ride_distance",
        name="Ride Biggest Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:ruler",
    ),
    SensorEntityDescription(
        key="ytd_ride_totals_count", name="Ride YTD Count", icon="mdi:numeric"
    ),
    SensorEntityDescription(
        key="ytd_ride_totals_distance",
        name="Ride YTD Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:ruler",
    ),
    SensorEntityDescription(
        key="ytd_ride_totals_elapsed_time",
        name="Ride YTD Elapsed Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="ytd_ride_totals_elevation_gain",
        name="Ride YTD Elevation Gain",
        native_unit_of_measurement=UnitOfLength.METERS,
    ),
    SensorEntityDescription(
        key="ytd_ride_totals_moving_time",
        name="Ride YTD Moving Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer",
    ),
    SensorEntityDescription(
        key="recent_ride_totals_count",
        name="Ride Last 4 Weeks Count",
        icon="mdi:numeric",
    ),
    SensorEntityDescription(
        key="recent_ride_totals_distance",
        name="Ride Last 4 Weeks Distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        icon="mdi:ruler",
    ),
    SensorEntityDescription(
        key="recent_ride_totals_elapsed_time",
        name="Ride Last 4 Weeks Elapsed Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="recent_ride_totals_elevation_gain",
        name="Ride Last 4 Weeks Elevation Gain",
        native_unit_of_measurement=UnitOfLength.METERS,
        icon="mdi:elevation-rise",
    ),
    SensorEntityDescription(
        key="recent_ride_totals_moving_time",
        name="Ride Last 4 Weeks Moving Time",
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer",
    ),
)
