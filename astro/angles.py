# -*- coding: utf8
"""
    Calculate the angles among the interesting planets and Moon.
"""
import ephem
import itertools
import collections

MAX_ANGLE = ephem.degrees('45')

class Separation(collections.namedtuple('Separation', 'p1 p2 angle')):
    def __str__(self):
        return "{0.angle}° {0.p1.symbol} {0.p1.body.name} ⇔ {0.p2.symbol} {0.p2.body.name}".format(self)

class Body(collections.namedtuple('Body', 'symbol body')):
    def separation_from(self, other):
        return Separation(self, other,
            ephem.separation(self.body, other.body))


def main():
    bodies = (
        Body('☽', ephem.Moon()),
        Body('☿', ephem.Mercury()),
        Body('♀', ephem.Venus()),
        Body('♂', ephem.Mars()),
        Body('♃', ephem.Jupiter()),
        Body('♄', ephem.Saturn())
    )

    for body in bodies:
        body.body.compute()

    angles = [
        a.separation_from(b)
        for a, b in itertools.combinations(bodies, 2)
        ]
    angles.sort(key=lambda x:x.angle)
    later = ephem.now() + ephem.hour
    for i in angles:
        if i.angle > MAX_ANGLE:
            break
        i.p1.body.compute(later)
        i.p2.body.compute(later)
        newsep = ephem.separation(i.p1.body, i.p2.body)
        s = '⬇ closer' if i.angle > newsep else '⬆ further'
        print("{} {}".format(i, s))

if __name__ == '__main__':
    main()

