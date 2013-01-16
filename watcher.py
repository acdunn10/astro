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
from astro import Comets
from astro import PLANETS, SYMBOLS, CITY

logger = logging.getLogger('watcher')

STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux',
         'Regulus', 'Nunki', 'Alcyone', 'Elnath')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')
COMMANDS = 'ademrp'

FIELDS = ('rise_time', 'transit_time', 'set_time')  # order is important
AZALT = ('rise_az', 'transit_alt', 'set_az')

event_queue = queue.PriorityQueue()
body_queue = queue.Queue()

def event_consumer():
    logger.debug("Event consumer starting up")
    while True:
        logger.debug("{:4d} get".format(event_queue.qsize()))
        ev = event_queue.get()
        logger.debug("Working on: {}".format(ev))
        event_queue.task_done()
        while True:
            seconds_to_go = 86400 * (ev.date - ephem.now())
            if seconds_to_go <= 0:
                break
            logger.debug("In {:.0f} seconds: {}".format(seconds_to_go, ev))
            time.sleep(min(60, seconds_to_go))
        logger.info("EVENT: {}".format(ev))

@functools.total_ordering
class Event:
    def __init__(self, body_name, date, event_name, azalt):
        self.body_name = body_name
        self.date = date
        self.event_name = event_name
        self.azalt = azalt
        self.priority = float(date) if date is not None else 0.0

    def __str__(self):
        return "{0.date} {0.body_name} {0.event_name}".format(self)

    def __eq__(self, other):
        return self.priority == other.priority

    def __lt__(self, other):
        return self.priority < other.priority

def reschedule_event(ev, events, bodies, observer):
    if ev.event_name == 'rise_time':
        body = bodies[ev.body_name]
        date = observer.next_rising(body, start=ev.date)
        if date is not None:
            new_ev = Event(ev.body_name, date, 'rise_time', body.rise_az)
            heapq.heappush(events, new_ev)
            print("Rescheduled: {}".format(new_ev))


def event_producer():
    logger.debug("event_producer startup")
    observer = ephem.city(CITY)
    while True:
        body = body_queue.get()
        body.compute(observer)
        logger.debug("Working on {0.name}".format(body))
        for fieldname, azalt in zip(FIELDS, AZALT):
            date = getattr(body, fieldname)
            azalt = getattr(body, azalt)
            if date is not None:
                ev = Event(body.name, date, fieldname, azalt)
                event_queue.put(ev)
        body_queue.task_done()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
        format="%(levelname)s %(threadName)s %(message)s")
    for i in range(3):
        t = threading.Thread(target=event_producer,
            name='EventProducer #{}'.format(i))
        t.start()
    sun_and_moon = [ephem.Sun(), ephem.Moon()]
    planets = [planet() for planet in PLANETS]
    star_list = [ephem.star(name) for name in stars.keys()]
    for body in itertools.chain(sun_and_moon, planets, star_list):
        body_queue.put(body)
        time.sleep(.03)
    ct = threading.Thread(target=event_consumer, name='EventConsumer')
    ct.start()



