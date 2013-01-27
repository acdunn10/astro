import sys
import os
import operator
import curses
import itertools
import collections
import logging
import subprocess
import ephem
from astro import Comets
from astro.utils import pairwise
from astro.utils import format_angle as _
from astro import miles_from_au
from astro import PLANETS, SYMBOLS, CITY

logger = logging.getLogger('astro')

STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux',
         'Regulus', 'Nunki', 'Alcyone', 'Elnath')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')
MAX_ANGLE = ephem.degrees('30')
COMMANDS = 'adDemrp'

FIELDS = ('rise_time', 'transit_time', 'set_time')
AZALT = ('rise_az', 'transit_alt', 'set_az')


class Calculate:
    "Manage the display of data in the curses window"
    def __init__(self):
        "Load up initial data, including the comets"
        self.cmd = 'p'
        self.observer = ephem.city(CITY)
        self.sun = ephem.Sun()
        self.moon = ephem.Moon()
        self.planets = [planet() for planet in PLANETS]
        self.stars = [ephem.star(name) for name in STARS]
        comet_dict = Comets()
        logger.info("Comets last-modified: {}".format(comet_dict.last_modified))
        self.comets = [comet_dict[name] for name in COMETS]
        self.except_stars = [self.sun, self.moon] + \
                            self.planets + self.comets
        self.all_bodies = self.except_stars + self.stars
        self.rs = collections.defaultdict(list)
        self.rs_events = []

    def compute(self):
        "Compute data for all bodies, not using the Observer"
        [body.compute(self.date) for body in self.all_bodies]
        return self

    def compute_observer(self):
        "Compute with the Observer"
        [body.compute(self.observer) for body in self.all_bodies]
        return self

    def update(self, w, cmd):
        "Update the window to display the specified info"
        if cmd != self.cmd:
            w.erase()
            logger.debug("New command: {}".format(cmd))
        self.date = ephem.now()
        self.observer.date = self.date
        w.addstr(0, 0, "{:%H:%M:%S} {:11.5f}".format(
            ephem.localtime(self.date), self.date))
        w.addstr(0, 40, COMMANDS)
        if cmd == 'a':
            self.compute().update_angles(w)
        elif cmd == 'd':
            self.compute().update_distance(w)
        elif cmd == 'D':
            self.compute().update_sun_distance(w)
        elif cmd == 'p':
            self.compute_observer().update_position(w)
        elif cmd == 'r':
            self.update_rise_set(w)
        elif cmd == 'm':
            self.compute().update_moon(w)
        elif cmd == 'e':
            self.compute().update_elongation(w)
        self.cmd = cmd
        today = int(float(self.date))
        for i in range(today, today + 3):
            if i not in self.rs:
                self.calc_rise_set(i)


    def update_angles(self, w):
        "Display the closest angular separations"
        angles = (
            Separation(a, b, ephem.separation(a, b))
            for a, b in itertools.combinations(self.all_bodies, 2)
            )
        #angles = filter(lambda x:x.angle < MAX_ANGLE, angles)
        angles = itertools.filterfalse(lambda x:x.is_two_stars(), angles)
        w.addstr(2, 0, 'Angular separation')
        for row, sep in enumerate(sorted(angles, key=operator.attrgetter('angle'))):
            try:
                w.addstr(row + 3, 0, *sep.format())
            except curses.error:
                break
            w.clrtoeol()

    def update_elongation(self, w):
        "Elongation for the planets and comets"
        w.addstr(2, 0, 'Elongation')
        bodies = self.planets + self.comets
        for row, body in enumerate(sorted(bodies, key=operator.attrgetter('elong'))):
            w.addstr(row + 3, 0,
                "{} {:>13} {}".format(
                    get_symbol(body), _(body.elong), body.name))
            w.clrtoeol()

    def update_distance(self, w):
        "Distance and speed (relative to Earth) for objects of interest"
        self._update_distance(w, 'earth_distance', 'Earth Distances')

    def update_sun_distance(self, w):
        "Distance and speed relative to Sun"
        self._update_distance(w, 'sun_distance', 'Sun Distances')

    def _update_distance(self, w, attr, title):
        distances = (
            Distance(self.date, body, attr)
            for body in self.except_stars
            )
        w.addstr(2, 0, title)
        for row, obj in enumerate(sorted(distances, key=operator.attrgetter('mph'))):
            w.addstr(row + 3, 0, *obj.format())
            w.clrtoeol()

    def update_position(self, w):
        "Display sky position"
        w.addstr(2, 0, 'Azimuth and Altitude')
        #is_sun_or_is_up = lambda body:body.name == 'Sun' or body.alt > 0
        bodies = self.except_stars  #filter(is_sun_or_is_up, self.except_stars)
        flag = 3
        for row, body in enumerate(sorted(bodies, key=operator.attrgetter('alt'), reverse=True)):
            try:
                if flag == 3 and body.alt < 0:  # first body below horizon
                    w.hline(row + flag, 0, '-', 60)
                    flag = 4
                w.addstr(row + flag, 0, *format_sky_position(body))
                w.clrtoeol()
            except curses.error:
                break
        w.clrtobot()

    def update_moon(self, w):
        "Display some info about the Moon"
        moon = ephem.Moon(self.date)
        # young or old (within 72 hours)
        previous_new = ephem.previous_new_moon(self.date)
        age = 24 * (self.date - previous_new)
        msg = ''
        if age <= 72:
            msg = "Young: {:.1f} hours".format(age)
        else:
            next_new = ephem.next_new_moon(self.date)
            age = 24 * (next_new - self.date)
            if age <= 72:
                msg = "Old: {:.1f} hours".format(age)
        w.addstr(2, 0,
            'Moon: Phase={0.moon_phase:.2%} {1}'.format(moon, msg))
        distance = miles_from_au(moon.earth_distance)
        moon.compute(ephem.Date(self.date + ephem.hour))
        moved = miles_from_au(moon.earth_distance) - distance
        color = 2 if moved > 0 else 1
        w.addstr(3, 0,
            'Earth distance:    {:13,.0f} miles, {:+5.0f} mph'.format(
                distance, moved), curses.color_pair(color))
        observer = ephem.city(CITY)
        observer.date = self.date
        moon.compute(observer)
        m2 = moon.copy()
        distance = miles_from_au(moon.earth_distance)
        observer.date = ephem.Date(self.date + ephem.hour)
        moon.compute(observer)
        moved = miles_from_au(moon.earth_distance) - distance
        color = 2 if moved > 0 else 1
        w.addstr(4, 0,
            'Observer distance: {:13,.0f} miles, {:+5.0f} mph'.format(
                distance, moved), curses.color_pair(color))
        w.addstr(5, 0, "Azimuth {}".format(_(m2.az)))
        w.addstr(5, 30, "Altitude {}".format(_(m2.alt)))


    def calc_rise_set(self, base_date):
        "Get rise, transit and setting info for the specified date"
        self.observer.date = ephem.Date(base_date)
        logger.info("calc_rise_set: {0.observer.date}".format(self))
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

    def update_rise_set(self, w):
        "Display rise, transit and set, ordered chronologically"
        events = []
        localdate = ephem.localtime(self.date)
        for key in self.rs.keys():
            for ev in self.rs[key]:
                if ev['date'] >= localdate:
                    events.append(ev)
        w.addstr(2, 0, 'Rise, Transit and Set {:2d} {:4d}'.format(
            len(self.rs), len(events)))
        events.sort(key=operator.itemgetter('date'))
        for row, ev in enumerate(events):
            try:
                w.addstr(row + 3, 0, *format_rise_set(ev))
                w.clrtoeol()
            except curses.error:
                break

