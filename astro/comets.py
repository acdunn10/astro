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
from . import CITY, miles_from_au, astro_path, AstroData
from math import degrees

# A place to locally save Comet elements
SOURCE = astro_path('comets.txt')
URL = 'http://www.minorplanetcenter.net/iau/Ephemerides/Comets/Soft03Cmt.txt'

NAMES = (
    'C/2012 S1 (ISON)',
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
        comets = {}
        for line in f:
            if line.startswith('#'):
                continue
            name = line.split(',', 1)[0]
            comets[name] = line.strip()
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



def sky_position(body, observer):
    if body.alt > 0:
        az, alt = [degrees(float(i)) for i in (body.az, body.alt)]
        up_or_down = '⬆' if az <= 180 else '⬇'
        print('{} {:3.0f}°⇔  {:.0f}°{}'.format(
            symbol, az, alt, up_or_down))
        rising_method = observer.previous_rising
        srise = 'Rose'
    else:
        rising_method = observer.next_rising
        srise = 'Rise'
    fmt = '{} {:%I:%M %p %a} {:.0f}°⇔'
    rising = ephem.localtime(rising_method(body))
    r = fmt.format(srise, rising, degrees(float(body.az)))
    setting = ephem.localtime(observer.next_setting(body))
    s = fmt.format('Set', setting, degrees(float(body.az)))
    print('{} {}   {} {}'.format(symbol, r, symbol, s))

def where_is(name, elements):
    now = ephem.now()
    comet = ephem.readdb(elements)
    comet.compute(now)
    print('Comet {}:  R.A. {}   Decl. {}   T {}'.format(name,
        comet.ra, comet.dec, comet._epoch_p))
    print('{1}, Mag {0.mag:.1f} Elong {0.elong}°'.format(comet,
        ephem.constellation(comet)[1]))
    print('Distance: Sun={0.sun_distance:.4f} AU Earth={0.earth_distance:.4f} AU'.format(comet))
    obj = CometData()
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
    print(obj.sky_position)
    print(obj.rise_and_set)

def main():
    if not os.path.exists(SOURCE):
        print('Requesting comet data from minorplanetcenter.net ...')
        save_comet_elements()
    assert os.path.exists(SOURCE), "Expected to have comet elements"
    last_modified, comets = get_comet_elements()
    elements_age = (time.mktime(time.gmtime()) - last_modified) / 86400
    print('{} comets. Last modified: {:.1f} days ago'.format(
        len(comets), elements_age))
    for name in comets:
        if name in NAMES:
            where_is(name, comets[name])
    if elements_age >= 7.0:
        print("Requesting new comet data due to age")
        save_comet_elements()

if __name__ == '__main__':
    main()
