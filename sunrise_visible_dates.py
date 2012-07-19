#!/usr/bin/env python
# -*- coding: utf8
"""
    When does sunrise become visible from my north-facing building?

    My building faces north and my view to the east is blocked by
    another tall building a block or two away. The leftmost edge
    of that building is at a compass direction of 78°, so I do not
    see any sunrises until the Sun rises to the left of that
    building.

    On which day in the spring does the Sun finally rise left of
    the building? And what is the last day that a sunrise will
    be visible?
"""
from __future__ import print_function
import ephem
import itertools
import defaults


def generate_sunrise_info():
    "Generate daily info about sunrise for an entire year"
    observer = ephem.city(defaults.CITY)
    sun = ephem.Sun()
    YEAR = 2012  # doesn't really matter what year we choose
    observer.date = ephem.date(str(YEAR))
    while True:
        observer.date = observer.next_rising(sun)
        if observer.date.triple()[0] != YEAR:
            break
        sun.compute(observer)
        yield (observer, sun)

BUILDING_AZIMUTH = ephem.degrees('78')


def sunrise_not_visible((observer, sun)):
    "could be a lambda but this is more obvious"
    return sun.az > BUILDING_AZIMUTH


def sunrise_visible((observer, sun)):
    return sun.az <= BUILDING_AZIMUTH

iter = generate_sunrise_info()

for observer, sun in itertools.dropwhile(sunrise_not_visible, iter):
    print("First visible sunrise:", ephem.localtime(observer.date).date())
    break
for observer, sun in itertools.dropwhile(sunrise_visible, iter):
    print("Sunrise no longer visible", ephem.localtime(observer.date).date())
    break
