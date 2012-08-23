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
from __future__ import division
import ephem
from math import degrees
import itertools
import defaults


METERS_PER_MILE = 1609.344
MILES_PER_AU = ephem.meters_per_au / METERS_PER_MILE

observer = ephem.city(defaults.CITY)
sun = ephem.Sun(observer)
moon = ephem.Moon(observer)

SOURCE = (('☼', sun), ('☽', moon))


def sky_position():
    current = []
    for symbol, body in SOURCE:
        if body.alt > 0:
            az, alt = [degrees(float(i)) for i in (body.az, body.alt)]
            up_or_down = '⬆' if az <= 180 else '⬇'
            current.append('{} {:3.0f}°⇔  {:.0f}°{}'.format(
                symbol, az, alt, up_or_down))
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
        srise = 'Rose'
    else:
        rising_method = observer.next_rising
        srise = 'Rise'
    fmt = '{} {:%I:%M %p %a} {:.0f}°⇔'
    rising = ephem.localtime(rising_method(body))
    r = fmt.format(srise, rising, degrees(float(body.az)))
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
        yield "☽ Young Moon: {:.1f} hours".format(moon_age)
    else:
        next_new = ephem.next_new_moon(now)
        moon_age = 24 * (next_new - now)
        if moon_age <= 72:
            yield "☽ Old Moon {:.1f} hours".format(moon_age)
    # where is the moon now
    moon.compute(now)
    distance = moon.earth_distance * MILES_PER_AU
    phase = moon.phase
    # where is the Moon one minute later
    now += ephem.minute
    moon.compute(now)
    ps = "⬆" if moon.phase > phase else "⬇"
    moved = (moon.earth_distance * MILES_PER_AU) - distance
    ds = "⬆" if moved > 0 else "⬇"
    mph = abs(60 * moved)
    yield "☽Phase {:.2f}%{}, {:,.1f} miles, {}{:.1f}mph".format(
        phase, ps, distance, ds, mph)


if __name__ == '__main__':
    for line in itertools.chain(sky_position(), sun_and_moon(), moon_info()):
        print(line.encode('utf8'))
