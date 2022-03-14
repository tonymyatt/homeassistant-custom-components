import pandas as pd
import requests
import json
import time
from datetime import date, timedelta, datetime
import pprint

from secrets import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_CODE


# REQUEST http://www.strava.com/oauth/authorize?client_id=CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all
# RESPONSE http://localhost/exchange_token?state=&code=CODE&scope=read,activity:read_all,profile:read_all

def token_read():
    # Make Strava auth API call with your 
    # client_code, client_secret and code
    response = requests.post(
                        url = 'https://www.strava.com/oauth/token',
                        data = {
                                'client_id': STRAVA_CLIENT_ID,
                                'client_secret': STRAVA_CLIENT_SECRET,
                                'code': STRAVA_CODE,
                                'grant_type': 'authorization_code'
                                }
                    )
    #Save json response as a variable
    strava_tokens = response.json()
    # Save tokens to file
    with open('strava_tokens.json', 'w') as outfile:
        json.dump(strava_tokens, outfile)
    # Open JSON file and print the file contents 
    # to check it's worked properly
    with open('strava_tokens.json') as check:
        data = json.load(check)
    print(data)

class StravaTest():

    _weekly_data = None

    def read_strava(self):

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
        activities = dict()
        
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

            activities[r[x]['id']] = {
                "name": r[x]['name'],
                'start_date_local': r[x]['start_date_local'],
                'distance': r[x]['distance'],
                'moving_time': r[x]['moving_time'],
                'elapsed_time': r[x]['elapsed_time'],
                'total_elevation_gain': r[x]['total_elevation_gain']
            }
            
        print(f"Writing {len(activities)} activites to file")
        with open('strava_activities.json', 'w') as convert_file:
            convert_file.write(json.dumps(activities))

        self._weekly_data = dict()

        for d in self._all_mondays():
            self._weekly_data[d] = {'distance': 0, 'time': 0, "elevation": 0}
            for a in activities:
                b = activities[a]
                ad = datetime.strptime(b['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                ad = date(ad.year, ad.month, ad.day)
                if ad >= d and ad < d+ timedelta(7):
                    self._weekly_data[d]['distance'] += b['distance']/1000
                    self._weekly_data[d]['time'] += b['moving_time']/3600
                    self._weekly_data[d]['elevation'] += int(b['total_elevation_gain'])

    def _all_mondays(self):
        d = date(date.today().year-1, 1, 1)
        d += timedelta(7 - d.weekday())
        while d <= date.today():
            yield d
            d += timedelta(7)

    def read_strava_activities(self):

        if self._weekly_data is None:
            return None

        weekly_data = self._weekly_data
        monday_this_week = date.today() + timedelta(0 - date.today().weekday())
        monday_last_week = monday_this_week + timedelta(-7)
        monday_fortnight = monday_last_week + timedelta(-7)

        print(f"Cycling Last Week Distance: {weekly_data[monday_last_week]['distance']:0.1f}km")
        print(f"Cycling Last Week Distance delta: {weekly_data[monday_last_week]['distance']/weekly_data[monday_fortnight]['distance']*100:0.0f}%")
        print(f"Cycling Last Week Time: {weekly_data[monday_last_week]['time']:0.1f}hrs")
        print(f"Cycling Last Week Time delta: {weekly_data[monday_last_week]['time']/weekly_data[monday_fortnight]['time']*100:0.0f}%")
        print(f"Cycling Last Week Elevation: {weekly_data[monday_last_week]['elevation']:0.0f}m")
        print(f"Cycling Last Week Climbing: {weekly_data[monday_last_week]['elevation']/weekly_data[monday_last_week]['distance']/10:0.1f}%")
        print(f"Cycling This Week Distance: {weekly_data[monday_this_week]['distance']:0.1f}km")
        print(f"Cycling This Week Distance delta: {weekly_data[monday_this_week]['distance']/weekly_data[monday_last_week]['distance']*100:0.0f}%")
        print(f"Cycling This Week Time: {weekly_data[monday_this_week]['time']:0.1f}hrs")
        print(f"Cycling This Week Time delta: {weekly_data[monday_this_week]['time']/weekly_data[monday_last_week]['time']*100:0.0f}%")
        print(f"Cycling This Week Elevation: {weekly_data[monday_this_week]['elevation']:0.0f}m")
        print(f"Cycling This Week Climbing: {weekly_data[monday_this_week]['elevation']/weekly_data[monday_this_week]['distance']/10 if weekly_data[monday_this_week]['distance'] == 0 else 0:0.1f}%")
        
strava = StravaTest()
strava.read_strava()
strava.read_strava_activities()