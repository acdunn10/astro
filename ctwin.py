import operator
import curses
import itertools
import collections
import ephem
from astro import Comets
from astro.utils import pairwise
from astro.utils import format_angle as _
from astro import miles_from_au
from astro import PLANETS, SYMBOLS

STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux',
         'Regulus', 'Nunki', 'Alcyone', 'Elnath')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')
MAX_ANGLE = ephem.degrees('20')


FIELDS = ('rise_time', 'transit_time', 'set_time')
AZALT = ('rise_az', 'transit_alt', 'set_az')


class Separation(collections.namedtuple('Separation', 'body1 body2 angle')):
    def is_two_stars(self):
        return all([isinstance(self.body1, ephem.FixedBody),
                   isinstance(self.body2, ephem.FixedBody)])

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
        self.rs = collections.defaultdict(list)

    def update(self, w, default):
        if default != self.default:
            w.erase()
        self.date = ephem.now()
        self.observer.date = self.date
        w.addstr(0, 0, "{:%H:%M:%S} {:11.5f}".format(
            ephem.localtime(self.date), self.date))
        w.addch(0, 30, default)
        w.addstr(0, 40, 'admrpq')
        if default in 'pm':
            [body.compute(self.observer) for body in self.all_bodies]
        elif default in 'ad':
            [body.compute(self.date) for body in self.all_bodies]
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
        angles = (
            Separation(a, b, ephem.separation(a, b))
            for a, b in itertools.combinations(self.all_bodies, 2)
            )
        angles = filter(lambda x:x.angle < MAX_ANGLE, angles)
        angles = itertools.filterfalse(lambda x:x.is_two_stars(), angles)
        w.addstr(2, 0, 'Angular separation')
        for row, sep in enumerate(sorted(angles, key=operator.attrgetter('angle'))):
            color = 1 if sep.trend() else 2
            w.addstr(row + 3, 0,
                "{1} {2} {0.body1.name} ⇔ {3} {0.body2.name}".format(
                    sep, _(sep.angle), get_symbol(sep.body1),
                    get_symbol(sep.body2)),
                curses.color_pair(color))
            w.clrtoeol()

    def update_distance(self, w):
        # Calculate distance and velocity for objects of interest
        distances = (Distance(self.date, body) for body in self.except_stars)
        w.addstr(2, 0, 'Distances')
        for row, obj in enumerate(sorted(distances, key=operator.attrgetter('mph'))):
            w.addstr(row + 3, 0, *obj.format())
            w.clrtoeol()

    def sky_position(self, w):
        w.addstr(2, 0, 'Azimuth and Altitude')
        is_sun_or_is_up = lambda body:body.name == 'Sun' or body.alt > 0
        bodies = filter(is_sun_or_is_up, self.except_stars)
        for row, body in enumerate(sorted(bodies, key=operator.attrgetter('alt'), reverse=True)):
            w.addstr(row + 3, 0, *format_sky_position(body))
            w.clrtoeol()

    def update_moon(self, w):
        w.addstr(2, 0, 'Moon')

    def calc_rise_set(self, base_date):
        self.observer.date = ephem.Date(base_date)
        for body in self.except_stars:
            body.compute(self.observer)
            for fieldname, azalt in zip(FIELDS, AZALT):
                date = getattr(body, fieldname)
                if date is None:
                    continue
                self.rs[base_date].append({
                               'key': fieldname.split('_')[0],
                               'name': body.name,
                               'date': ephem.localtime(date),
                               'azalt': getattr(body, azalt),
                               'symbol': get_symbol(body)})

    def rise_set(self, w):
        today = int(float(self.date))
        for i in range(today, today + 3):
            if i not in self.rs:
                self.calc_rise_set(i)

        events = []
        localdate = ephem.localtime(self.date)
        for key in self.rs.keys():
            for ev in self.rs[key]:
                if ev['date'] >= localdate:
                    events.append(ev)
        w.addstr(2, 0, 'Rise, Transit and Set {:2d} {:4d}'.format(
            len(self.rs), len(events)))
        events.sort(key=operator.itemgetter('date'))
        for row, ev in enumerate(events[:30]):
            w.addstr(row + 3, 0, *format_rise_set(ev))
            w.clrtoeol()

def format_rise_set(ev):
    if ev['name'] == 'Sun':
        color = 3
    elif ev['key'] == 'transit':
        color = 1
    elif ev['key'] == 'set':
        color = 2
    else:
        color = 0
    return (
        "{key:8} {date:%a %I:%M:%S %p} {symbol} {name} {azalt}°".format(**ev),
        curses.color_pair(color)
        )


def format_sky_position(body):
    "Returns both the formatted string and the desired color"
    if body.name == 'Sun':
        color = 3
    elif body.alt < 0:  # even though we're not currently displaying this
        color = 0
    else:
        color = 1 if body.az < ephem.degrees('180') else 2
    symbol = get_symbol(body)
    if body.name == 'Moon':
        extra = "Phase {0.moon_phase:.2%}".format(body)
    elif body.name != 'Sun':
        extra = "Mag {0.mag:.1f}".format(body)
    else:
        extra = ''
    return (
        "{} {} {} {} {}".format(get_symbol(body), body.name,
                                _(body.az), _(body.alt), extra),
        curses.color_pair(color)
        )

def get_symbol(body):
    if isinstance(body, ephem.HyperbolicBody):
        key = '_comet'
    elif isinstance(body, ephem.FixedBody):
        key = '_star'
    else:
        key = body.name
    return SYMBOLS[key]

class Distance:
    def __init__(self, date, body):
        self.body = body
        self.miles = miles_from_au(body.earth_distance)
        x = body.copy()
        x.compute(ephem.date(date + ephem.hour))
        moved = miles_from_au(x.earth_distance) - self.miles
        self.trend = moved < 0
        self.mph = abs(moved)

    def format(self):
        #returns both the formatted string and the color
        color = 1 if self.trend else 2
        return (
            "{0.mph:7,.0f} mph {0.miles:13,.0f} {1} {0.body.name}".format(
                self, get_symbol(self.body)),
            curses.color_pair(color)
            )

def main(w):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    w.timeout(2000)
    default = 'r'
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
#     c = Calculate('r')
#     now = ephem.now()
#     today = int(float(now))
#     tomorrow = today + 1
#     print(now, today, tomorrow, float(now))
#     if today not in c.rs:
#         c.calc_rise_set(today)
#         print(len(c.rs))
#     if tomorrow not in c.rs:
#         c.calc_rise_set(tomorrow)
#         print(len(c.rs))
#     for key in (today, tomorrow):
#         print('\n***', key, len(c.rs[key]))
#         for ev in sorted(c.rs[key], key=operator.itemgetter('date')):
#             print('{date:%H:%M:%S %a}'.format(**ev))


