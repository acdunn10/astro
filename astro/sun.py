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
from . import CITY, astro_path, SunData
import logging
from bisect import bisect_left, bisect_right

logger = logging.getLogger(__name__)

def date_to_minutes(date):
    return int(date * 1440)

class SunEvent(collections.namedtuple('SunEvent', 'date event')):
    """ Remembers a rising, setting or twilight event.
        We need key because at different times, the event time
        calculations can be very slightly different. This is
        because they are calculated by iterating until close enough.
        Our key property rounds to the nearest minute, which is
        plenty close enough.
    """
    @property
    def key(self):
        return date_to_minutes(self.date)

    def __str__(self):
        return '{:%I:%M %p %a} {}'.format(
            ephem.localtime(self.date), self.event)

Horizon = collections.namedtuple('Horizon', 'name degrees')

twilights = [
    Horizon('Civil Twilight', ephem.degrees('-6')),
    Horizon('Nautical Twilight', ephem.degrees('-12')),
    Horizon('Astronomical Twilight', ephem.degrees('-18'))
    ]
riseset = Horizon('Rise or Set', ephem.degrees('-0:34'))


class EventsCollection(SortedCollection):
    source_name = 'sun-rise-set.json'

    def __init__(self, sun, observer, date):
        """ Initialize the collection, possibly from data
            previously saved, then update with the specified date.
        """
        super().__init__(key=operator.attrgetter('key'))
        path = astro_path(self.source_name)
        if os.path.exists(path):
            with open(path) as f:
                evlist = json.load(f)
                for ev in evlist:
                    self.insert(SunEvent(
                            ephem.date(ev['date']),
                            ev['event']))
            logger.debug("Loaded {} events from source".format(len(self)))
        self.update(sun, observer, date)

    def write(self):
        "Save the collection for later use"
        path = astro_path(self.source_name)
        evlist = [ev._asdict() for ev in self]
        with open(path, 'w') as f:
            json.dump(evlist, f, indent=2)
        logger.debug("{} events written".format(len(evlist)))

    def update(self, sun, observer, date):
        "Update with new times as needed"
        need_to_write = False
        for ev in get_sun_events(sun, observer, date):
            try:
                self.find(ev.key)
                pass
            except ValueError:
                self.insert(ev)
                logger.debug("{} insert: {}".format(self._key(ev), ev))
                need_to_write = True
        """ Remove an older event if we have one. There might be
            more than one, but we'll eventually get them all.
        """
        try:
            event = self.find_lt(ephem.date(date - 2))
            self.remove(event)
            need_to_write = True
        except ValueError:
            pass
        if need_to_write:
            self.write()


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


def get_sun_data():
    date = ephem.now()
    observer = ephem.city(CITY)
    observer.date = date
    sun = ephem.Sun(observer)
    obj = SunData(az=sun.az, alt=sun.alt)

    if obj.alt < 0:
        if obj.alt >= ephem.degrees('-6'):
            obj.twilight = 'Civil'
        elif obj.alt >= ephem.degrees('-12'):
            obj.twilight = 'Nautical'
        elif obj.alt >= ephem.degrees('-18'):
            obj.twilight = 'Astronomical'

    # Rise and Set
    observer.pressure = 0
    observer.horizon = '-0:34'
    if obj.alt > 0:
        obj.rise = observer.previous_rising(sun)
        obj.az_rise = sun.az
    else:
        obj.rise = observer.next_rising(sun)
        obj.az_rise = sun.az
    obj.set = observer.next_setting(sun)
    obj.az_set = sun.az

    return obj

#     events = EventsCollection(sun, observer, date)
#     key = date_to_minutes(date)
#     before = events.find_lt(key)
#     after = events.find_ge(key)
#     print(before, end=' ')
#     if alt > 0:
#         up_or_down = '⬆' if az <= ephem.degrees('180') else '⬇'
#         print('☼ {}°{} {}°⇔ '.format(alt, up_or_down, az), end='')
#     elif alt >= ephem.degrees('-6'):
#         print('Civil', alt, end='')
#     elif alt >= ephem.degrees('-12'):
#         print('Nautical', alt, end='')
#     elif alt >= ephem.degrees('-18'):
#         print('Astronomical', alt, end='')
#     else:
#         print("It's dark out there. {}° ⇔".format(az))
#     print(after)

def main():
    obj = get_sun_data()
    print(obj.sky_position)
    print(obj.rise_and_set)
    if obj.show_twilight: print(obj.show_twilight)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, handler=logging.StreamHandler())
    main()

