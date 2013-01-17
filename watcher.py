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

logger = logging.getLogger('watcher')

FIELDS = ('rise_time', 'transit_time', 'set_time')  # order is important
AZALT = ('rise_az', 'transit_alt', 'set_az')

bodies = {}  # get the right ephem when we need to reschedule
events = {}  # all events, indexed by key

event_queue = queue.PriorityQueue()  # rise,transit,set ordered by date
body_queue = queue.Queue()  # bodies from which to create Events
reschedule_queue = queue.Queue()  # events to be rescheduled

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
    """ Monitor the event_queue by getting the first event from it and
        then sleeping until that event happens.
    """
    logger.debug("Startup")
    while True:
        logger.debug("{:4d} {:4d} get".format(event_queue.qsize(), len(events)))
        ev = event_queue.get()
        event_queue.task_done()
        logger.info("Next event: {}".format(ev))
        while True:
            seconds_to_go = 86400 * (ev.date - ephem.now())
            if seconds_to_go < 0:
                break
            logger.debug("In {:.0f} seconds: {}".format(seconds_to_go, ev))
            time.sleep(min(10, seconds_to_go))
        logger.info("EVENT: {}".format(ev))
        reschedule_queue.put(ev)

def rescheduler():
    """ After an event happens, it's added to the reschedule queue
        so that the next time it occurs can be added to the event queue.
        For example, after Moon rise, this function calculates the date
        of the next Moon rise and puts it on the event queue.
    """
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
        body = bodies[ev.body_name]  # should I make a copy?
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
    """ This thread only runs at startup. It calculates
        rise, transit and set times for the body and puts those
        events on the event queue. It exits once the queue
        is empty.
    """
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
            break

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
        star_list = []
        comet_list = [comets[name] for name in COMETS]
    all_bodies = sun_and_moon + planets + star_list + comet_list
    for body in all_bodies:
        body_queue.put(body)
        bodies[body.name] = body
    bt = threading.Thread(target=body_consumer, name='BodyConsumer')
    bt.start()
    logger.debug('BodyConsumer started')
    bt.join()  # wait for all of them to be added
    threading.Thread(target=event_consumer, name='EventConsumer').start()
    threading.Thread(target=rescheduler, name='Rescheduler').start()
    for name in sorted(bodies.keys()):
        body = bodies[name]
        print(name, type(body), body)


