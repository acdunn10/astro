# -*- coding: utf8
""" Close approaches between two planets (and the Moon) in a given year.
    Results are logged to stderr and written as JSON to stdout, so the
    following can be convenient:

    python close_approaches.py > output/close-approaches.json
"""
import sys
import ephem
import collections
import operator
import logging
import itertools
from astro.utils import pairwise

logger = logging.getLogger(__name__)

BODIES = (ephem.Moon, ephem.Venus, ephem.Jupiter,
          ephem.Mars, ephem.Saturn, ephem.Mercury)

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

class TwoBodyDelta(collections.namedtuple('TwoBodyDelta',
            'date body1 body2 separation delta')):
    def info(self):
        "Returns a dictionary of useful info that is easily serialized to JSON"
        return {
            'date': self.date.tuple(),
            'DJD': self.date,
            'body1': self.body1.name,
            'body2': self.body2.name,
            'separation': self.separation,
            }

def two_body(year, body1, body2):
    iter = position_interval(year, ephem.hour, body1, body2)
    for (date, (body1, body2)) in iter:
        yield TwoBodySeparation(date, body1, body2,
                                ephem.separation(body1, body2))

def separation(year, body1, body2):
    for a, b in pairwise(two_body(year, body1, body2)):
        yield TwoBodyDelta(b.date, body1, body2, b.separation,
                           b.separation - a.separation)

def close_approaches(year, body1, body2):
    logger.info("{2}: {0.name} and {1.name}".format(body1, body2, year))
    for a, b in pairwise(separation(year, body1, body2)):
        if a.delta < 0 and b.delta > 0:
            if a.separation > ephem.degrees('20'):
                continue
            logger.info("   {} {} ".format(a.date, a.separation))
            yield a.info()

def all_planets(years):
    approaches = []
    for year in years:
        logger.info("Close approaches for the year {}".format(year))
        for a, b in itertools.combinations(BODIES, 2):
            for approach in close_approaches(year, a(), b()):
                approaches.append(approach)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
        format="%(message)s", handler=logging.StreamHandler())
    # Use a list of years or the current year. Keep it simple...
    years = [int(i) for i in sys.argv[1:] if i.isdigit()]
    if not years:
        years = [ephem.now().tuple()[0]]
    all_planets(years)

