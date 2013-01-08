# -*- coding: utf8
"""
    Current information about the position of the Moon
"""
import ephem
import itertools
from . import CITY, miles_from_au
from .data import MoonData
import logging

logger = logging.getLogger(__name__)

def young_and_old_moons(obj):
    "A bit more useful information about the Moon"
    now = ephem.now()
    previous_new = ephem.previous_new_moon(now)
    obj.age = 24 * (now - previous_new)
    obj.young = obj.old = None
    if obj.age <= 72:
        obj.young = True
    else:
        next_new = ephem.next_new_moon(now)
        obj.age = 24 * (next_new - now)
        if obj.age <= 72:
            obj.young = False


def earth_moon_distance(obj):
    now = ephem.now()
    moon = ephem.Moon(now)
    obj.earth_distance = miles_from_au(moon.earth_distance)
    obj.phase = moon.phase
    moon.compute(ephem.date(now + ephem.minute))
    obj.waxing = moon.phase > obj.phase
    moved = miles_from_au(moon.earth_distance) - obj.earth_distance
    obj.receding = moved > 0
    obj.mph = abs(moved * 60)

def get_moon_data():
    date = ephem.now()
    observer = ephem.city(CITY)
    observer.date = date
    moon = ephem.Moon(observer)

    obj = MoonData(az=moon.az, alt=moon.alt)
    earth_moon_distance(obj)
    young_and_old_moons(obj)
    obj.calculate_rise_and_set(moon, observer)
    return obj

def main():
    obj = get_moon_data()
    if obj.alt > 0:
        print(obj.sky_position(magnitude=False))
    print(obj.phase_and_distance())
    print(obj.rise_and_set())
    if obj.age <= 72:
        print(obj.young_and_old())


"""
def today():
    moon = ephem.Moon()
    observer = ephem.city(CITY)
    start = ephem.date('2013/1/6 07:05:00')
    finish = ephem.date('2013/1/6 17:49:00')
    date = start
    while date <= finish:
        observer.date = date
        moon.compute(date)
        dist = miles_from_au(moon.earth_distance)
        moon.compute(observer)
        odist = miles_from_au(moon.earth_distance)
        print('{} {:,.0f} {:,.0f} {} {}'.format(
            date, dist, odist, moon.az, moon.alt))
        date = ephem.date(date + 1 * ephem.minute)
"""


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, handler=logging.StreamHandler())
    main()






