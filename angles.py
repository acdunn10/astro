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

if __name__ == '__main__':
    stars_list = [ephem.star(name) for name in stars.keys()]
    solar_system = [ephem.Moon()] + [planet() for planet in PLANETS]

    [body.compute() for body in solar_system + stars_list]
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
