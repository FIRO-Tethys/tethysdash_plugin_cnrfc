import requests


def get_nwps_location_metadata(location):
    response = requests.get(f"https://api.water.noaa.gov/nwps/v1/gauges/{location}")
    return response.json()
