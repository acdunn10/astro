# -*- coding: utf8
""" Earth Satellite info

    http://spaceflight.nasa.gov/realdata/sightings/cities/view.cgi?
        country=United_States&region=Ohio&city=Columbus
    http://celestrak.com/NORAD/elements/
    http://www.satflare.com/
"""
import ephem
import requests
import logging
import datetime
from . import astro_config

__all__ = ['EarthSatellites']

logger = logging.getLogger(__name__)

# where we locally save Space Station elements
SOURCE = astro_config('satellites.txt')
URL = 'http://celestrak.com/NORAD/elements/visual.txt'
MAXIMUM_AGE_DAYS = 1

class EarthSatellites(dict):
    "A dictionary but with last_modified info added"
    def __init__(self):
        super().__init__()
        self.load()
        logger.debug("EarthSatellite data last_modified: {0.last_modified}".format(self))
        if ephem.now() - self.last_modified > MAXIMUM_AGE_DAYS:
            if self.retrieve():
                self.load()
        logger.debug("{} Earth Satellites loaded".format(len(self)))

    def load(self):
        self.clear()
        with open(SOURCE) as f:
            s = f.readline().strip()
            self.last_modified = ephem.Date(
                datetime.datetime.strptime(
                    s[7:], "%d %b %Y %H:%M:%S %Z"))
            lines = [line.strip() for line in f]
            args = [iter(lines)] * 3
            for name, line1, line2 in zip(*args):
                self[name] = ephem.readtle(name, line1, line2)

    def retrieve(self):
        logger.info("Retrieving new EarthSatellite data")
        r = requests.get(URL)
        if r.status_code == 200:
            with open(SOURCE, 'w') as f:
                f.write('# {}\r\n'.format(r.headers['Last-Modified']))
                f.write(r.text)
        return r.status_code == 200


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    satellites = EarthSatellites()
