# -*- coding: utf8
""" Print some current interesting information about the Moon"""
from collections import namedtuple
import operator
import ephem
from ephem.stars import stars
from .utils import miles_from_au
from .utils import format_angle as _

class MoonPhaseEvent(namedtuple('MoonPhaseEvent', 'method_name date')):
    def __str__(self):
        return "{:30s} {}".format(
            self.method_name.replace('_', ' ').capitalize(),
            self.date)

def moon_phase_events():
    date = ephem.now()
    next_prev = ('next', 'previous')
    phase = ('new', 'first_quarter', 'full', 'last_quarter')
    events = []
    for np in next_prev:
        for p in phase:
            method_name = '{}_{}_moon'.format(np, p)
            method = getattr(ephem, method_name)
            events.append(MoonPhaseEvent(method_name, method(date)))
    for event in sorted(events, key=operator.attrgetter('date')):
        yield event

def compute_star(name):
    star = ephem.star(name)
    star.compute()
    return star

def nearest_stars():
    print('\nThe stars within 20° of the Moon:')
    now = ephem.now()
    moon = ephem.Moon(now)
    separations = {
        name:ephem.separation(moon, compute_star(name))
        for name in stars
    }
    closest = (
        (value, name)
        for (name, value) in separations.items()
        if value <= ephem.degrees('20')
    )
    for (value, name) in sorted(closest):
        print(name, value)


def main(observer):
    date = ephem.now()
    moon = ephem.Moon(date)
    # Young or old Moon (within 72 hours of new)
    previous_new = ephem.previous_new_moon(date)
    age = 24 * (date - previous_new)
    if age <= 72:
        print("Young Moon: {:.1f} hours".format(age))
    else:
        next_new = ephem.next_new_moon(date)
        age = 24 * (next_new - date)
        if age <= 72:
            print("Old Moon: {:.1f} hours".format(age))

    print("Phase {0.moon_phase:.2%}".format(moon))
    distance = miles_from_au(moon.earth_distance)
    moon.compute(ephem.Date(date + ephem.hour))
    moved = miles_from_au(moon.earth_distance) - distance
    print(
        'Earth distance:    {:13,.0f} miles, {:+5.0f} mph'.format(
            distance, moved))
    observer.date = date
    moon.compute(observer)
    m2 = moon.copy()
    distance = miles_from_au(moon.earth_distance)
    observer.date = ephem.Date(date + ephem.hour)
    moon.compute(observer)
    moved = miles_from_au(moon.earth_distance) - distance
    print(
        'Observer distance: {:13,.0f} miles, {:+5.0f} mph'.format(
            distance, moved))
    print("Azimuth {}".format(_(m2.az)))
    print("Altitude {}".format(_(m2.alt)))
    print("Declination {}".format(_(m2.dec)))
    print("\n")
    for event in moon_phase_events():
        print(str(event))
    #nearest_stars()

if __name__ == '__main__':
    main(ephem.city('Columbus'))
