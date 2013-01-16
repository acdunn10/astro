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

bodies = {}
events = {}
event_queue = queue.PriorityQueue()
body_queue = queue.Queue()
reschedule_queue = queue.Queue()

@functools.total_ordering
class Event:
    def __init__(self, body_name, date, event_name, azalt):
        self.body_name = body_name
        self.date = date
        self.event_name = event_name
        self.azalt = azalt
        assert date is not None
        self.priority = float(date) if date is not None else 0.0
        self.key = '{0.body_name}:{0.event_name}'.format(self)

    def __str__(self):
        return "{0.date} {0.body_name} {0.event_name}".format(self)

    def __eq__(self, other):
        return self.priority == other.priority

    def __lt__(self, other):
        return self.priority < other.priority


def event_consumer():
    logger.debug("Startup")
    while True:
        logger.debug("{:4d} {:4d} get".format(
            event_queue.qsize(), len(events)))
        ev = event_queue.get()
        event_queue.task_done()
        print("Next event: {}".format(ev))
        while True:
            seconds_to_go = 86400 * (ev.date - ephem.now())
            if seconds_to_go < 0:
                break
            logger.debug("In {:.0f} seconds: {}".format(seconds_to_go, ev))
            time.sleep(min(10, seconds_to_go))
        print("EVENT: {}".format(ev))
        reschedule_queue.put(ev)

def rescheduler():
    logger.debug("Startup")
    while True:
        logger.debug("{:4d} {:4d} get".format(
            reschedule_queue.qsize(), len(events)))
        ev = reschedule_queue.get()
        logger.debug("Rescheduling:{}".format(ev))
        del events[ev.key]
        observer = ephem.city(CITY)
        next_method = {
            'rise_time': observer.next_rising,
            'transit_time': observer.next_transit,
            'set_time': observer.next_setting,
            }[ev.event_name]
        body = bodies[ev.body_name]
        body.compute(ephem.now())
        start_date = ephem.Date(ev.date + ephem.minute)
        date = next_method(body, start=start_date)
        if date is not None:
            altaz = getattr(body, {
                'rise_time': 'rise_az',
                'transit_time': 'transit_alt',
                'set_time': 'set_az',
                }[ev.event_name])
            new_ev = Event(ev.body_name, date, ev.event_name, altaz)
            event_queue.put(new_ev)
            events[new_ev.key] = new_ev
            logger.debug("Rescheduled: {}".format(new_ev))
        reschedule_queue.task_done()



def body_consumer():
    logger.debug("Startup")
    observer = ephem.city(CITY)
    while True:
        try:
            body = body_queue.get_nowait()
            body.compute(observer)
            logger.debug("Working on {0.name}".format(body))
            for fieldname, azalt in zip(FIELDS, AZALT):
                date = getattr(body, fieldname)
                azalt = getattr(body, azalt)
                if date is not None:
                    ev = Event(body.name, date, fieldname, azalt)
                    event_queue.put(ev)
                    events[ev.key] = ev
            body_queue.task_done()
        except queue.Empty:
            pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
        filename=os.path.expanduser('~/Library/Logs/AstroWatcher.log'),
        format="%(asctime)s %(levelname)s %(threadName)s %(message)s")
    # Load the body queue before we start things up
    sun_and_moon = [ephem.Sun(), ephem.Moon()]
    planets = [planet() for planet in PLANETS]
    star_list = [ephem.star(name) for name in stars.keys()]
    comets = Comets()
    all_bodies = sun_and_moon + planets + star_list + list(comets.values())
    for body in all_bodies: #sun_and_moon:
        body_queue.put(body)
        bodies[body.name] = body
    threading.Thread(target=body_consumer, name='BodyConsumer').start()
    logger.debug('BodyConsumer started')
    # wait until the queue is filled
    while not body_queue.empty():
        logger.debug("wait for queue: {}".format(body_queue.qsize()))
        time.sleep(0.1)
    threading.Thread(target=event_consumer, name='EventConsumer').start()
    threading.Thread(target=rescheduler, name='Rescheduler').start()

