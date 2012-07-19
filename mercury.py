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

for sunrise, sunset in generate_rise_set(2012, observer):
    # where is Mercury at sunset?
    observer.date = sunset
    mercury.compute(observer)
    if mercury.alt > 0:
        print(ephem.localtime(observer.date).date(),
            mercury.alt, mercury.elong)
