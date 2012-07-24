#!/usr/bin/env python
# -*- coding: utf8
"""
    Calculate rise, set and location for the Sun and Moon today.

    If the Sun (or Moon) has not yet risen, it prints the next rise and
    set times. If the body has already risen, it returns the rise time and
    also the next set time.

    I use GeekTool to display the output of this on the desktop background:
        http://projects.tynsoe.org/en/geektool/
    A similar tool for Windows is called Rainmeter:
        http://rainmeter.net/

    Using Python 2.7

    The utf-8 encoding trick below seemed to be the easiest way to
    get the output to show up in GeekTool without generating a
    UnicodeEncodeError
"""
from __future__ import print_function
import ephem
from math import degrees
import itertools
import defaults

SUN_SYMBOL = u'\u263c'
MOON_SYMBOL = u'\u263d'

observer = ephem.city(defaults.CITY)
sun = ephem.Sun(observer)
moon = ephem.Moon(observer)

def calculate(symbol, body):
    """
        Calculate the appropriate rising and setting time. We'll
        calculate tomorrow's time if the body is not currently
        above the horizon.
    """
    if body.alt > 0:
        az, alt = [degrees(float(i)) for i in (body.az, body.alt)]
        current = u'Azi {:3.0f}\xb0 Alt {:.0f}\xb0'.format(az, alt)
        rising_method = observer.previous_rising
    else:
        current = None
        rising_method = observer.next_rising
    fmt = u'{} {:%I:%M %p %a} Azi {:.0f}\xb0'
    rising = ephem.localtime(rising_method(body))
    r = fmt.format(u'Rise', rising, degrees(float(body.az)))
    setting = ephem.localtime(observer.next_setting(body))
    s = fmt.format(u'Set', setting, degrees(float(body.az)))
    yield u'{}{} {}\u2605{}'.format(symbol, body.name, r, s)
    if current:
        yield u'{} {}'.format(symbol, current)


def sun_and_moon():
    "Rise, set and current position of the Sun and Moon"
    source = (
        (SUN_SYMBOL, sun),
        (MOON_SYMBOL, moon)
        )
    for symbol, body in source:
        for line in calculate(symbol, body):
            yield line

def moon_info():
    "A bit more useful information about the Moon"
    now = ephem.now()
    previous_new = ephem.previous_new_moon(now)
    moon_age = 24 * (now - previous_new)
    if moon_age <= 72:
        yield u"{} Young Moon: {:.1f} hours".format(MOON_SYMBOL, moon_age)
    else:
        next_new = ephem.next_new_moon(now)
        moon_age = 24 * (next_new - now)
        if moon_age <= 72:
            yield u"{} Old Moon {:.1f} hours".format(MOON_SYMBOL, moon_age)
    moon.compute(now)
    moon_distance_miles = ephem.meters_per_au * moon.earth_distance / 1609.344
    yield u"{}Phase {:.2f}%, {:,.1f} miles".format(
        MOON_SYMBOL, moon.phase, moon_distance_miles)
    events = [
        ("First Quarter", ephem.next_first_quarter_moon(now)),
        ("Full Moon", ephem.next_full_moon(now)),
        ("Last Quarter", ephem.next_last_quarter_moon(now)),
        ("New Moon", ephem.next_new_moon(now))
        ]
    events.sort(key=lambda x:x[1])
    yield u"{}{} {}".format(MOON_SYMBOL, *events[0])


if __name__ == '__main__':
    for line in itertools.chain(sun_and_moon(), moon_info()):
        s = line.encode('utf8')
        print(s)
