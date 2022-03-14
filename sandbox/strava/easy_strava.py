from os.path import exists
import requests
import json
import time
from datetime import date, timedelta, datetime

from secrets import STRAVE_TOKEN

# REQUEST http://www.strava.com/oauth/authorize?client_id=CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all
# RESPONSE http://localhost/exchange_token?state=&code=CODE&scope=read,activity:read_all,profile:read_all

class CycleWeekStats():
    distance = 0
    distance_delta = 0
    time = 0
    time_delta = 0
    elevation = 0

    @property
    def climbing(self) -> float:
        climb = 0
        if self.distance > 0:
            climb = self.elevation/self.distance/10
        return climb

class StravaTest():

    _weekly_data = None

    def token_create(self):
        
        # Start with a valid token
        strava_tokens = STRAVE_TOKEN

        # Save tokens to file
        with open('strava_tokens.json', 'w') as outfile:
            json.dump(strava_tokens, outfile)

        # Open JSON file and print the file contents 
        # to check it's worked properly
        with open('strava_tokens.json') as check:
            data = json.load(check)
        print(data)

    def read_strava(self):

        file_exists = exists('strava_tokens.json')
        if not file_exists:
            self.token_create()

        ## Get the tokens from file to connect to Strava
        with open('strava_tokens.json') as json_file:
            strava_tokens = json.load(json_file)

        ## If access_token has expired then use the refresh_token to get the new access_token
        if strava_tokens['expires_at'] < time.time():

            #Make Strava auth API call with current refresh token
            response = requests.post(
                                url = 'https://www.strava.com/oauth/token',
                                data = {
                                        'client_id': 11696,
                                        'client_secret': 'c367949748704d55237aadd58d1e01a714579fb0',
                                        'grant_type': 'refresh_token',
                                        'refresh_token': strava_tokens['refresh_token']
                                        }
                            )
            #Save response as json in new variable
            new_strava_tokens = response.json()

            # Save new tokens to file
            with open('strava_tokens.json', 'w') as outfile:
                json.dump(new_strava_tokens, outfile)
            
            #Use new Strava tokens from now
            strava_tokens = new_strava_tokens

        #Loop through all activities
        url = "https://www.strava.com/api/v3/activities"
        access_token = strava_tokens['access_token']
        
        ## Create the dataframe ready for the API call to store your activity data
        activities = []
        
        # get page of activities from Strava
        r = requests.get(url + '?access_token=' + access_token + '&per_page=200&page=1')
        r = r.json()
        # if no results then exit loop
        if (not r):
            exit()
            
        # otherwise add new data to dataframe
        for x in range(len(r)):

            # Skip non-rides
            if r[x]['type'] != 'Ride':
                continue

            activities.append({
                "id": r[x]['id'],
                "name": r[x]['name'],
                'start_date_local': r[x]['start_date_local'],
                'distance': r[x]['distance'],
                'moving_time': r[x]['moving_time'],
                'elapsed_time': r[x]['elapsed_time'],
                'total_elevation_gain': r[x]['total_elevation_gain']
            })
            
        print(f"Writing {len(activities)} activites to file")
        with open('strava_activities.json', 'w') as convert_file:
            convert_file.write(json.dumps(activities))

        self._weekly_data = dict()

        for mon_date in self._last_2years_mondays():
            self._weekly_data[mon_date] = {'distance': 0, 'time': 0, "elevation": 0}
            for a in activities:
                act_date = datetime.strptime(a['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                act_date = date(act_date.year, act_date.month, act_date.day)
                if act_date >= mon_date and act_date < mon_date+ timedelta(7):
                    self._weekly_data[mon_date]['distance'] += a['distance']/1000
                    self._weekly_data[mon_date]['time'] += a['moving_time']/3600
                    self._weekly_data[mon_date]['elevation'] += int(a['total_elevation_gain'])

    def calc_weekly_strava_stats(self):

        # Weekly data not available
        if self._weekly_data is None:
            return None

        data = self._weekly_data
        mon_this_week = date.today() + timedelta(0 - date.today().weekday())
        mon_last_week = mon_this_week + timedelta(-7)
        mon_last_fnight = mon_last_week + timedelta(-7)

        last_week = CycleWeekStats()
        last_week.distance = data[mon_last_week]['distance']
        last_week.distance_delta = last_week.distance/data[mon_last_fnight]['distance']*100
        last_week.time = data[mon_last_week]['time']
        last_week.time_delta = last_week.time/data[mon_last_fnight]['time']*100
        last_week.elevation = data[mon_last_week]['elevation']

        this_week = CycleWeekStats()
        this_week.distance = data[mon_this_week]['distance']
        this_week.distance_delta = this_week.distance/data[mon_last_week]['distance']*100
        this_week.time = data[mon_this_week]['time']
        this_week.time_delta = this_week.time/data[mon_last_week]['time']*100
        this_week.elevation = data[mon_this_week]['elevation']

        print(f"Cycling Last Week Distance: {last_week.distance:0.1f}km")
        print(f"Cycling Last Week Distance delta: {last_week.distance_delta:0.0f}%")
        print(f"Cycling Last Week Time: {last_week.time:0.1f}hrs")
        print(f"Cycling Last Week Time delta: {last_week.time_delta:0.0f}%")
        print(f"Cycling Last Week Elevation: {last_week.elevation:0.0f}m")
        print(f"Cycling Last Week Climbing: {last_week.climbing:0.1f}%")

        print(f"Cycling This Week Distance: {this_week.distance:0.1f}km")
        print(f"Cycling This Week Distance delta: {this_week.distance_delta:0.0f}%")
        print(f"Cycling This Week Time: {this_week.time:0.1f}hrs")
        print(f"Cycling This Week Time delta: {this_week.time_delta:0.0f}%")
        print(f"Cycling This Week Elevation: {this_week.elevation:0.0f}m")
        print(f"Cycling This Week Climbing: {this_week.climbing:0.1f}%")

        return {
            "last_week": last_week,
            "this_week": this_week
        }

    def _last_2years_mondays(self):
        d = date(date.today().year-1, 1, 1)
        d += timedelta(7 - d.weekday())
        while d <= date.today():
            yield d
            d += timedelta(7)
        
strava = StravaTest()
strava.read_strava()
strava.calc_weekly_strava_stats()