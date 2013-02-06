# -*- coding: utf8
""" Get and save up-to-date information about interesting comets.
    We save the data locally and retrieve it again once it gets
    too old. The data comes from the Minor Planet Center.

    Information about Comet C/2012 S1 (ISON):
        http://en.wikipedia.org/wiki/C/2012_S1
        http://scully.cfa.harvard.edu/cgi-bin/returnprepeph.cgi?d=c&o=CK12S010
"""
import ephem
import requests
import logging
import datetime
from .files import astro_config

__all__ = ['Comets']

logger = logging.getLogger(__name__)

# A place to locally save Comet elements
SOURCE = astro_config('comets.txt')
URL = 'http://www.minorplanetcenter.net/iau/Ephemerides/Comets/Soft03Cmt.txt'
MAXIMUM_AGE_DAYS = 5

class Comets(dict):
    "A regular dictionary but with the last_modified info added"
    def __init__(self):
        super().__init__()
        self.load()
        logger.debug("Comet data last_modified: {0.last_modified}".format(self))
        if ephem.now() - self.last_modified > MAXIMUM_AGE_DAYS:
            if self.retrieve():
                self.load()
        logger.debug("{} comets loaded".format(len(self)))

    def load(self):
        self.clear()
        with open(SOURCE) as f:
            s = f.readline().strip()
            self.last_modified = ephem.Date(
                datetime.datetime.strptime(
                    s[7:], "%d %b %Y %H:%M:%S %Z"))
            for line in f:
                if line.startswith('#'):
                    continue
                name = line.split(',', 1)[0]
                self[name] = ephem.readdb(line.strip())

    def retrieve(self):
        "Request the comets and save locally for later use"
        logger.info("Retrieving new comet data")
        r = requests.get(URL)
        if r.status_code == 200:
            with open(SOURCE, 'w') as f:
                f.write('# {}\n'.format(r.headers['Last-Modified']))
                f.write(r.text)
        return r.status_code == 200


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    comets = Comets()

