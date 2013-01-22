# -*- coding: utf8
""" Report on sunrise, sunset and azimuth values for the current year
"""
import ephem
from .utils import generate_rise_set
from . import CITY
import datetime

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
    year = ephem.now().triple()[0]
    start_date = ephem.date(str(year))
    end_date = ephem.date('{}/12/31'.format(year))
    for info in generate_rise_set(ephem.Sun(), ephem.city(CITY),
                                  start_date, end_date):
        r, s = map(ephem.localtime, (info.rise_time, info.set_time))
        daylight = datetime.timedelta(seconds=int(86400 * (info.set - info.rise)))
        print('{0:%Y-%m-%d} {0:%H:%M:%S} {2.rise_az} {1:%H:%M:%S} {2.set_az} {3}'.format(
                r, s, info, daylight))
