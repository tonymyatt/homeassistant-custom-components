from __future__ import annotations

import json
import logging
import pprint
from datetime import datetime as dt, date, timedelta

from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.components.sensor import SensorDeviceClass

from .const import MAX_NB_ACTIVITIES, GEAR_SERVICE_KEYS

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class CycleGearService:
    """Represents a serviceable item on a bike."""

    distance: int = 0
    time: int = 0
    service_date: dt = dt(2024, 8, 1, 13, 0, 0)

    def add_activity(self, act_date: dt, act_dist: int, act_time: int):
        """Add an activities distance time to this service, dependant on date."""
        if act_date >= self.service_date:
            self.distance += act_dist
            self.time += act_time

    def __repr__(self) -> str:
        return f"CycleGearService time:{self.time}; distance:{self.distance}; service_date:{self.service_date}"


class CycleGear:
    """Represents a bike (Strava Gear item)."""

    name: str = "Unknown Name"
    ha_id: str = None
    distance: int = 0
    service_dist_1: CycleGearService
    service_dist_2: CycleGearService
    service_dist_3: CycleGearService
    service_dist_4: CycleGearService
    service_dist_5: CycleGearService
    service_time_1: CycleGearService
    service_time_2: CycleGearService
    service_time_3: CycleGearService

    def __init__(self) -> None:
        """Create a cycle gear object."""
        self.service_dist_1 = CycleGearService()
        self.service_dist_2 = CycleGearService()
        self.service_dist_3 = CycleGearService()
        self.service_dist_4 = CycleGearService()
        self.service_dist_5 = CycleGearService()
        self.service_time_1 = CycleGearService()
        self.service_time_2 = CycleGearService()
        self.service_time_3 = CycleGearService()

    def add_activity(self, act_date: dt, act_dist: int, act_time: int):
        """Add an activities distance time to service items, dependant on date."""
        self.service_dist_1.add_activity(act_date, act_dist, act_time)
        self.service_dist_2.add_activity(act_date, act_dist, act_time)
        self.service_dist_3.add_activity(act_date, act_dist, act_time)
        self.service_dist_4.add_activity(act_date, act_dist, act_time)
        self.service_dist_5.add_activity(act_date, act_dist, act_time)
        self.service_time_1.add_activity(act_date, act_dist, act_time)
        self.service_time_2.add_activity(act_date, act_dist, act_time)
        self.service_time_3.add_activity(act_date, act_dist, act_time)

    def __repr__(self) -> str:
        return f"CycleGear {self.name} {self.service_dist_1} {self.service_dist_2} {self.service_dist_3} {self.service_dist_4} {self.service_dist_5} {self.service_time_1} {self.service_time_2} {self.service_time_3}"


class CycleWeekStats:
    distance = 0
    distance_delta = 0
    time = 0
    time_delta = 0
    elevation = 0

    @property
    def climbing(self) -> float:
        climb = 0
        if self.distance > 0:
            climb = round(self.elevation / self.distance / 10, 1)
        return climb


