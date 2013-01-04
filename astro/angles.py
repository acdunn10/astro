# -*- coding: utf8
"""
    Calculate the angles among the interesting planets and Moon.
"""
import ephem
import itertools
import collections

MAX_ANGLE = ephem.degrees('20')

AngleBetween = collections.namedtuple('AngleBetween', 'p1 p2 angle')

if __name__ == '__main__':
    BODIES = (
        ('☽', ephem.Moon()),
        ('☿', ephem.Mercury()),
        ('♀', ephem.Venus()),
        ('♂', ephem.Mars()),
        ('♃', ephem.Jupiter()),
        ('♄', ephem.Saturn())
    )

    now = ephem.now()
    for symbol, body in BODIES:
        body.compute()

    bodies = (body for symbol, body in BODIES)
    angles = []
    for a, b in itertools.combinations(bodies, 2):
        separation = ephem.separation(a, b)
        if separation < MAX_ANGLE:
            angles.append(AngleBetween(a, b, separation))
    angles.sort(key=lambda x:x.angle)
    later = now + ephem.hour
    for i in angles:
        i.p1.compute(later)
        i.p2.compute(later)
        newsep = ephem.separation(i.p1, i.p2)
        closer = i.angle > newsep
        print(i.angle, i.p1.name, i.p2.name, 'closer' if closer else 'further')


