#!/usr/bin/env python
# -*- coding: utf8
"""
    When is Mercury next visible?

    Mercury is a bit hard to see because it never gets very far away
    from the Sun. But every now and then it's more easily seen than
    at other times. I'm trying to find those times.
"""
from __future__ import print_function
import ephem
import itertools
from sun import generate_rise_set
import defaults

observer = ephem.city(defaults.CITY)
mercury = ephem.Mercury()


def report(what, when):
    observer.date = when
    mercury.compute(observer)
    if mercury.alt > 0:
        print("{:7} {:%b %d} Alt {}  Elongation {}".format(
            what, ephem.localtime(observer.date).date(),
            mercury.alt, mercury.elong))

year = 2012
print("Mercury's position at sunrise or sunset for", year)
for sunrise, sunset in generate_rise_set(year, observer):
    report("Sunrise", sunrise)
    report("Sunset", sunset)