class StravaAPI:
    """
    API to read data from Strava API
    """

    _gear_service_dates = {}

    _strava_ride_activities: list = []
    _strava_ride_gear: dict[str, CycleGear] = {}
    _strava_athlete_id: int = None

    def __init__(
        self,
        oauth_websession: config_entry_oauth2_flow.OAuth2Session,
    ):
        """Init the Object."""
        self.oauth_websession = oauth_websession

    async def set_gear_service_date(self, service_key, service_date):
        pprint.pprint(f"{service_key} set to {service_date}, now recalc")
        self._gear_service_dates[service_key] = service_date

    async def fetch_ride_activities(self):
        """Fetch ride activities from the Strava API, using adding found gear to the list."""

        _LOGGER.debug("Fetching Data from Strava API")

        activities_response = await self.oauth_websession.async_request(
            method="GET",
            url=f"https://www.strava.com/api/v3/athlete/activities?per_page={MAX_NB_ACTIVITIES}",
        )

        # Exit on rate limit, cannot update data
        if activities_response.status == 429:
            _LOGGER.warning(
                "Strava API rate limit has been reached why requesting activities"
            )
            return

        # Otherwise, existing logging message if not a good response
        if activities_response.status != 200:
            _LOGGER.error(
                f"Could not fetch strava activities (response code: {activities_response.status}): {await activities_response.text()}"
            )
            return

        json_data = json.loads(await activities_response.text())
        for activity in json_data:
            self._strava_athlete_id = int(activity["athlete"]["id"])

        # Create a list of ride activities only
        for idx, activity in enumerate(json_data):
            if activity["type"] != "Ride":
                continue
            self._strava_ride_activities.append(activity)

        # Make sure the gear dict contains all gear from ride activities
        for a in self._strava_ride_activities:
            gear_id = a["gear_id"]

            # Check if this gear id has been found already, if not setup
            if gear_id not in self._strava_ride_gear:
                self._strava_ride_gear[gear_id] = CycleGear()

    async def fetch_gear_information(self):
        """Retrieve all gear information based on known id's from strava API."""

        # Load the name and overall distance of all gear
        for gear_id, gear in self._strava_ride_gear.items():
            api_response = await self.oauth_websession.async_request(
                method="GET",
                url=f"https://www.strava.com/api/v3/gear/{gear_id}",
            )

            # Exit on rate limit, cannot update data
            if api_response.status == 429:
                _LOGGER.warning(
                    f"Strava API rate limit has been reached when requesting gear {gear_id}"
                )
                return

            # Otherwise, existing logging message if not a good response
            if api_response.status != 200:
                _LOGGER.error(
                    f"Could not fetch strava gear (response code: {api_response.status}): {await api_response.text()}"
                )
                return

            json_gear = json.loads(await api_response.text())
            gear.name = json_gear["name"]
            name = json_gear["name"]
            name = name.replace(" ", "_")
            name = name.lower()
            gear.ha_id = name
            gear.distance = int(json_gear["distance"] / 1000)

    def calc_gear_service(self):
        """Calculate gear service times and distances from loaded activities."""
        # Make sure the gear dict contains all gear from ride activities
        for a in self._strava_ride_activities:
            gear_id = a["gear_id"]

            # activity date and time
            act_date = dt.strptime(a["start_date_local"], "%Y-%m-%dT%H:%M:%SZ")
            distance = round(a["distance"] / 1000, 1)
            moving_time = round(a["moving_time"] / 3600, 2)

            # Add the activity distance and time to the gear
            self._strava_ride_gear[gear_id].add_activity(
                act_date, distance, moving_time
            )

    def _calc_weekly_strava_stats(self):
        weekly_data: dict = {}

        for mon_date in self._last_2years_mondays():
            weekly_data[mon_date] = {"distance": 0, "time": 0, "elevation": 0}
            for a in self._strava_ride_activities:
                # activity date and time
                act_date = dt.strptime(a["start_date_local"], "%Y-%m-%dT%H:%M:%SZ")
                distance = round(a["distance"] / 1000, 1)
                moving_time = round(a["moving_time"] / 3600, 2)

                #  increment weekly info
                act_date = date(act_date.year, act_date.month, act_date.day)
                if act_date >= mon_date and act_date < mon_date + timedelta(7):
                    weekly_data[mon_date]["distance"] += distance
                    weekly_data[mon_date]["time"] += moving_time
                    weekly_data[mon_date]["elevation"] += int(a["total_elevation_gain"])

        mon_this_week = date.today() + timedelta(0 - date.today().weekday())
        mon_last_week = mon_this_week + timedelta(-7)
        mon_last_fnight = mon_last_week + timedelta(-7)

        last_week = CycleWeekStats()
        last_week.distance = weekly_data[mon_last_week]["distance"]
        last_week.distance_delta = round(
            last_week.distance / weekly_data[mon_last_fnight]["distance"] * 100, 1
        )
        last_week.time = weekly_data[mon_last_week]["time"]
        last_week.time_delta = round(
            last_week.time / weekly_data[mon_last_fnight]["time"] * 100, 1
        )
        last_week.elevation = weekly_data[mon_last_week]["elevation"]

        this_week = CycleWeekStats()
        this_week.distance = weekly_data[mon_this_week]["distance"]
        this_week.distance_delta = round(
            this_week.distance / weekly_data[mon_last_week]["distance"] * 100, 1
        )
        this_week.time = weekly_data[mon_this_week]["time"]
        this_week.time_delta = round(
            this_week.time / weekly_data[mon_last_week]["time"] * 100, 1
        )
        this_week.elevation = weekly_data[mon_this_week]["elevation"]

        return {"last_week": last_week, "this_week": this_week}

    async def fetch_strava_data(self):
        """
        Fetches data for the latest activities from the Strava API
        """

        await self.fetch_ride_activities()
        self.calc_gear_service()

        # _LOGGER.debug("Fetching Data from Strava API")

        # activities_response = await self.oauth_websession.async_request(
        #    method="GET",
        #    url=f"https://www.strava.com/api/v3/athlete/activities?per_page={MAX_NB_ACTIVITIES}",
        # )

        # if activities_response.status == 200:
        # json_data = json.loads(await activities_response.text())
        # athlete_id = None
        # for activity in json_data:
        #    athlete_id = int(activity["athlete"]["id"])

        # Create a list of ride activities only
        # activities = []
        # for idx, activity in enumerate(json_data):
        #    if activity["type"] != "Ride":
        #        continue

        #    activities.append(activity)

        # gear_list = dict()

        # for a in activities:
        #    gear_id = a["gear_id"]

        # Check if this gear id has been found already, if not setup
        #    if not gear_id in gear_list.keys():
        #        gear_list[gear_id] = self._create_gear(gear_id)

        # activity date and time
        #    act_date = dt.strptime(a["start_date_local"], "%Y-%m-%dT%H:%M:%SZ")

        #    distance = round(a["distance"] / 1000, 1)
        #    moving_time = round(a["moving_time"] / 3600, 2)

        # For each sevice type, increment km if after start date
        #    for key in GEAR_SERVICE_KEYS:
        #        start_date = gear_list[gear_id][key]["start_date"]
        #        if act_date >= start_date:
        #            gear_list[gear_id][key]["distance"] += distance
        #            gear_list[gear_id][key]["time"] += moving_time
        # match description.device_class:
        #    case SensorDeviceClass.DURATION:
        #        gear_list[gear_id][description.key]["total"] += (
        #            moving_time
        #        )
        #    case SensorDeviceClass.DISTANCE:
        #        gear_list[gear_id][description.key]["total"] += (
        #            distance
        #        )

        await self.fetch_gear_information()

        weekly_stats = self._calc_weekly_strava_stats()

        # fetch summary stats
        summary_stats_url = (
            f"https://www.strava.com/api/v3/athletes/{self._strava_athlete_id}/stats"
        )

        summary_stats_response = await self.oauth_websession.async_request(
            method="GET",
            url=summary_stats_url,
        )

        sumary_stats = json.loads(await summary_stats_response.text())

        # Create a single dictionary of key:value pairs
        summary_stats = {}
        for k, v in sumary_stats.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    summary_stats[k + "_" + k2] = v2
            else:
                summary_stats[k] = v

        # Change units, from strava to our units
        # time = strava:seconds; we want:hours
        # distance = strava:meters; we want:km
        for k, v in summary_stats.items():
            if "distance" in k:
                summary_stats[k] = round(v / 1000, 1)
            if "time" in k:
                summary_stats[k] = round(v / 3600, 2)
            if "elevation" in k:
                summary_stats[k] = int(v)

        # Create a single dictionary of key:value pairs for gear
        gear_stats = {}
        gear_ids = {}
        for k, v in self._strava_ride_gear.items():
            ha_id = v.ha_id
            gear_ids[ha_id] = v.name
            gear_stats[ha_id + "_distance"] = {"distance": v.distance}
            for key in GEAR_SERVICE_KEYS:
                prefix = ha_id + "_" + key
                gear_stats[prefix] = {
                    "time": int(round(getattr(v, key).time, 0)),
                    "distance": int(round(getattr(v, key).distance, 0)),
                }
                gear_stats[prefix + "_date"] = getattr(v, key).service_date

        # elif activities_response.status == 429:
        #    _LOGGER.warn("Strava API rate limit has been reached")
        #    return

        # else:
        #    _LOGGER.error(
        #        f"Could not fetch strava activities (response code: {activities_response.status}): {await activities_response.text()}"
        #    )
        #    return

        _LOGGER.debug("Strava statistics updated from API")

        pprint.pprint(gear_ids)
        pprint.pprint(gear_stats)

        data = {
            # "activities": activities,
            "summary_stats": summary_stats,
            "weekly_stats": weekly_stats,
            "gear_ids": gear_ids,
            "gear_stats": gear_stats,
        }

        return data

    def _create_gear(self, id):
        gear = {
            "name": "Name Not Found; ID:" + id,
            "distance": 0,
        }

        for key in GEAR_SERVICE_KEYS:
            gear[key] = {
                "start_date": dt(2024, 8, 1, 13, 0, 0),
                "distance": 0,
                "time": 0,
            }

        return gear

    def _last_2years_mondays(self):
        d = date(date.today().year - 1, 1, 1)
        d += timedelta(7 - d.weekday())
        while d <= date.today():
            yield d
            d += timedelta(7)
