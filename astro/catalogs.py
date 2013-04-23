"""
    Information about Comet C/2012 S1 (ISON):
        http://en.wikipedia.org/wiki/C/2012_S1
        http://scully.cfa.harvard.edu/cgi-bin/returnprepeph.cgi?d=c&o=CK12S010

    Minor Planets also, with the current news about
        Asteroid 2012 DA14

    Earth Satellite info:

    http://spaceflight.nasa.gov/realdata/sightings/cities/view.cgi?
        country=United_States&region=Ohio&city=Columbus
    http://celestrak.com/NORAD/elements/
    http://celestrak.com/NORAD/documentation/tle-fmt.asp
    http://www.satflare.com/

"""
# -*- coding: utf8
import os
import ephem
import requests
import logging
import datetime

logger = logging.getLogger(__name__)

MAXIMUM_AGE_DAYS = 3

class Catalog(dict):
    """ A Catalog is a dictionary of bodies, usually comets, asteroids,
        earth satellites. It also has a last_modified attribute so we
        know how old the data is.
    """
    LINE_END = '\n'

    def __init__(self):
        super().__init__()
        self.load()

    def path(self):
        return os.path.join(os.path.expanduser('~/.astro'), self.SOURCE)

    def __str__(self):
        return (
            "[{1:,}] "
            "{0.__class__.__name__} {0.last_modified}".format(
                self, len(self)))

    def load(self):
        self.clear()
        try:
            with open(self.path()) as f:
                self.last_modified = ephem.Date(
                    datetime.datetime.strptime(
                        f.readline().strip()[7:],
                        "%d %b %Y %H:%M:%S %Z"))
                self.line_loader(f)
        except FileNotFoundError:
            self.last_modified = 0

    def retrieve(self):
        "Request the records and save locally for later use"
        try:
            r = requests.get(self.URL)
            if r.status_code == 200:
                with open(self.path(), 'w') as f:
                    f.write('# {}{}'.format(
                        r.headers['Last-Modified'], self.LINE_END))
                    f.write(r.text)
            return r.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(str(e))
        return False

class DatabaseLoader:
    def line_loader(self, f):
        for line in f:
            if line.startswith('#'):
                continue
            name = line.split(',', 1)[0]
            self[name] = ephem.readdb(line.strip())

class ElementLoader:
    def line_loader(self, f):
        lines = [line.strip() for line in f]
        args = [iter(lines)] * 3
        for name, line1, line2 in zip(*args):
            self[name] = ephem.readtle(name, line1, line2)


class Comets(Catalog, DatabaseLoader):
    SOURCE = 'comets.txt'
    URL = 'http://www.minorplanetcenter.net/iau/Ephemerides/Comets/Soft03Cmt.txt'

class Asteroids(Catalog, DatabaseLoader):
    SOURCE = 'asteroids.txt'
    URL = 'http://www.minorplanetcenter.net/iau/Ephemerides/Unusual/Soft03Unusual.txt'

class Satellites(Catalog, ElementLoader):
    LINE_END = '\r\n'
    SOURCE = 'satellites.txt'
    URL = 'http://celestrak.com/NORAD/elements/visual.txt'


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    now = ephem.now()
    for klass in (Comets, Asteroids, Satellites):
        catalog = klass()
        print(catalog)
        if now - catalog.last_modified >= MAXIMUM_AGE_DAYS:
            print("Retrieving most recent data...")
            catalog.retrieve()



