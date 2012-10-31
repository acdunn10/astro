#!/usr/bin/env python
# -*- coding: utf8
"""
"""
from __future__ import print_function
import ephem
import defaults


def generate_rise_set(year, observer):
    "Generate sunrise and sunset times for a given year"
    sun = ephem.Sun()
    observer.date = ephem.date(str(year))
    while True:
        observer.date = observer.next_rising(sun)
        if observer.date.triple()[0] > year:
            break
        sunrise = observer.date
        observer.date = observer.next_setting(sun)
        yield (sunrise, observer.date)


def generate_twilight(year, observer, value='-6'):
    "Generate twilight times (Civil twilight by default)"
    sun = ephem.Sun()
    observer.date = ephem.date(str(year))
    observer.horizon = value
    while True:
        observer.date = observer.next_rising(sun, use_center=True)
        if observer.date.triple()[0] > year:
            break
        morning = observer.date
        observer.date = observer.next_setting(sun, use_center=True)
        evening = observer.date
        yield (morning, evening)





if __name__ == '__main__':
    for sunrise, sunset in generate_rise_set(2012, ephem.city(defaults.CITY)):
        print(sunrise, sunset)
