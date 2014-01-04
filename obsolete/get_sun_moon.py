# -*- coding: utf8
"""
    Calculate the angles among the interesting planets, Moon and stars.
"""
import ephem
import itertools
import operator
import collections
from astro import PLANETS
from astro.utils import format_angle as _
from ephem.stars import stars

MAX_ANGLE = ephem.degrees('20')

class Separation(collections.namedtuple('Separation', 'p1 p2 angle')):
    def __str__(self):
        return "{1} {0.p1.name} ({0.p1.mag:.1f}) ⇔ {0.p2.name} ({0.p2.mag:.1f})".format(self, _(self.angle))

def close_star_approaches(year=None):
    if year is None:
        year = ephem.now().triple()[0]
    starting_date = ephem.Date(str(year))
    stars_list = [ephem.star(name) for name in stars.keys()]
    # Stars don't move, so just compute them once
    [star.compute(starting_date) for star in stars_list]

    planets = [planet() for planet in PLANETS]
    for day in range(365):
        date = ephem.Date(starting_date + day)
        [body.compute(date) for body in planets]
        for body in planets:
            for star in stars_list:
                sep = ephem.separation(body, star)
                if sep < ephem.degrees('3'):
                    print(date, body.name, star.name, sep)

def current_separations():
    stars_list = [ephem.star(name) for name in stars.keys()]
    planets = [planet() for planet in PLANETS]
    solar_system = [ephem.Moon()] + planets
    [body.compute() for body in solar_system + stars_list]
    print(type(stars_list[0]))
    angles = []
    # Separations between solar system bodies and stars
    for body in solar_system:
        for star in stars_list:
            angles.append(
                Separation(body, star, ephem.separation(body, star)))
    # more separations
    for a, b in itertools.combinations(solar_system, 2):
        angles.append(Separation(a, b, ephem.separation(a, b)))

    for sep in sorted(angles, key=operator.attrgetter('angle')):
        if sep.angle > MAX_ANGLE:
            break
        print(sep)

if __name__ == '__main__':
    current_separations()
    #close_star_approaches()

