# -*- coding: utf8
"""
"""
import os
import ephem
import itertools
import collections
import operator
from .sorted_collection import SortedCollection
import json
from . import CITY, astro_path

class SunEvent(collections.namedtuple('SunEvent', 'date event')):
    def display(self):
        return '{:%I:%M %p %a} {}'.format(
            ephem.localtime(self.date), self.event)

Horizon = collections.namedtuple('Horizon', 'name degrees')

twilights = [
    Horizon('Civil Twilight', ephem.degrees('-6')),
    Horizon('Nautical Twilight', ephem.degrees('-12')),
    Horizon('Astronomical Twilight', ephem.degrees('-18'))
    ]
riseset = Horizon('Rise or Set', ephem.degrees('-0:34'))


class EventsCollection:
    source_name = 'sun-rise-set.json'

    def __init__(self):
        self.events = SortedCollection(key=operator.attrgetter('date'))
        path = astro_path(self.source_name)
        if os.path.exists(path):
            with open(path) as f:
                evlist = json.load(f)
                for ev in evlist:
                    self.events.insert(
                        SunEvent(
                            ephem.date(ev['date']), ev['event']))

    def find(self, sun, observer):
        date = observer.date
        retry = 5  # in case we get stuck in a loop
        while retry > 0:
            try:
                return (self.events.find_lt(date),
                        self.events.find_gt(date))
            except ValueError:
                print("Loading events")
                retry -= 1
                for ev in get_sun_events(sun, observer, date):
                    self.events.insert(ev)
                self.write()
        assert False, "Oops"

    def write(self):
        path = astro_path(self.source_name)
        print(self.events[0]._asdict())
        evlist = [ev._asdict() for ev in self.events]
        print("Writing", len(evlist), "events.")
        with open(path, 'w') as f:
            json.dump(evlist, f, indent=2)

def get_sun_events(sun, observer, date):
    observer.pressure = 0
    observer.horizon = riseset.degrees
    for func in (observer.previous_rising, observer.next_rising):
        yield SunEvent(func(sun, start=date), 'Rise')
    for func in (observer.previous_setting, observer.next_setting):
        yield SunEvent(func(sun, start=date), 'Set')
    for twi in twilights:
        observer.horizon = twi.degrees
        for func in (observer.previous_rising, observer.next_rising):
            yield SunEvent(func(sun, start=date),
                'Morning {0.name}'.format(twi))
        for func in (observer.previous_setting, observer.next_setting):
            yield SunEvent(func(sun, start=date),
                'Evening {0.name}'.format(twi))



if __name__ == '__main__':
    observer = ephem.city(CITY)
    sun = ephem.Sun(observer)  # ☼

    events = EventsCollection()
    before, after = events.find(sun, observer)
    print(before.display(), end=' ')
    if sun.alt > 0:
        up_or_down = '⬆' if sun.az <= ephem.degrees('180') else '⬇'
        print('☼ {}°{} {}°⇔ '.format(sun.alt, up_or_down, sun.az), end='')
    elif sun.alt >= ephem.degrees('-6'):
        print('Civil twilight', sun.alt, end='')
    elif sun.alt >= ephem.degrees('-12'):
        print('Nautical twilight', sun.alt, end='')
    elif sun.alt >= ephem.degrees('-18'):
        print('Astronomical twilight', sun.alt, end='')
    else:
        print("It's dark out there. {}° ⇔".format(sun.az))
    print(after.display())

    #print(ephem.now() - events.events[0].date)
