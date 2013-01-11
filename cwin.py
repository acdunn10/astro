""" Uses the curses module to display data in a window
"""
import sys
import curses
import ephem
import itertools
import collections
import operator
from copy import copy
from math import degrees
from astro import astro_path, miles_from_au
from astro.utils import format_angle as _

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)
STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux', 'Regulus')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')
MAX_ANGLE = ephem.degrees('20')
ARROWS = "⬆⬇"  # these fancy arrows aren't showing up on curses

SYMBOLS = {
    'Sun': '☼',
    'Moon': '☽',
    'Mercury': '☿',
    'Venus': '♀',
    'Mars': '♂',
    'Jupiter': '♃',
    'Saturn': '♄',
    'Uranus': '♅',
    'Neptune': '♆',
    '_comet': '☄',
    '_star': '★',
    }


class Separation(collections.namedtuple('Separation', 'body1 body2 angle')):
    def trend(self):
        "Returns True if the two bodies are getting closer"
        arrows = "UD" #
        a, b = map(copy, (self.body1, self.body2))
        later = ephem.now() + ephem.hour
        a.compute(later)
        b.compute(later)
        later_separation = ephem.separation(a, b)
        return later_separation < self.angle

class Distance:
    def __init__(self, date, body):
        self.body = body
        self.miles = miles_from_au(body.earth_distance)
        x = copy(body)
        x.compute(ephem.date(date + ephem.hour))
        moved = miles_from_au(x.earth_distance) - self.miles
        self.trend = moved < 0
        self.mph = abs(moved)

class Event(collections.namedtuple('Event', 'name row date msg attr')):
    @property
    def get_attr(self):
        "special case hack for the Sun"
        if self.name == 'Sun':
            return curses.color_pair(3)
        else:
            return self.attr

    @property
    def symbol(self):
        try:
            s = SYMBOLS[self.name]
        except KeyError:
            if self.name.startswith('C/'):
                s = SYMBOLS['_comet']
            else:
                s = SYMBOLS['_star']
        return s + ' '

def get_horizon_for_body(body):
    if body.name in ('Sun', 'Moon'):
        return ephem.degrees('-0:34')
    else:
        return ephem.degrees('0')

def calculate(w):
    date = ephem.now()
    w.addstr(30, 0, "Local: {:%H:%M:%S}".format(ephem.localtime(date)))
    w.refresh()

    sun = ephem.Sun(date)
    moon = ephem.Moon(date)
    planets = [planet(date) for planet in PLANETS]
    stars = [ephem.star(name) for name in STARS]
    comets = [comet for comet in get_comets()]
    [body.compute(date) for body in stars + comets]

    all_bodies = [sun, moon] + planets + stars + comets
    except_stars = [sun, moon] + planets + comets

    # Calculate angular separation between planetary bodies
    angles = []
    for a, b in itertools.combinations(all_bodies, 2):
        angle = ephem.separation(a, b)
        if angle < MAX_ANGLE:
            angles.append(Separation(a, b, angle))
    angles.sort(key=operator.attrgetter('angle'))
    for row, sep in enumerate(angles):
        color = 1 if sep.trend() else 2
        w.addstr(row + 13, 0,
            "{1} {0.body1.name} ⇔ {0.body2.name}".format(
                sep, _(sep.angle)),
            curses.color_pair(color))
        w.clrtoeol()

    # Calculate distance and velocity for objects of interest
    distances = [
        Distance(date, body)
        for body in [sun, moon] + planets + comets
    ]
    distances.sort(key=operator.attrgetter('mph'))
    for row, obj in enumerate(distances):
        color = 1 if obj.trend else 2
        w.addstr(row + 13, 44,
            "{0.mph:7,.0f} mph {0.miles:13,.0f} {0.body.name}".format(obj),
            curses.color_pair(color))

    observer = ephem.city('Columbus')
    observer.date = date
    w.addstr(31, 0, "Sidereal: {}".format(observer.sidereal_time()))

    events = []
    for row, body in enumerate(except_stars):
        observer.date = date
        observer.horizon = get_horizon_for_body(body)
        body.compute(observer)
        if body.alt > 0:
            mag = "Mag {0.mag:.1f}".format(body) if body.name not in ('Sun', 'Moon') else ""
            if body.name == 'Moon':  # special case for the moon
                mag = 'Phase {0.moon_phase:.2%}'.format(body)
            b = copy(body)
            if body.set_time > date:
                set = body.set_time
                observer.date = set
                b.compute(observer)
                az = b.az
            else:
                set = observer.next_setting(b, start=body.rise_time)
                az = b.az
            msg = '{} {} {} {} Set {:%I:%M %p %a} {:.0f}°'.format(
                    body.name, _(body.az), _(body.alt), mag,
                    ephem.localtime(set), degrees(az))
            events.append(Event(body.name, row, set, msg, 0))
        else:
            b = copy(body)
            if body.rise_time > date:
                rise = body.rise_time
                observer.date = rise
                b.compute(observer)
                az = b.az
            else:
                rise = observer.next_rising(b, start=body.set_time)
                az = b.az
            msg = '{0.name} Rise {1:%I:%M %p %a} {2:.0f}°'.format(body,
                ephem.localtime(rise), degrees(az))
            events.append(Event(body.name, row, rise, msg, curses.color_pair(2)))
    events.sort(key=operator.attrgetter('date'))
    for row, event in enumerate(events):
        w.addstr(row, 0, event.symbol + event.msg, event.get_attr)
        w.clrtoeol()

def get_comets():
    SOURCE = astro_path('comets.txt')
    comets = []
    with open(SOURCE) as f:
        f.readline().strip()  # Last-Modified
        for line in f:
            if line.startswith('#'):
                continue
            comet = ephem.readdb(line.strip())
            if comet.name in COMETS:
                comets.append(comet)
    return comets


def main(w):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    w.timeout(6000)

    while True:
        try:
            calculate(w)
            curses.curs_set(0)
            w.refresh()
            ch = w.getch()
            if ch != -1:
                break
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    curses.wrapper(main)
