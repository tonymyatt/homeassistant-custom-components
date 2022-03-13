"""Constants for the Tony M integration."""
from datetime import timedelta
from typing import Final


class StravaField:

    name: str
    units: str
    key: str

    def __init__(self, name: str, units: str, key: str):
        self.name = name
        self.units = units
        self.key = key


DOMAIN = "tonym"

SCAN_INTERVAL: Final = timedelta(minutes=15)

STRAVA = "strava_"
WEEK = "week_"
LWEEK = "lweek_"
TIME = "time_"
DIST = "dist_"
ELEV = "elev_"
DELTA = "delta_"

LWEEK_DIST = StravaField("Cycling Last Week Distance", "km", "strava_last_week_km")
# e.add_extra_state_attribute("Last Week Delta", "%", "strava_week_km_delta")
LWEEK_TIME = StravaField("Cycling Last Week Time", "hrs", "strava_last_week_hrs")

WEEK_DIST = StravaField("Cycling Week Distance", "km", "strava_week_km")
# e.add_extra_state_attribute("Last Week Delta", "%", "strava_week_km_delta")
WEEK_TIME = StravaField("Cycling Week Time", "hrs", "strava_week_hrs")
