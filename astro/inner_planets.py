# -*- coding: utf8
"""
    Inner planets
"""
import ephem
import collections
from . import CITY
from .utils import pairwise

observer = ephem.city(CITY)
sun = ephem.Sun(observer)
mercury = ephem.Mercury(observer)
venus = ephem.Venus(observer)

Elong = collections.namedtuple('Elong', 'date angle diff')

def hourly(year, planet):
    "Hourly position report for a planet"
    date = ephem.Date(str(year))
    while date.triple()[0] == year:
        planet.compute(date)
        yield Elong(date, planet.elong, ephem.degrees(0))
        date = ephem.Date(date + ephem.hour)

def elongation():
    for a, b in pairwise(hourly(2009, ephem.Venus())):
        yield Elong(b.date, b.angle, b.angle - a.angle)

def positive(x):
    return x >= 0

# for a,b in pairwise(elongation()):
#     if positive(a.diff) != positive(b.diff):
#         print(b.date, b.angle)

for i in elongation():
    print("{0.date} {0.angle} {0.diff:12.8f}".format(i))
