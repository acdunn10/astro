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

# Where are you?
#   I've chosen a convenient Confluence point in my home town
observer = ephem.Observer()
observer.lat = '40.0'
observer.lon = '-83.0'
observer.elevation = 250  # meters above sea level


def main():
    def show(body, time, rs):
        print("{:%I:%M %p %a} {}{}  Azi {:3.0f}".format(
            ephem.localtime(time), body.name, rs, degrees(float(body.az))))

    for body in (ephem.Sun(observer), ephem.Moon(observer)):
        if body.alt > 0:
            current = ' Azi {:3.0f} Alt {:3.0f}'.format(
                degrees(float(body.az)), degrees(float(body.alt)))
            rising = observer.previous_rising(body)
            show(body, rising, 'rise')
            print(current)
            setting = observer.next_setting(body)
            show(body, setting, 'set')
        else:
            current = ''
            rising = observer.next_rising(body)
            show(body, rising, 'rise')
            setting = observer.next_setting(body)
            show(body, setting, 'set')
        print()

if __name__ == '__main__':
    main()
