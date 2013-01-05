# -*- coding: utf8
"""
"""
import os
import ephem
import itertools
import collections
import operator
from sorted_collection import SortedCollection
import json
from . import CITY, astro_path

class SunEvent(collections.namedtuple('SunEvent', 'date event')):
    def __str__(self):
        #return '{0.date} {0.event}'.format(self)
        return '{:%Y-%m-%d %H:%M:%S} {}'.format(ephem.localtime(self.date), self.event)

Horizon = collections.namedtuple('Horizon', 'name degrees')

twilights = [
    Horizon('Civil Twilight', ephem.degrees('-6')),
    Horizon('Nautical Twilight', ephem.degrees('-12')),
    Horizon('Astronomical Twilight', ephem.degrees('-18'))
    ]
riseset = Horizon('Rise or Set', ephem.degrees('-0:34'))

def make_all_sun_events(sun, observer, date):
    noon = int(date)
    dates = [ephem.date(i) for i in (noon-1, noon, noon+1)]
    events = SortedCollection(key=operator.attrgetter('date'))
    observer.pressure = 0
    for date in dates:
        observer.horizon = riseset.degrees
        for func in (observer.previous_rising, observer.next_rising):
            events.insert(SunEvent(func(sun, start=date), 'Rise'))
        for func in (observer.previous_setting, observer.next_setting):
            events.insert(SunEvent(func(sun, start=date), 'Set'))
        for twi in twilights:
            observer.horizon = twi.degrees
            for func in (observer.previous_rising, observer.next_rising):
                events.insert(SunEvent(func(sun, start=date), 'Morning {0.name}'.format(twi)))
            for func in (observer.previous_setting, observer.next_setting):
                events.insert(SunEvent(func(sun, start=date), 'Evening {0.name}'.format(twi)))
    return events

def make_sun_events(sun, observer, date):
    events = SortedCollection(key=operator.attrgetter('date'))
    observer.pressure = 0
    observer.horizon = riseset.degrees
    for func in (observer.previous_rising, observer.next_rising):
        events.insert(SunEvent(func(sun, start=date), 'Rise'))
    for func in (observer.previous_setting, observer.next_setting):
        events.insert(SunEvent(func(sun, start=date), 'Set'))
    for twi in twilights:
        observer.horizon = twi.degrees
        for func in (observer.previous_rising, observer.next_rising):
            events.insert(SunEvent(func(sun, start=date), 'Morning {0.name}'.format(twi)))
        for func in (observer.previous_setting, observer.next_setting):
            events.insert(SunEvent(func(sun, start=date), 'Evening {0.name}'.format(twi)))
    return events




if __name__ == '__main__':
    observer = ephem.city(CITY)
    sun = ephem.Sun(observer)  # ☼

    if sun.alt > 0:
        up_or_down = '⬆' if sun.az <= ephem.degrees('180') else '⬇'
        print('☼ {}{} {} ⇔ '.format(sun.alt, up_or_down, sun.az))
    elif sun.alt >= ephem.degrees('-6'):
        print('Civil twilight', sun.alt)
    elif sun.alt >= ephem.degrees('-12'):
        print('Nautical twilight', sun.alt)
    elif sun.alt >= ephem.degrees('-18'):
        print('Astronomical twilight', sun.alt)
    else:
        print("It's dark out there. {}° ⇔".format(sun.az))

    events = make_sun_events(sun, observer, observer.date)
    for ev in events:
        print(ev)
    print(10 * '-')
    print(events.find_lt(observer.date))
    print(events.find_gt(observer.date))
