# -*- coding: utf8
"""
    Earth Satellite info

    http://spaceflight.nasa.gov/realdata/sightings/cities/view.cgi?
        country=United_States&region=Ohio&city=Columbus
    http://celestrak.com/NORAD/elements/
    http://www.satflare.com/

"""
import os
import ephem
import requests
import datetime
import time
import itertools
import collections
from .files import astro_config

__all__ = ['EarthSatellites', 'save_space_stations']

# where we locally save Space Station elements
SOURCE = astro_config('satellites.txt')

PASSES = 10
URL = 'http://celestrak.com/NORAD/elements/visual.txt'
MAXIMUM_AGE_DAYS = 5


class EarthSatellites(dict):
    "A dictionary but with last_modified info added"
    def __init__(self):
        super().__init__()
        with open(SOURCE) as f:
            s = f.readline().strip()
            t = time.strptime(s[7:], "%d %b %Y %H:%M:%S %Z")
            self.last_modified = ephem.Date(
                datetime.datetime.fromtimestamp(time.mktime(t)))
            lines = [line.strip() for line in f]
            args = [iter(lines)] * 3
            for name, line1, line2 in zip(*args):
                self[name] = ephem.readtle(name, line1, line2)


def save_space_stations():
    "Save the space station data for later use"
    r = requests.get(URL)
    if r.status_code == 200:
        with open(SOURCE, 'w') as f:
            f.write('# {}\r\n'.format(r.headers['Last-Modified']))
            f.write(r.text)

def main():
    from . import CITY
    if not os.path.exists(SOURCE):
        print('Requesting station data...')
        save_stations()
    assert os.path.exists(SOURCE), "Expected to have station data"
    last_modified = os.path.getmtime(SOURCE)
    last_request, stations = get_stations()
    file_age = (time.time() - last_modified) / 3600
    request_age = 4 + ((time.time() - last_request) / 3600) # temporary hack
    print("Request age: {:.1f} hours, file age: {:.1f} hours".format(
        request_age, file_age))
    my_station = stations["ISS (ZARYA)"]
    observer = ephem.city(CITY)
    satellite_observations(ephem.readtle(*my_station), observer)

if __name__ == '__main__':
    #save_space_stations()
    stations = EarthSatellites()
    print(len(stations), 'satellites, last modified on', stations.last_modified)
    if ephem.now() - stations.last_modified> MAXIMUM_AGE_DAYS:
        print("Space station data is old, requesting newer data")
        save_space_stations()
    else:
        observer = ephem.city('Columbus')
        for station in stations.values():
            station.compute(observer)
            print(station.name, station.az, station.alt)

