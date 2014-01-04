import sys
import os
import operator
import curses
import math
import itertools
import collections
import logging
import logging.handlers
import subprocess
import threading
import queue
import time
import warnings
warnings.simplefilter('default')
import ephem
from astro import PLANETS, SYMBOLS, COMETS
from astro.comets import Comets, Asteroids
from astro.utils import pairwise, miles_from_au, format_angle as _
from ephem.stars import stars
from astro.satellites import EarthSatellites
import requests
import json

logger = logging.getLogger('astro')

STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux',
         'Regulus', 'Nunki', 'Alcyone', 'Elnath')
ASTEROIDS = ('3753 Cruithne', )
SATELLITES = ('HST', 'ISS (ZARYA)', 'TIANGONG 1')
SPECIAL_STARS = ('Sirius',)  # I just like this one

COMMANDS = 'adDeLmrp!?'
TRANSIT_METHODS = ('next_transit', 'next_antitransit')

HELP = {
    'a': 'Angular separation',
    'd': 'Distance from Earth',
    'D': 'Distance from the Sun',
    'e': 'Elongation',
    'L': 'Logging',
    'm': 'Moon',
    'r': 'Rise, Transit, Antitransit, Set and Satellite Passes',
    'p': 'Position in the sky (azimuth and altitude)',
    '!': 'Request and use current location',
    '?': 'Help',
    }

def format_rise_transit_set(dct):
    key = dct['key']
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

def m_to_mi(meters):
    return meters / 1609.344

class _Observer:
    def __init__(self):
        self.default = ephem.city('Columbus')
        self.current = None

    def __call__(self):
        if self.current is not None:
            return self.current
        return self.default

    def update(self):
        url = os.environ.get('LOCATION_URL', None)
        if url is not None:
            try:
                r = requests.get(url, params={'format': 'json'})
                if r.status_code == 200:
                    data = json.loads(str(r.content, 'utf-8'))
                    data = data['objects'][0]
                    observer = ephem.Observer()
                    observer.lat = str(data['latitude'])
                    observer.lon = str(data['longitude'])
                    self.current = observer
            except requests.exceptions.RequestException as e:
                logger.error(str(e))

Observer = _Observer()

class RiseTransitSetProcessor(threading.Thread):
    def __init__(self, requests, results):
        super().__init__()
        self.name = self.__class__.__name__
        self.requests = requests
        self.results = results
        logger.debug("Init")

    def run(self):
        logger.debug("Running")
        while True:
            dct = self.requests.get()
            self.requests.task_done()
            if dct is None:
                break
            logger.debug('Request: {kind} for {body.name}'.format(**dct))
            observer = Observer()
            observer.date = ephem.Date(ephem.now() + ephem.minute)
            method = getattr(observer, dct['kind'])
            try:
                dct['date'] = method(dct['body'])
                azalt = dct['body'].alt if dct['kind'] in TRANSIT_METHODS else dct['body'].az
                dct['azalt'] = int(math.degrees(azalt))
                dct['key'] = dct['kind'].split('_')[1]
                self.results.put(dct)
            except ephem.CircumpolarError as e:
                logger.error(str(e))
        logging.debug("Terminated")

class SatellitePassProcessor(threading.Thread):
    def __init__(self, requests, results):
        super().__init__()
        self.name = self.__class__.__name__
        self.requests = requests
        self.results = results
        logger.debug("Init")

    def run(self):
        logger.debug("Running")
        keys = ('rising', 'transit', 'setting')
        while True:
            dct = self.requests.get()
            self.requests.task_done()
            if dct is None:
                break
            logger.debug('Request: {kind} for {body.name}'.format(**dct))
            observer = Observer()
            observer.date = ephem.Date(ephem.now() + ephem.minute)
            method = getattr(observer, dct['kind'])
            info = method(dct['body'])
            args = zip(*[iter(info)] * 2)
            for ((date, azalt), key) in zip(args, keys):
                if date and azalt:
                    d = dct.copy()
                    d['date'] = date
                    d['azalt'] = int(math.degrees(azalt))
                    d['key'] = key
                    d['reschedule'] = (key == 'setting')
                    self.results.put(d)
        logging.debug("Terminated")

class DistanceList(list):
    "A list of distances, recalculated every minute"
    def __init__(self, attr, title):
        self.attr = attr
        self.title = title
        self.next_update = 0
        super().__init__()

    def update(self, date, bodies):
        self.clear()
        for body in bodies:
            self.append(Distance(date, body, self.attr))
        self.next_update = ephem.date(date + ephem.minute)

    def display(self, w):
        w.addstr(2, 0,
            "{0.title}. Next update at {0.next_update}".format(self))
        for row, obj in enumerate(sorted(self, key=operator.attrgetter('mph'))):
            w.addstr(row + 3, 0, *obj.format())
            w.clrtoeol()

