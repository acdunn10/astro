# -*- coding: utf8
import ephem
import collections
import operator
import logging
import itertools
from astro import CITY, PLANETS
from astro.utils import pairwise
from astro.utils import format_angle as _

logger = logging.getLogger(__name__)

def position_interval(year, interval, *bodies):
    bodies = list(bodies)
    date = ephem.Date(str(year))
    end_date = ephem.Date(str(year+1))
    while date < end_date:
        [body.compute(date) for body in bodies]
        yield (date, bodies)
        date = ephem.Date(date + interval)

TwoBodySeparation = collections.namedtuple('TwoBodySeparation',
    'date body1 body2 separation')

TwoBodyDelta = collections.namedtuple('TwoBodyDelta',
    'date body1 body2 separation delta')

def two_body(body1, body2):
    iter = position_interval(2013, ephem.hour, body1, body2)
    for (date, (body1, body2)) in iter:
        yield TwoBodySeparation(date, body1, body2,
                                ephem.separation(body1, body2))

def separation(body1, body2):
    for a, b in pairwise(two_body(body1, body2)):
        yield TwoBodyDelta(b.date, body1, body2, b.separation,
                           b.separation - a.separation)

def close_approaches(body1, body2):
    print("Close approaches between {0.name} and {1.name}".format(body1, body2))
    observer =  ephem.city(CITY)
    for a, b in pairwise(separation(body1, body2)):
        logger.debug("{0.date} {0.separation} {0.delta:.7f} {1.delta:.7f}".format(a, b))
        if a.delta < 0 and b.delta > 0:
            if a.separation > ephem.degrees('20'):
                continue
            observer.date = a.date
            body1.compute(observer)
            print("{:%Y-%m-%d %H:%M} {:>12} Alt={:>12} Az={:>12}".format(
                ephem.localtime(a.date),
                _(a.separation), _(body1.alt), _(body1.az)))
    print(40 * '=')

def all_planets():
    for a, b in itertools.combinations(PLANETS, 2):
        close_approaches(a(), b())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, handler=logging.StreamHandler())
    #close_approaches(ephem.Moon(), ephem.Jupiter())
    #close_approaches(ephem.Venus(), ephem.Jupiter())
    all_planets()

