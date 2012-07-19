#!/usr/bin/env python
# -*- coding: utf8
"""
"""
from __future__ import print_function
import ephem


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

if __name__ == '__main__':
    for sunrise, sunset in generate_rise_set(2012, ephem.city('Columbus')):
        print(sunrise, sunset)
