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
import defaults

observer = ephem.city(defaults.CITY)


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

source = (u'\u263c', ephem.Sun(observer)), (u'\u263d', ephem.Moon(observer))
for symbol, body in source:
    for line in calculate(symbol, body):
        s = line.encode('utf8')
        print(s)
