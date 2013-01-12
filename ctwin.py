import operator
import curses
import itertools
import collections
import ephem
from astro import Comets
from astro.utils import pairwise
from astro.utils import format_angle as _
from astro import miles_from_au

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)
STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux', 'Regulus')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')
MAX_ANGLE = ephem.degrees('20')



FIELDS = ('rise_time', 'transit_time', 'set_time')
AZALT = ('rise_az', 'transit_alt', 'set_az')

# if __name__ == '__main__':
#     o = ephem.city('Columbus')
#     bodies = make_all_bodies()
#     events = []
#     for b in bodies:
#         b.compute(o)
#         for fname, azalt in zip(FIELDS, AZALT):
#             events.append(Event(b.name, fname,
#                 getattr(b, fname), getattr(b, azalt)))
#     events.sort(key=operator.attrgetter('date'))
#     for ev in events:
#         if ev.date >= ephem.now():
#             print(ev)

class Separation(collections.namedtuple('Separation', 'body1 body2 angle')):
    def trend(self):
        "Returns True if the two bodies are getting closer"
        arrows = "UD" #
        a = self.body1.copy()
        b = self.body2.copy()
        later = ephem.now() + ephem.hour
        a.compute(later)
        b.compute(later)
        return ephem.separation(a, b) < self.angle

class Calculate:
    def __init__(self, default):
        self.default = default
        self.observer = ephem.city('Columbus')
        self.sun = ephem.Sun()
        self.moon = ephem.Moon()
        self.planets = [planet() for planet in PLANETS]
        self.stars = [ephem.star(name) for name in STARS]
        comet_dict = Comets()
        self.comets = [comet_dict[name] for name in COMETS]
        self.except_stars = [self.sun, self.moon] + \
                            self.planets + self.comets
        self.all_bodies = self.except_stars + self.stars

    def update(self, w, default):
        if default != self.default:
            w.erase()
        self.date = ephem.now()
        self.observer.date = self.date
        w.addstr(0, 0, "{:%H:%M:%S}".format(
            ephem.localtime(self.date)))
        w.addch(0, 30, default)
        w.addstr(0, 40, 'admrpq')
        arg = self.observer if default in ('r', 'p', 'm') else self.date
        [body.compute(arg) for body in self.all_bodies]
        if default == 'a':
            self.update_angles(w)
        elif default == 'd':
            self.update_distance(w)
        elif default == 'p':
            self.sky_position(w)
        elif default == 'r':
            self.rise_set(w)
        elif default == 'm':
            self.update_moon(w)
        self.default = default

    def update_angles(self, w):
        # Calculate angular separation between planetary bodies
        angles = []
        for a, b in itertools.combinations(self.all_bodies, 2):
            angle = ephem.separation(a, b)
            if angle < MAX_ANGLE:
                angles.append(Separation(a, b, angle))
        angles.sort(key=operator.attrgetter('angle'))
        w.addstr(2, 0, 'Angular separation')
        for row, sep in enumerate(angles):
            color = 1 if sep.trend() else 2
            w.addstr(row + 3, 0,
                "{1} {0.body1.name} ⇔ {0.body2.name}".format(
                    sep, _(sep.angle)),
                curses.color_pair(color))
            w.clrtoeol()

    def update_distance(self, w):
        # Calculate distance and velocity for objects of interest

        distances = [
            Distance(self.date, body)
            for body in self.except_stars
        ]
        distances.sort(key=operator.attrgetter('mph'))
        w.addstr(2, 0, 'Distances')
        for row, obj in enumerate(distances):
            color = 1 if obj.trend else 2
            w.addstr(row + 3, 0,
                "{0.mph:7,.0f} mph {0.miles:13,.0f} {0.body.name}".format(obj),
                curses.color_pair(color))

    def sky_position(self, w):
        w.addstr(2, 0, 'Azimuth and Altitude')
        for row, b in enumerate(sorted(self.except_stars, key=operator.attrgetter('alt'), reverse=True)):
            if b.name == 'Sun':
                color = 3
            elif b.alt < 0:
                color = 0
            else:
                color = 1 if b.az < ephem.degrees('180') else 2
            w.addstr(row + 3, 0,
                "{0.name} {0.az} {0.alt}".format(b),
                curses.color_pair(color))

    def update_moon(self, w):
        w.addstr(2, 0, 'Moon')

    def rise_set(self, w):
        w.addstr(2, 0, 'Rise, Transit and Set')
        events = []
        for b in self.except_stars:
            for fieldname, azalt in zip(FIELDS, AZALT):
                date = getattr(b, fieldname)
                if date >= self.date:
                    events.append({'key': fieldname.split('_')[0],
                                   'name': b.name,
                                   'date': ephem.localtime(date),
                                   'azalt': getattr(b, azalt)})
        for row, ev in enumerate(sorted(events, key=operator.itemgetter('date'))):
            if ev['key'] == 'transit':
                color = 1
            elif ev['key'] == 'set':
                color = 2
            else:
                color = 0
            w.addstr(row + 3, 0,
                "{name:16} {key:8} {date:%H:%M:%S} {azalt}".format(**ev),
                curses.color_pair(color))
class Distance:
    def __init__(self, date, body):
        self.body = body
        self.miles = miles_from_au(body.earth_distance)
        x = body.copy()
        x.compute(ephem.date(date + ephem.hour))
        moved = miles_from_au(x.earth_distance) - self.miles
        self.trend = moved < 0
        self.mph = abs(moved)


def main(w):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    w.timeout(2000)
    default = 'p'
    calculate = Calculate(default)

    while True:
        try:
            ch = w.getch()
            if ch == ord('a'):
                default = 'a'
            elif ch == ord('d'):
                default = 'd'
            elif ch == ord('p'):
                default = 'p'
            elif ch == ord('r'):
                default = 'r'
            elif ch == ord('m'):
                default = 'm'
            elif ch == ord('q'):
                break
            calculate.update(w, default)
            curses.curs_set(0)
            w.refresh()
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    curses.wrapper(main)


