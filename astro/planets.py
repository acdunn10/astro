# -*- coding: utf8
"""
    Calculate rise, set and location for the major planets.

    If the Sun (or Moon) has not yet risen, it prints the next rise and
    set times. If the body has already risen, it returns the rise time and
    also the next set time.
"""
import ephem
from math import degrees
from . import CITY


def format_position(symbol, body):
    az, alt = [degrees(float(i)) for i in (body.az, body.alt)]
    up_or_down = '⬆' if az <= 180 else '⬇'
    return '{:10} {} {:.0f}°⇔ {:.0f}°{}'.format(body.name, symbol, az, alt, up_or_down)


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
    print('{:10} {} {}   {} {}'.format(body.name, symbol, r, symbol, s))


if __name__ == '__main__':
    observer = ephem.city(CITY)

    PLANETS = (
        ('☿', ephem.Mercury(observer)),
        ('♀', ephem.Venus(observer)),
        ('♂', ephem.Mars(observer)),
        ('♃', ephem.Jupiter(observer)),
        ('♄', ephem.Saturn(observer))
    )

    for symbol, body in PLANETS:
        if body.alt > 0:
            print(format_position(symbol, body))

    for symbol, body in PLANETS:
        calculate(symbol, body)
