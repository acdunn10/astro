import sys
import os
import operator
import curses
import math
import itertools
import collections
import logging
import subprocess
import threading
import queue
import time
import warnings
warnings.simplefilter('default')
import ephem
from astro import Comets
from astro.utils import pairwise
from astro.utils import format_angle as _
from astro import miles_from_au
from astro import PLANETS, SYMBOLS, CITY
from ephem.stars import stars
from astro import EarthSatellites

logger = logging.getLogger('astro')

STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux',
         'Regulus', 'Nunki', 'Alcyone', 'Elnath')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)',
          '273P/Pons-Gambart', 'C/2012 F6 (Lemmon)',
          'C/2006 S3 (LONEOS)',
         )
COMMANDS = 'adDemrp'

rst_requests = queue.Queue()  # stores rise-transit-set requests
rst_results = queue.Queue()  # computed rise, transit and set times.

def format_rise_transit_set(dct):
    key = dct.get('key', dct['kind'].split('_')[1])
    if dct['body'].name == 'Sun':
        color = 3
    elif isinstance(dct['body'], ephem.EarthSatellite):
        color = 4
    elif key == 'transit':
        color = 1
    elif key == 'setting':
        color = 2
    else:
        color = 0
    return (
        "{} {:%a %I:%M:%S %p} {:^7} {} {}°".format(
            get_symbol(dct['body']), ephem.localtime(dct['date']), key,
            dct['body'].name, dct['azalt']),
        curses.color_pair(color)
        )


def handle_earth_satellite(dct, method):
    keys = ('rising', 'transit', 'setting')
    info = method(dct['body'])
    args = zip(*[iter(info)] * 2)
    for ((date, azalt), key) in zip(args, keys):
        if date and azalt:
            d = dct.copy()
            d['date'] = date
            d['azalt'] = azalt
            d['key'] = key
            d['reschedule'] = (key == 'setting')
            rst_results.put(d)


def handle_body(dct, method):
    "Get next rising, transit or setting"
    try:
        dct['date'] = method(dct['body'])
        azalt = dct['body'].alt if dct['kind'] == 'next_transit' else dct['body'].az
        dct['azalt'] = int(math.degrees(azalt))
        rst_results.put(dct)
    except ephem.CircumpolarError as e:
        logger.error(str(e))


def rst_producer(event):
    while not event.is_set():
        if event.wait(timeout=0.1):
            break
        try:
            dct = rst_requests.get(block=True, timeout=0.5)
            rst_requests.task_done()
            logger.debug('Request: {kind} for {body.name}'.format(**dct))
            observer = ephem.city(CITY)
            method = getattr(observer, dct['kind'])
            if dct['kind'] == 'next_pass':
                handle_earth_satellite(dct, method)
                continue
            else:
                handle_body(dct, method)
        except queue.Empty:
            pass


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
        sats = EarthSatellites()
        logger.info("Earth Satellites last-modified: {}".format(
            sats.last_modified))
        self.satellites = list(sats.values())
        self.except_stars = [self.sun, self.moon] + \
                            self.planets + self.comets
        self.all_bodies = self.except_stars + self.stars
        self.rst_events = []

        def make_rst_request(body):
            for kind in ('next_rising', 'next_transit', 'next_setting'):
                rst_requests.put({'body': body, 'kind': kind})

        [make_rst_request(body) for body in self.except_stars]
        [rst_requests.put({'body':body, 'kind':'next_pass'})
            for body in self.satellites
        ]

        # For testing rise/transit/set, it's useful to have
        # a large number of bodies
        if False:
            for name in stars.keys():
                star = ephem.star(name)
                make_rst_request(star)
            comets = Comets()
            for comet in comets.values():
                make_rst_request(comet)


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
        # Add any newly calculated rst events to my list
        while True:
            try:
                event = rst_results.get(block=False)
                rst_results.task_done()
                self.rst_events.append(event)
                logger.debug('Added: {kind} for {body.name}'.format(**event))
            except queue.Empty:
                break
        # Get rid of past events and reschedule
        for event in reversed(self.rst_events):
            if event['date'] < self.date:
                reschedule = event.get('reschedule', True)
                if reschedule:
                    rst_requests.put(event)
                logger.debug('Deleting: {kind} for {body.name}'.format(**event))
                self.rst_events.remove(event)


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
        [body.compute(self.observer) for body in self.satellites]
        bodies = self.except_stars + self.satellites
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

    def update_rise_set(self, w):
        "Display rise, transit and set, ordered chronologically"
        w.addstr(2, 0, 'Rise, Transit and Set events={:5d} requests={:5d}'.format(
            len(self.rst_events), rst_requests.qsize()))
        for row, ev in enumerate(sorted(self.rst_events, key=operator.itemgetter('date'))):
            try:
                w.addstr(row + 3, 0, *format_rise_transit_set(ev))
                w.clrtoeol()
            except curses.error:
                break


def format_sky_position(body):
    "Formatting details for update_position"
    if body.name == 'Sun':
        color = 3
    elif isinstance(body, ephem.EarthSatellite):
        color = 4
    elif body.alt < 0:
        color = 0
    else:
        color = 1 if body.az < ephem.degrees('180') else 2
    symbol = get_symbol(body)
    if body.name == 'Moon':
        extra = "Phase {0.moon_phase:.2%}".format(body)
    elif isinstance(body, ephem.EarthSatellite):
        extra = "#{0._orbit} Incl={0._inc}°".format(body)
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
    if isinstance(body, (ephem.HyperbolicBody, ephem.ParabolicBody, ephem.EllipticalBody)):
        key = '_comet'
    elif isinstance(body, ephem.FixedBody):
        key = '_star'
    elif isinstance(body, ephem.EarthSatellite):
        key = '_satellite'
    else:
        key = body.name
    return SYMBOLS.get(key, '?')

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
    producer_event = threading.Event()
    t = threading.Thread(target=rst_producer,
        args=(producer_event,), name='RST-Producer')
    t.start()

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
    producer_event.set()
    logger.info('Shutdown')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
        filename=os.path.expanduser('~/Library/Logs/astro-ctwin.log'),
        format="%(asctime)s [%(name)s.%(funcName)s] %(levelname)s: %(message)s")
    logging.captureWarnings(True)
    curses.wrapper(main)

