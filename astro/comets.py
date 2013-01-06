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

def sky_position(body, observer):
    symbol = '☄'
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

def where_is(name, elements, observer):
    print("Where is", name)
    comet = ephem.readdb(elements)
    comet.compute(observer)
    print('R.A.', comet.ra, 'Decl.', comet.dec)
    print('T {0._epoch_p}'.format(comet))
    sky_position(comet, observer)
    print('Magnitude: {0.mag:.1f} Elongation:{0.elong}'.format(comet))
    print('Constellation', ephem.constellation(comet)[1])
    print('Distance: Sun={0.sun_distance:.4f} AU Earth={0.earth_distance:.4f} AU'.format(comet))
    earth_distance = miles_from_au(comet.earth_distance)
    print('{:,.0f} miles from Earth'.format(earth_distance))
    """ The distance values are only changing daily. There must be
        some sort of step calculation here that I don't know about.
        This is different from the Moon.
    """

def main():
    observer = ephem.city(CITY)
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
            where_is(name, comets[name], observer)
    if elements_age >= 7.0:
        print("Requesting new comet data due to age")
        save_comet_elements()

if __name__ == '__main__':
    main()
