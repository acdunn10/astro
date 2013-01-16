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

def rise_set_worker():
    print("rise_set_worker startup")
    initial_bodies = [ephem.Sun(), ephem.Moon()] +\
             [planet() for planet in PLANETS] +\
             [ephem.star(name) for name in stars.keys()]
    observer = ephem.city(CITY)
    [body.compute(observer) for body in initial_bodies]
    bodies = {body.name: body for body in initial_bodies}
    events = []
    for body in bodies.values():
        for fieldname, azalt in zip(FIELDS, AZALT):
            date = getattr(body, fieldname)
            azalt = getattr(body, azalt)
            heapq.heappush(events, Event(body.name, date, fieldname, azalt))
    while True:
        now = ephem.now()
        print("Queue {:4d} {}".format(len(events), now))
        try:
            ev = heapq.heappop(events)
            if ev.date is None:
                print("Skipping event with no date:", ev)
            elif ev.date < now:
                print("Event has already occurred:", ev)
                reschedule_event(ev, events, bodies, observer)
            else:
                print("Waiting for next event:", ev)
                time_to_go = 86400 * (ev.date - now)
                print("time to go:", time_to_go)
                time.sleep(time_to_go)
                print("done sleeping")
        except IndexError:
            break

def main():
    rise_set_worker()

if __name__ == '__main__':
    main()

