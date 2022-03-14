import requests, json

from secrets import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET

token_url = "https://www.strava.com/oauth/token"

test_api_url = "<<URL of the API you want to call goes here>>"

#step A, B - single call with client credentials as the basic auth header - will return access_token
data = {'grant_type': 'client_credentials'}

access_token_response = requests.post(token_url, data=data, verify=False, allow_redirects=False, auth=(STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET))

print(access_token_response.headers)
print(access_token_response.text)

tokens = json.loads(access_token_response.text)

print("access token: " + tokens['access_token'])

#step B - with the returned access_token we can make as many calls as we want

api_call_headers = {'Authorization': 'Bearer ' + tokens['access_token']}
api_call_response = requests.get(test_api_url, headers=api_call_headers, verify=False)

print(api_call_response.text)