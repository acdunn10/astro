# -*- coding: utf8
"""
    Get and save the info about space stations

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

__all__ = ['SpaceStations', 'save_space_stations']

# where we locally save Space Station elements
SOURCE = astro_config('space-stations.txt')

PASSES = 10
URL = 'http://celestrak.com/NORAD/elements/stations.txt'
MAXIMUM_AGE_DAYS = 5

SatPass = collections.namedtuple('SatPass',
    'rise_time rise_az transit_time transit_alt set_time set_az')

def satellite_observations(satellite, observer, passes=PASSES):
    satellite.compute(observer)
    print("Current position: Lat={0.sublat} Lon={0.sublong}".format(satellite))
    print("Elevation: {0.elevation}".format(satellite))
    print("Range: {0.range}".format(satellite))
    print("Range velocity: {0.range_velocity}".format(satellite))
    print("Eclipsed? {0.eclipsed}".format(satellite))
    sun = ephem.Sun(observer)
    for i in range(PASSES):
        info = SatPass(*observer.next_pass(satellite))
        observer.date = info.transit_time
        sun.compute(observer)
        satellite.compute(observer)
        if not satellite.eclipsed:
            transit_time = ephem.localtime(info.transit_time).replace(microsecond=0)
            print("Transit ", transit_time, "at", info.transit_alt)
        observer.date = info.set_time + ephem.minute

class SpaceStations(dict):
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

# def get_stations():
#     with open(SOURCE) as f:
#         s = f.readline().strip()
#         last_request = time.mktime(time.strptime(s[7:], "%d %b %Y %H:%M:%S GMT"))
#         # TODO - should convert to GMT
#         stations = {}
#         lines = [line.strip() for line in f]
#         args = [iter(lines)] * 3
#         stations = {
#             name: [name, line1, line2]
#             for name, line1, line2 in zip(*args)
#             }
#     return (last_request, stations)

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
    stations = SpaceStations()
    print(len(stations), 'stations, last modified on', stations.last_modified)
    if ephem.now() - stations.last_modified> MAXIMUM_AGE_DAYS:
        print("Space station data is old, requesting newer data")
        save_space_stations()
    else:
        observer = ephem.city('Columbus')
        for station in stations.values():
            station.compute(observer)
            print(station.name, station.az, station.alt)

