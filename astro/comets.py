# -*- coding: utf8
"""
    Get and save information about the interesting list of comets
    from the Minor Planet Center

    python -m astro.comets will request and save newer comet data
    whenever the data gets too old.

    Information about Comet C/2012 S1 (ISON):
        http://en.wikipedia.org/wiki/C/2012_S1
        http://scully.cfa.harvard.edu/cgi-bin/returnprepeph.cgi?d=c&o=CK12S010
"""
import ephem
import requests
import time
import datetime
from .files import astro_config

__all__ = ['Comets', 'save_comets']

# A place to locally save Comet elements
SOURCE = astro_config('comets.txt')
URL = 'http://www.minorplanetcenter.net/iau/Ephemerides/Comets/Soft03Cmt.txt'
MAXIMUM_AGE_DAYS = 5

class Comets(dict):
    "A regular dictionary but with the last_modified info added"
    def __init__(self):
        super().__init__()
        with open(SOURCE) as f:
            s = f.readline().strip()
            t = time.strptime(s[7:], "%d %b %Y %H:%M:%S %Z")
            self.last_modified = ephem.Date(
                datetime.datetime.fromtimestamp(time.mktime(t)))
            for line in f:
                if line.startswith('#'):
                    continue
                name = line.split(',', 1)[0]
                self[name] = ephem.readdb(line.strip())

def save_comets():
    "Request the comets and save locally for later use"
    r = requests.get(URL)
    if r.status_code == 200:
        with open(SOURCE, 'w') as f:
            f.write('# {}\n'.format(r.headers['Last-Modified']))
            f.write(r.text)


if __name__ == '__main__':
    INTERESTING_COMETS = (
        'C/2012 S1 (ISON)',
        'C/2011 L4 (PANSTARRS)',
        )
    comets = Comets()
    print(len(comets), 'comets, last modified on', comets.last_modified)
    if ephem.now() - comets.last_modified > MAXIMUM_AGE_DAYS:
        print("Comet data is old, requesting newer data")
        save_comets()
    else:
        observer = ephem.city('Columbus')
        for name in INTERESTING_COMETS:
            comet = comets[name]
            comet.compute(observer)
            print('--- Comet', comet.name)
            print('Magnitude {0.mag:.1f}'.format(comet))
            print('Distance from earth: {0.earth_distance:.5f} AU'.format(comet))
            print('Azimuth: {0.az}   Altitude: {0.alt}'.format(comet))