def format_rise_set(ev):
    "Formatting details for update_rise_set"
    if ev['name'] == 'Sun':
        color = 3
    elif ev['key'] == 'transit':
        color = 1
    elif ev['key'] == 'set':
        color = 2
    else:
        color = 0
    return (
        "{symbol} {date:%a %I:%M:%S %p} {key:^7} {name} {azalt}°".format(**ev),
        curses.color_pair(color)
        )


def format_sky_position(body):
    "Formatting details for update_position"
    if body.name == 'Sun':
        color = 3
    elif body.alt < 0:
        color = 0
    else:
        color = 1 if body.az < ephem.degrees('180') else 2
    symbol = get_symbol(body)
    if body.name == 'Moon':
        extra = "Phase {0.moon_phase:.2%}".format(body)
    elif body.name != 'Sun':
        extra = "{0.mag:+.1f}".format(body)
    else:
        extra = ''
    return (
        "{} {:>12} {:>12} {} {}".format(get_symbol(body), _(body.alt),
            _(body.az), body.name, extra),
        curses.color_pair(color)
        )

def get_symbol(body):
    "Get the traditional planetary symbols, among others"
    if isinstance(body, ephem.HyperbolicBody):
        key = '_comet'
    elif isinstance(body, ephem.FixedBody):
        key = '_star'
    else:
        key = body.name
    return SYMBOLS[key]

class Separation(collections.namedtuple('Separation', 'body1 body2 angle')):
    "Manage info about the angular separation between two bodies"
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

    def format(self):
        "Formatting details for update_angles"
        color = 1 if self.trend() else 2
        return (
            "{1:>12}  {2}  {0.body1.name} ⇔ {3} {0.body2.name} ({4})".format(
                self, _(self.angle), get_symbol(self.body1),
                get_symbol(self.body2),
                ephem.constellation(self.body2)[1]),
            curses.color_pair(color)
            )

class Distance:
    "Manage info about the distance between two bodies"
    def __init__(self, date, body, attr='earth_distance'):
        self.body = body
        self.miles = miles_from_au(getattr(body, attr))
        x = body.copy()
        x.compute(ephem.date(date + ephem.hour))
        moved = miles_from_au(getattr(x, attr)) - self.miles
        self.trend = moved < 0
        self.mph = abs(moved)

    def format(self):
        "Formatting details for update_distance"
        color = 1 if self.trend else 2
        return (
            "{0.mph:8,.0f} mph {0.miles:13,.0f} {1} {0.body.name}".format(
                self, get_symbol(self.body)),
            curses.color_pair(color)
            )

def growl(message):
    "Send a message to Growl, if we can"
    growl_path = '/usr/local/bin/growlnotify'
    if os.path.exists(growl_path):
        subprocess.call([growl_path, '-m', '"{}"'.format(message)])
    logger.info("Growl: '{}'".format(message))

def main(w):
    "Initialize and then manage the event loop"
    logger.info('Startup')
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    w.timeout(2000)
    calculate = Calculate()

    cmd = 'p'
    ord_commands = list(map(ord, COMMANDS))
    while True:
        try:
            ch = w.getch()
            if ch == ord('q'):
                break
            if ch in ord_commands:
                cmd = bytes([ch]).decode()
            calculate.update(w, cmd)
            curses.curs_set(0)
            w.refresh()
        except KeyboardInterrupt:
            break
    logger.info('Shutdown')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
        filename=os.path.expanduser('~/Library/Logs/astro-ctwin.log'),
        format="%(asctime)s [%(name)s.%(funcName)s] %(levelname)s: %(message)s")
    curses.wrapper(main)

