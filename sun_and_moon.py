#!/usr/bin/env python
# -*- coding: utf8
"""
    Calculate rise, set and location for the Sun and Moon today.

    If the Sun (or Moon) has not yet risen, it prints the next rise and
    set times. If the body has already risen, it returns the rise time and
    also the next set time.

    I use GeekTool to display the output of this on the desktop background:
        http://projects.tynsoe.org/en/geektool/
    I'm sure this is a similar tool available on Windows or Linux.

    Requires the PyEphem package, available at:
        http://rhodesmill.org/pyephem/

    Using Python 2.7
"""
from __future__ import print_function
import ephem
from math import degrees
import defaults

observer = ephem.city(defaults.CITY)


def calculate(symbol, body):
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
    print(u'{}{} {}\u2605{}'.format(symbol, body.name, r, s))
    if current:
        print(u'{} {}'.format(symbol, current))


calculate(u'\u263c', ephem.Sun(observer))
calculate(u'\u263d', ephem.Moon(observer))
