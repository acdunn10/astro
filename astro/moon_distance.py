# -*- coding: utf8
import ephem
from . import MILES_PER_AU
from .utils import pairwise


def compute_moon(interval=ephem.hour):
    moon = ephem.Moon()
    date = ephem.now()
    while True:
        moon.compute(date)
        yield moon.earth_distance * MILES_PER_AU
        date += interval

iter = pairwise(compute_moon(ephem.minute))
for i in range(10):
    a, b = next(iter)
    print("{:.1f} {:5.1f}".format(b, b - a))
