#!/usr/bin/env python
# -*- coding: utf8
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import ephem
from itertools import tee, izip

MOON = '\u263d'
METERS_PER_MILE = 1609.344
MILES_PER_AU = ephem.meters_per_au / METERS_PER_MILE


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def compute_moon(interval=ephem.hour):
    moon = ephem.Moon()
    date = ephem.now()
    while True:
        moon.compute(date)
        yield moon.earth_distance * MILES_PER_AU
        date += interval

iter = pairwise(compute_moon(ephem.minute))
for i in range(10):
    a, b = iter.next()
    print("{:.1f} {:5.1f}".format(b, b - a))
