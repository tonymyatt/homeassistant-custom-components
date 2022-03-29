import requests
import json
import pprint
from bs4 import BeautifulSoup

URL = 'https://petrolbuddy.net.au/?fuelType=3&distance=5&sortType=cheapest&searchBy=1&lat=-27.634499&lon=152.9199269'

#raw_html = requests.get(URL).text
#data = BeautifulSoup(raw_html, 'html.parser')
#print(data.select('css-1w7lunh'))


#URL2 = 'https://trafficbuddy.com.au/?lat=-27.634499&lon=152.9199269&distance=5000'
URL2 = 'https://trafficbuddy.com.au/?lat=-27.635100&lon=152.916180&distance=5000'

raw_html = requests.get(URL2).text
fuel_prices = json.loads(raw_html)
pprint.pprint(fuel_prices)