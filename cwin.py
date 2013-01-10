""" Uses the curses module to display data in a window
"""
import sys
import curses
import ephem
import itertools
import collections
import operator
from copy import copy
from astro import astro_path, miles_from_au
from astro.utils import format_angle as _

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)
INNER_PLANETS = ('Mercury', 'Venus', 'Mars')
STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux', 'Regulus')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')
MAX_ANGLE = ephem.degrees('20')
ARROWS = "⬆⬇"  # these fancy arrows aren't showing up on curses

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

def calculate(w):
    date = ephem.now()

    sun = ephem.Sun(date)
    moon = ephem.Moon(date)
    planets = [planet(date) for planet in PLANETS]
    stars = [ephem.star(name) for name in STARS]
    comets = [comet for comet in get_comets()]
    [body.compute(date) for body in stars + comets]

    all_bodies = [sun, moon] + planets + stars + comets
    except_stars = [sun, moon] + planets + comets
    inner_planets = [i for i in planets if i.name in INNER_PLANETS]

    # Calculate angular separation between planetary bodies
    angles = []
    for a, b in itertools.combinations(all_bodies, 2):
        angle = ephem.separation(a, b)
        if angle < MAX_ANGLE:
            angles.append(Separation(a, b, angle))
    angles.sort(key=operator.attrgetter('angle'))
    for row, sep in enumerate(angles):
        color = 1 if sep.trend() else 2
        w.addstr(row + 15, 0,
            "{1} {0.body1.name} ⇔ {0.body2.name}".format(
                sep, _(sep.angle)),
            curses.color_pair(color))
        w.clrtoeol()

    # Calculate distance and velocity for objects of interest
    distances = [
        Distance(date, body)
        for body in [sun, moon] + inner_planets + comets
    ]
    distances.sort(key=operator.attrgetter('mph'))
    for row, obj in enumerate(distances):
        color = 1 if obj.trend else 2
        w.addstr(row + 15, 45,
            "{0.mph:7,.0f} mph {0.miles:11,.0f} {0.body.name}".format(obj),
            curses.color_pair(color))

    observer = ephem.city('Columbus')
    observer.date = date
    for row, body in enumerate(except_stars):
        body.compute(observer)
        if body.alt > 0:
            mag = "Mag {0.mag}".format(body) if body.name not in ('Sun', 'Moon') else ""
            if body.set_time > date:
                set = body.set_time
            else:
                set = observer.next_setting(copy(body), start=body.rise_time)
            w.addstr(row, 0,
                '{} {} {} {} Set {:%I:%M %p %a}'.format(
                    body.name, _(body.az), _(body.alt), mag,
                    ephem.localtime(set)))
        else:
            if body.rise_time > date:
                rise = body.rise_time
            else:
                rise = observer.next_rising(copy(body), start=body.set_time)
            w.addstr(row, 0,
                '{0.name} Rise {1:%I:%M %p %a}'.format(body,
                    ephem.localtime(rise)),
                curses.color_pair(2))
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


def main(stdscr, args):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)

    while True:
        try:
            calculate(stdscr)
            curses.curs_set(0)
            stdscr.refresh()
            if len(args) > 0:
                curses.napms(6000)
            else:
                if stdscr.getch() == ord('q'):
                    break
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    curses.wrapper(main, sys.argv[1:])