class Calculate:
    "Manage the display of data in the curses window"
    def __init__(self, cmd):
        "Load up initial data, including the comets"
        self.logging_queue = queue.Queue()
        self.logging_counter = 0
        handler = logging.handlers.QueueHandler(self.logging_queue)
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        self.logging_messages = collections.deque([], 20)

        self.cmd = cmd
        self.observer = Observer()
        self.sun = ephem.Sun()
        self.moon = ephem.Moon()
        self.planets = [planet() for planet in PLANETS]
        self.stars = [ephem.star(name) for name in STARS]
        self.special = [ephem.star(name) for name in SPECIAL_STARS]
        comet_dict = Comets()
        logger.info("Comets last-modified: {}".format(comet_dict.last_modified))
        self.comets = [
            comet_dict[name]
            for name in COMETS
            if name in comet_dict
            ]
        asteroid_dict = Asteroids()
        logger.info("Asteroids last-modified: {}".format(asteroid_dict.last_modified))
        self.asteroids = [
            asteroid_dict[name]
            for name in ASTEROIDS
            if name in asteroid_dict
            ]
        sats = EarthSatellites()
        logger.info("Earth Satellites last-modified: {}".format(
            sats.last_modified))
        self.satellites = [
            sats[name]
            for name in SATELLITES
            if name in sats
            ]
        self.except_stars = [self.sun, self.moon] + \
                            self.planets + self.comets + \
                            self.asteroids
        self.all_bodies = self.except_stars + self.stars
        self.everything = self.all_bodies + self.special
        self.rst_events = []
        self.earth_distances = DistanceList('earth_distance', 'Earth Distances')
        self.sun_distances = DistanceList('sun_distance', 'Sun Distances')

        # Start the thread that calculates rise, transit, set
        self.rst_requests = queue.Queue()
        self.rst_results = queue.Queue()
        RiseTransitSetProcessor(
            self.rst_requests, self.rst_results).start()

        def make_rst_request(body):
            for kind in ('next_rising', 'next_setting') + TRANSIT_METHODS:
                self.rst_requests.put({'body': body, 'kind': kind})

        [make_rst_request(body) for body in self.except_stars + self.special]

        # A different thread to handle Earth Satellites
        self.pass_requests = queue.Queue()
        SatellitePassProcessor(
            self.pass_requests, self.rst_results).start()

        [self.pass_requests.put({'body':body, 'kind':'next_pass'})
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

    def quit(self):
        logger.debug("Quitting requested")
        self.rst_requests.put(None)  # a poison pill for the thread
        self.pass_requests.put(None)
        self.rst_requests.join()  # wait for it to finish
        self.pass_requests.join()
        logger.debug("Quit")

    def compute(self):
        "Compute data for all bodies, not using the Observer"
        [body.compute(self.date) for body in self.everything]
        return self

    def compute_observer(self):
        "Compute with the Observer"
        [body.compute(self.observer) for body in self.everything]
        return self

    def update(self, w, cmd):
        "Update the window to display the specified info"
        if cmd == '!':
            Observer.update()
            cmd = self.cmd
        self.observer = Observer()
        if cmd != self.cmd:
            w.erase()
            logger.debug("New command: {}".format(cmd))
        self.date = ephem.now()
        self.observer.date = self.date
        w.addstr(0, 0, "{:%H:%M:%S} {:%H:%M:%S} UT {:11,.5f} {:04d}".format(
            ephem.localtime(self.date), self.date.datetime(),
            self.date, self.logging_counter))
        w.addstr(0, 45, COMMANDS)
        w.addstr(1, 8, "Location: Lat {}  Lon {}".format(
            _(self.observer.lat), _(self.observer.lon)))

        try:
            if cmd == 'a':
                self.compute().update_angles(w)
            elif cmd == 'd':
                self.compute().update_earth_distance(w)
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
            elif cmd == '?':
                self.help(w)
            elif cmd == 'L':
                self.logging(w)
        except curses.error:
            pass
        self.cmd = cmd

        # Add any newly calculated rst events to my list
        while True:
            try:
                event = self.rst_results.get_nowait()
                self.rst_results.task_done()
                self.rst_events.append(event)
                logger.debug('Added: {key} for {body.name}'.format(**event))
            except queue.Empty:
                break
        # Get rid of past events and reschedule
        for event in reversed(self.rst_events):
            if event['date'] < self.date:
                if event.get('reschedule', True):
                    q = self.pass_requests if event['kind'] == 'next_pass' else self.rst_requests
                    q.put(event)
                logger.debug('Deleting: {key} for {body.name}'.format(**event))
                self.rst_events.remove(event)
        # the logging queue
        while True:
            try:
                record = self.logging_queue.get_nowait()
                self.logging_queue.task_done()
                self.logging_counter += 1
                self.logging_messages.append(record)
            except queue.Empty:
                break

    def help(self, w):
        w.addstr(2, 0, 'Help')
        for row, letter in enumerate(COMMANDS):
            w.addstr(row + 3, 0, "{}: {}".format(letter, HELP[letter]))

    def logging(self, w):
        w.addstr(2, 0, "Logging")
        for row, record in enumerate(self.logging_messages):
            w.addstr(row + 3, 0, record.getMessage())
            w.clrtoeol()

    def update_angles(self, w):
        "Display the closest angular separations"
        angles = (
            Separation(a, b, ephem.separation(a, b))
            for a, b in itertools.combinations(self.all_bodies, 2)
            )
        angles = itertools.filterfalse(lambda x:x.is_two_stars(), angles)
        w.addstr(2, 0, 'Angular separation')
        for row, sep in enumerate(sorted(angles, key=operator.attrgetter('angle'))):
            w.addstr(row + 3, 0, *sep.format())
            w.clrtoeol()

    def update_elongation(self, w):
        "Elongation for the planets and comets"
        w.addstr(2, 0, 'Elongation')
        bodies = self.planets + self.comets + self.asteroids +\
                 [self.moon] + self.special
        for row, body in enumerate(sorted(bodies, key=operator.attrgetter('elong'))):
            w.addstr(row + 3, 0,
                "{} {:>13} {}".format(
                    get_symbol(body), _(body.elong), body.name))
            w.clrtoeol()

    def update_earth_distance(self, w):
        "Distance and speed (relative to Earth) for objects of interest"
        if self.date >= self.earth_distances.next_update:
            self.earth_distances.update(self.date, self.except_stars)
        self.earth_distances.display(w)

    def update_sun_distance(self, w):
        "Distance and speed relative to Sun"
        if self.date >= self.sun_distances.next_update:
            self.sun_distances.update(self.date, self.except_stars)
        self.sun_distances.display(w)


    def update_position(self, w):
        "Display sky position"
        w.addstr(2, 0, 'Altitude and Azimuth')
        [body.compute(self.observer) for body in self.satellites]
        bodies = self.except_stars + self.satellites + self.special
        flag = 3
        for row, body in enumerate(sorted(bodies, key=operator.attrgetter('alt'), reverse=True)):
            if flag == 3 and body.alt < 0:  # first body below horizon
                w.hline(row + flag, 0, '-', 60)
                flag = 4
            w.addstr(row + flag, 0, *format_sky_position(body))
            w.clrtoeol()
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
        observer = Observer()
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
        w.addstr(6, 0, "Declination {}".format(_(m2.dec)))

    def update_rise_set(self, w):
        "Display rise, transit and set, ordered chronologically"
        w.addstr(2, 0, 'Rise, Transit and Set events={:5d} requests={:5d}'.format(
            len(self.rst_events), self.rst_requests.qsize()))
        for row, ev in enumerate(sorted(self.rst_events, key=operator.itemgetter('date'))):
            w.addstr(row + 3, 0, *format_rise_transit_set(ev))
            w.clrtoeol()


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
        #extra = "#{0._orbit} Incl={0._inc}°".format(body)
        extra = "i{1:.0f}° {2:,.0f} {3:,.0f} {0}".format(
            not body.eclipsed, math.degrees(body._inc), m_to_mi(body.range),
            m_to_mi(body.range_velocity))
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

    try:
        cmd = sys.argv[1]
        if cmd not in COMMANDS:
            cmd = 'p'
    except IndexError:
        cmd = 'p'
    calculate = Calculate(cmd)

    ord_commands = list(map(ord, COMMANDS))
    while True:
        try:
            ch = w.getch()
            if ch == ord('q'):
                calculate.quit()
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
    logging.basicConfig(level=logging.INFO,
        filename=os.path.expanduser('~/Library/Logs/astro-ctwin.log'),
        format="%(asctime)s [%(threadName)s:%(name)s.%(funcName)s] %(levelname)s: %(message)s")
    logging.captureWarnings(True)
    curses.wrapper(main)

