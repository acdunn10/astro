""" Another exercise in working with threads.
"""
import sys
import os
import operator
#import curses
import itertools
import collections
import functools
import logging
import heapq
import threading
import queue
import time
import ephem
from ephem.stars import stars
from astro import Comets, STARS, COMETS
from astro import PLANETS, SYMBOLS, CITY

logger = logging.getLogger('rank_watcher')

FIELDS = ('rise_time', 'transit_time', 'set_time')  # order is important
AZALT = ('rise_az', 'transit_alt', 'set_az')

event_queue = queue.PriorityQueue()  # rise,transit,set ordered by date
reschedule_queue = queue.Queue()
position_queue = queue.Queue()

@functools.total_ordering
class Event:
    "A rise, transit or set event"
    def __init__(self, body_name, date, event_name, azalt):
        self.body_name = body_name
        self.date = date
        self.event_name = event_name
        self.azalt = azalt  # rise/set azimuth or transit altitude
        self.key = '{0.body_name}:{0.event_name}'.format(self)

    def __str__(self):
        return "{0.date} {0.body_name} {0.event_name}".format(self)

    def __eq__(self, other):
        return self.date == other.date

    def __lt__(self, other):
        return self.date < other.date


def event_consumer():
    logger.debug("Startup")
    while True:
        logger.debug("{:4d} get".format(event_queue.qsize()))
        ev = event_queue.get()
        event_queue.task_done()
        seconds_to_go = 86400 * (ev.date - ephem.now())
        if seconds_to_go > 0:
            time.sleep(seconds_to_go)
        logger.info(str(ev))
        reschedule_queue.put(ev)

def position_consumer():
    logger.debug("Startup")
    while True:
        position = position_queue.get()
        print(position)
        position_queue.task_done()

def planetary_body(body, update_rate):
    logger.debug("Startup")
    observer = ephem.city(CITY)
    body.compute(observer)
    for fieldname, azalt in zip(FIELDS, AZALT):
        date = getattr(body, fieldname)
        azalt = getattr(body, azalt)
        if date is not None:
            ev = Event(body.name, date, fieldname, azalt)
            event_queue.put(ev)
    while True:
        observer.date = ephem.now()
        body.compute(observer)
        position_queue.put("{0.name} {0.alt} {0.az}".format(body))
        time.sleep(update_rate)

Config = collections.namedtuple('Config', 'body_list update_rate')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
        filename=os.path.expanduser('~/Library/Logs/AstroWatcher.log'),
        format="%(asctime)s %(levelname)s %(threadName)s %(message)s")
    # Load the body queue before we start things up
    LONG_LIST = False  # long list useful when debugging to have a lot of bodies
    comets = Comets()
    sun_and_moon = [ephem.Sun(), ephem.Moon()]
    planets = [planet() for planet in PLANETS]
    if LONG_LIST:
        star_list = [ephem.star(name) for name in stars.keys()]
        comet_list = list(comets.values())
    else:
        star_list = [ephem.star(name) for name in STARS]
        comet_list = [comets[name] for name in COMETS]
    #all_bodies = sun_and_moon + planets + star_list + comet_list
    configs = (
        Config(sun_and_moon, 3),
        Config(planets, 7),
        Config(comet_list, 13),
        Config(star_list, 59),
        )
    for config in configs:
        for body in config.body_list:
            print(body.name)
            t = threading.Thread(target=planetary_body,
                    args=(body, config.update_rate), name=body.name)
            t.start()
    threading.Thread(target=event_consumer, name='Events').start()
    threading.Thread(target=position_consumer, name='Position').start()
