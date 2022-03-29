from cgi import print_exception
from codecs import namereplace_errors
from ctypes import addressof
from unicodedata import name
from xmlrpc.client import boolean
import requests
import json
import pprint

QUERY_URL = "https://trafficbuddy.com.au/?lat={lat}&lon={long}&distance={dist}"

class AusFuelPrice:
    name: str
    address: str
    latitude: float
    longitude: float
    brand: str
    price: float
    fuel_type: str

    def __str__(self):
        return f"{self.name} {self.address} {self.brand} {self.fuel_type} @ {self.price}c/L"

class AusFuelAPI:
    def __init__(self, search_distance, latitude, longitude):
        self._search_meters = search_distance * 1000
        self._latitude = latitude
        self._longitude = longitude

    def refresh_data(self) -> boolean:
        query = QUERY_URL.format(
            lat=self._latitude, long=self._longitude, dist=self._search_meters
        )
        print(query)
        raw_html = requests.get(query).text
        json_data = json.loads(raw_html)
        #pprint.pprint(json_data)
        self._fuel_prices = json_data["data"]
        return json_data["message"] == "ok"

    def get_data(self) -> dict:
        prices = {}
        for entry in self._fuel_prices:
            # Look for a station entry
            if not "station" in entry:
                continue

            station = entry["station"]
            name = station["name"]
            address = station["address"]
            latitude = station["location"]["latitude"]
            longitude = station["location"]["longitude"]
            brand = station["brand"]
            for price_entry in station["prices"]:
                price = AusFuelPrice
                price.name = name
                price.address = address
                price.latitude = latitude
                price.longitude = longitude
                price.brand = brand
                price.price = price_entry["price"]
                price.fuel_type = price_entry["type"]

                n = price.name.replace(" ", "_")
                f = price.fuel_type.replace(" ", "_")
                price_id = f"{n}_{f}"
                prices[price_id] = price

        data = {"prices": prices}

        return data

api = AusFuelAPI(5, -27.635100, 152.916180)
print(api.refresh_data())
data = api.get_data()
print(len(data))
pprint.pprint(data["prices"])