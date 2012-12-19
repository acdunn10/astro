# -*- coding: utf8
"""
    http://spaceflight.nasa.gov/realdata/sightings/cities/view.cgi?
        country=United_States&region=Ohio&city=Columbus
    http://celestrak.com/NORAD/elements/

"""
import os
import ephem
import requests
import time
import itertools
import collections


PASSES = 10
SOURCE = os.path.expanduser('~/.astro-space-station.txt')
URL = 'http://celestrak.com/NORAD/elements/stations.txt'

SatPass = collections.namedtuple('SatPass',
    'rise_time rise_az transit_time transit_alt set_time set_az')

def satellite_observations(satellite, observer, passes=PASSES):
    """ However, one thing this does not tell me is if the
        satellite is illuminated by the Sun. If it's not, then
        it won't be visible.
    """
    satellite.compute(observer)
    print("Current position: Az={0.az} Alt={0.alt}".format(satellite))
    sun = ephem.Sun(observer)
    for i in range(PASSES):
        info = SatPass(*observer.next_pass(satellite))
        observer.date = info.transit_time
        sun.compute(observer)
        print(ephem.localtime(info.transit_time).replace(microsecond=0),
            info.transit_alt, sun.alt)
        observer.date = info.set_time + ephem.minute

def save_stations():
    r = requests.get(URL)
    if r.status_code == 200:
        with open(SOURCE, 'w') as f:
            f.write('# {}\r\n'.format(r.headers['Last-Modified']))
            f.write(r.text)

def get_stations():
    with open(SOURCE) as f:
        s = f.readline().strip()
        last_request = time.mktime(time.strptime(s[7:], "%d %b %Y %H:%M:%S GMT"))
        # TODO - should convert to GMT
        stations = {}
        lines = [line.strip() for line in f]
        args = [iter(lines)] * 3
        stations = {
            name: [name, line1, line2]
            for name, line1, line2 in zip(*args)
            }
    return (last_request, stations)

if __name__ == '__main__':
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

