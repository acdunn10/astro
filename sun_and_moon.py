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

    GeekTool gets a UnicodeEncodeError unless I use line.encode('utf8')
"""
from __future__ import print_function
from __future__ import unicode_literals
import ephem
from math import degrees
import itertools
import defaults

SUN_SYMBOL = '\u263c'
MOON_SYMBOL = '\u263d'
METERS_PER_MILE = 1609.344

observer = ephem.city(defaults.CITY)
sun = ephem.Sun(observer)
moon = ephem.Moon(observer)

SOURCE = ((SUN_SYMBOL, sun), (MOON_SYMBOL, moon))


def sky_position():
    current = []
    for symbol, body in SOURCE:
        if body.alt > 0:
            az, alt = [degrees(float(i)) for i in (body.az, body.alt)]
            current.append('{} Azi {:3.0f}\xb0 Alt {:.0f}\xb0'.format(
                symbol, az, alt))
    yield '   '.join(current)


def calculate(symbol, body):
    """
        Calculate the appropriate rising and setting time. We'll
        calculate tomorrow's time if the body is not currently
        above the horizon.
    """
    if body.alt > 0:
        az, alt = [degrees(float(i)) for i in (body.az, body.alt)]
        rising_method = observer.previous_rising
    else:
        rising_method = observer.next_rising
    fmt = '{} {:%I:%M %p %a} Azi {:.0f}\xb0'
    rising = ephem.localtime(rising_method(body))
    r = fmt.format('Rise', rising, degrees(float(body.az)))
    setting = ephem.localtime(observer.next_setting(body))
    s = fmt.format('Set', setting, degrees(float(body.az)))
    yield '{}{}   {}{}'.format(symbol, r, symbol, s)


def sun_and_moon():
    "Rise, set and current position of the Sun and Moon"
    for symbol, body in SOURCE:
        for line in calculate(symbol, body):
            yield line


def moon_info():
    "A bit more useful information about the Moon"
    now = ephem.now()
    previous_new = ephem.previous_new_moon(now)
    moon_age = 24 * (now - previous_new)
    if moon_age <= 72:
        yield "{} Young Moon: {:.1f} hours".format(MOON_SYMBOL, moon_age)
    else:
        next_new = ephem.next_new_moon(now)
        moon_age = 24 * (next_new - now)
        if moon_age <= 72:
            yield "{} Old Moon {:.1f} hours".format(MOON_SYMBOL, moon_age)
    moon.compute(now)
    moon_distance_miles = ephem.meters_per_au *\
        moon.earth_distance / METERS_PER_MILE
    yield "{}Phase {:.2f}%, {:,.1f} miles".format(
        MOON_SYMBOL, moon.phase, moon_distance_miles)


if __name__ == '__main__':
    for line in itertools.chain(sky_position(), sun_and_moon(), moon_info()):
        print(line.encode('utf8'))
