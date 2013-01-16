import sys
import os
import operator
#import curses
import itertools
import collections
import functools
import logging
import queue
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

FIELDS = ('rise_time', 'transit_time', 'set_time')
AZALT = ('rise_az', 'transit_alt', 'set_az')


# class Calculate:
#     "Manage the display of data in the curses window"
#     def __init__(self):
#         "Load up initial data, including the comets"
#         self.cmd = 'p'
#         self.observer = ephem.city(CITY)
#         self.sun = ephem.Sun()
#         self.moon = ephem.Moon()
#         self.planets = [planet() for planet in PLANETS]
#         self.stars = [ephem.star(name) for name in STARS]
#         comet_dict = Comets()
#         logger.info("Comets last-modified: {}".format(comet_dict.last_modified))
#         self.comets = [comet_dict[name] for name in COMETS]
#         self.except_stars = [self.sun, self.moon] + \
#                             self.planets + self.comets
#         self.all_bodies = self.except_stars + self.stars
#         self.rs = collections.defaultdict(list)
#         self.rs_events = []
#
#     def compute(self):
#         "Compute data for all bodies, not using the Observer"
#         [body.compute(self.date) for body in self.all_bodies]
#         return self
#
#     def compute_observer(self):
#         "Compute with the Observer"
#         [body.compute(self.observer) for body in self.all_bodies]
#         return self
#
#     def calc_rise_set(self, base_date):
#         "Get rise, transit and setting info for the specified date"
#         self.observer.date = ephem.Date(base_date)
#         logger.info("calc_rise_set: {0.observer.date}".format(self))
#         for body in self.except_stars:
#             body.compute(self.observer)
#             for fieldname, azalt in zip(FIELDS, AZALT):
#                 date = getattr(body, fieldname)
#                 if date is None:
#                     continue
#                 self.rs[base_date].append({
#                                'key': fieldname.split('_')[0],
#                                'name': body.name,
#                                'date': ephem.localtime(date),
#                                'azalt': getattr(body, azalt),
#                                'symbol': get_symbol(body)})

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


def rise_set_worker():
    print("rise_set_worker startup")
    bodies = [ephem.Sun(), ephem.Moon()] +\
             [planet() for planet in PLANETS] +\
             [ephem.star(name) for name in stars.keys()]
    print(len(bodies),'bodies')
    observer = ephem.city(CITY)
    for body in bodies:
        body.compute(observer)
        #print(body.name, body.ra, body.rise_time)
    events = queue.PriorityQueue()
    for body in bodies:
        for fieldname, azalt in zip(FIELDS, AZALT):
            date = getattr(body, fieldname)
            azalt = getattr(body, azalt)
            ev = Event(body.name, date, fieldname, azalt)
            events.put(ev)
    while True:
        now = ephem.now()
        print("Queue {:4d} {}".format(events.qsize(), now))
        try:
            ev = events.get()
            if ev.date is None:
                print("Skipping event with no date:", ev)
            elif ev.date < now:
                print("Event has already occurred:", ev)
            else:
                print("Waiting for next event:", ev)
                time_to_go = 86400 * (ev.date - now)
                print("time to go:", time_to_go)
                time.sleep(time_to_go)
                print("done sleeping")
        except queue.Empty:
            break

def main():
    rise_set_worker()

if __name__ == '__main__':
    main()

