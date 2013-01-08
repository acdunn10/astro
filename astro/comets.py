# -*- coding: utf8
"""
    Information about Comet C/2012 S1 (ISON)

    http://en.wikipedia.org/wiki/C/2012_S1
    http://scully.cfa.harvard.edu/cgi-bin/returnprepeph.cgi?d=c&o=CK12S010
"""
import os
import ephem
import requests
import time
import itertools
import collections
from . import CITY, miles_from_au, astro_path
from .data import AstroData
from .utils import format_angle as _
from .utils import HMS
from math import degrees

# A place to locally save Comet elements
SOURCE = astro_path('comets.txt')
URL = 'http://www.minorplanetcenter.net/iau/Ephemerides/Comets/Soft03Cmt.txt'

NAMES = (
    'C/2012 S1 (ISON)',
    'C/2011 L4 (PANSTARRS)',
    )

def save_comet_elements():
    r = requests.get(URL)
    if r.status_code == 200:
        with open(SOURCE, 'w') as f:
            f.write('# {}\n'.format(r.headers['Last-Modified']))
            f.write(r.text)

def get_comet_elements():
    with open(SOURCE) as f:
        s = f.readline().strip()
        t = time.strptime(s[7:], "%d %b %Y %H:%M:%S %Z")
        last_modified = time.mktime(t)
        comets = []
        for line in f:
            if line.startswith('#'):
                continue
            name = line.split(',', 1)[0]
            if name in NAMES:
                comets.append(ephem.readdb(line.strip()))
    return (last_modified, comets)

class CometData(AstroData):
    symbol = '☄'

    @property
    def display_distance(self):
        s = [self.symbol]
        distance_change = "⬆" if self.receding else "⬇"
        s.append(' {0.earth_distance:,.0f}{1} miles, {0.mph:,.0f}mph'.format(
            self, distance_change))
        return ' '.join(s)


def where_is(comet):
    now = ephem.now()
    comet.compute(now)
    obj = CometData(mag=comet.mag)
    print('{} Comet {}:  R.A. {}   Decl. {}'.format(5 * obj.symbol, comet.name,
        _(comet.ra, HMS), _(comet.dec)))
    print('{} T {}'.format(obj.symbol, comet._epoch_p))
    print('{} {}, Elong {}'.format(obj.symbol,
        ephem.constellation(comet)[1], _(comet.elong)))
    print('{1.symbol} Distance: Sun={0.sun_distance:.4f} AU Earth={0.earth_distance:.4f} AU'.format(
        comet, obj))
    obj.earth_distance = miles_from_au(comet.earth_distance)
    comet.compute(ephem.date(now + ephem.hour))
    moved = miles_from_au(comet.earth_distance) - obj.earth_distance
    obj.receding = moved > 0
    obj.mph = abs(moved)
    print(obj.display_distance)
    observer = ephem.city(CITY)
    observer.date = now
    comet.compute(observer)
    obj.az, obj.alt = comet.az, comet.alt
    obj.calculate_rise_and_set(comet, observer)
    if obj.alt > 0:
        print(obj.sky_position(magnitude=True))
    print(obj.rise_and_set())

def main():
    if not os.path.exists(SOURCE):
        print('Requesting comet data from minorplanetcenter.net ...')
        save_comet_elements()
    assert os.path.exists(SOURCE), "Expected to have comet elements"
    last_modified, comets = get_comet_elements()
    elements_age = (time.mktime(time.gmtime()) - last_modified) / 86400
    print('Comet database last modified: {:.1f} days ago'.format(elements_age))
    for comet in comets:
        where_is(comet)
    if elements_age >= 7.0:
        print("Requesting new comet data due to age")
        save_comet_elements()

if __name__ == '__main__':
    main()
