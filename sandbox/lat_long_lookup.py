import requests

response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA')

resp_json_payload = response.json()
print(resp_json_payload)
print(resp_json_payload['results'][0]['geometry']['location'])