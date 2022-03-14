from __future__ import print_function
import time
from secrets import STRAVA_CLIENT_SECRET
import strava_api_v3
from strava_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: strava_oauth
configuration = strava_api_v3.Configuration()
configuration.access_token = STRAVA_CLIENT_SECRET

# create an instance of the API class
api_instance = strava_api_v3.ActivitiesApi(strava_api_v3.ApiClient(configuration))
before = 56 # int | An epoch timestamp to use for filtering activities that have taken place before a certain time. (optional)
after = 56 # int | An epoch timestamp to use for filtering activities that have taken place after a certain time. (optional)
page = 56 # int | Page number. (optional)
per_page = 30 # int | Number of items per page. Defaults to 30. (optional) (default to 30)

try:
    # List Athlete Activities
    api_response = api_instance.get_logged_in_athlete_activities(before=before, after=after, page=page, per_page=per_page)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ActivitiesApi->get_logged_in_athlete_activities: %s\n" % e)