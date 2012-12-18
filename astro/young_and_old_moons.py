# -*- coding: utf8
"""
    A "Young Moon" is a thin crescent Moon seen shortly after the New Moon.
    See my blog post <http://blog.mhsundstrom.com/?p=167> for some more
    information and there are some references from there with more information.
    The "Old Moon" is almost the same, except it's looking for a thin crescent
    Moon just before sunrise instead of just after sunset.

    This program is an exploration of the data behind all of that.
"""
import ephem
from . import CITY

sun = ephem.Sun()
moon = ephem.Moon()
observer = ephem.city(CITY)


def new_moons_in_year(year):
    "Returns a list of New Moons in the specified year"
    date = ephem.Date(str(year))
    new_moons = []
    while True:
        date = ephem.next_new_moon(date)
        if date.triple()[0] > year:
            break
        new_moons.append(date)
    return new_moons


def young_moons(new_moon_date):
    "Return Young Moon info for the specified New Moon date"
    info_list = []
    observer.date = new_moon_date
    # get data about the first 3 sunsets after this New Moon
    for i in range(3):
        observer.date = observer.next_setting(sun)
        sun.compute(observer)
        moon.compute(observer)
        d = {'Sunset': ephem.localtime(observer.date),
             'Sun azimuth': sun.az,
             'Moon azimuth': moon.az,
             'Moon altitude': moon.alt,
             'Sun-Moon elongation': moon.elong,
             'Moon phase': moon.moon_phase,
             'Age': 24 * (observer.date - new_moon_date),
             }
        observer.date = observer.next_setting(moon)
        d.update({'Moonset': ephem.localtime(observer.date)})
        info_list.append(d)
    return info_list


def old_moons(new_moon_date):
    "Return Old Moon info"
    info_list = []
    observer.date = new_moon_date
    for i in range(3):
        observer.date = observer.previous_rising(sun)
        sun.compute(observer)
        moon.compute(observer)
        d = {'Sunrise': ephem.localtime(observer.date),
             'Sun azimuth': sun.az,
             'Moon azimuth': moon.az,
             'Moon altitude': moon.alt,
             'Sun-Moon elongation': moon.elong,
             'Moon phase': moon.moon_phase,
             'Age': 24 * (new_moon_date - observer.date),
             'Moonrise': ephem.localtime(observer.previous_rising(moon))
             }
        info_list.append(d)
    return list(reversed(info_list))


def young_and_old_moons(new_moon_date):
    d = {'New Moon': new_moon_date,
         'Young Moons': young_moons(new_moon_date),
         'Old Moons': old_moons(new_moon_date)
         }
    return d


def young_and_old_by_year(year=None):
    if year is None:
        year = ephem.now().triple()[0]
    return {'Year': year,
            'Moons': [
                young_and_old_moons(new_moon_date)
                for new_moon_date in new_moons_in_year(year)
                ]
            }


if __name__ == '__main__':
    from pprint import pprint
    pprint(young_and_old_by_year())
