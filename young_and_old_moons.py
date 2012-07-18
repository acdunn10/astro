#!/usr/bin/env python
# -*- coding: utf8
"""
    A "Young Moon" is a thin crescent Moon seen shortly after the New Moon.
    See my blog post <http://blog.mhsundstrom.com/?p=167> for some more
    information and there are some references from there with more information.
    The "Old Moon" is almost the same, except it's looking for a thin crescent
    Moon just before sunrise instead of just after sunset.

    This program is an exploration of the data behind all of that.
"""
from __future__ import print_function
import ephem

sun = ephem.Sun()
moon = ephem.Moon()

observer = ephem.city('Columbus')

now = ephem.now()
print("The time is", now)
print("The local time is", ephem.localtime(now))

new_moon = ephem.next_new_moon(now)
print("Next New Moon:", ephem.localtime(new_moon))

starting_date = new_moon

for i in range(3):
    print()
    next_setting = observer.next_setting(sun, start=starting_date)
    print("Next sunset:", ephem.localtime(next_setting))

    observer.date = next_setting
    sun.compute(observer)
    print("Sun azimuth at sunset:", sun.az)
    moon.compute(observer)
    print("Moon at sunset:", moon.az, moon.alt, moon.elong, moon.moon_phase)
    age = next_setting - new_moon
    print("Young Moon age:", int(24 * age))
    moonset = observer.next_setting(moon)
    print("Moonset:", ephem.localtime(moonset))

    starting_date = moonset

# Now do the old moon
print('\nOld Moon')
new_moon = ephem.next_new_moon(starting_date)
print("Next New Moon:", ephem.localtime(new_moon))

starting_date = new_moon

for i in range(3):
    print()
    prev_rising = observer.previous_rising(sun, start=starting_date)
    print("Previous sunrise:", ephem.localtime(prev_rising))

    observer.date = prev_rising
    sun.compute(observer)
    print("Sun azimuth at sunrise:", sun.az)
    moon.compute(observer)
    print("Moon at sunrise:", moon.az, moon.alt, moon.elong, moon.moon_phase)
    age = new_moon - prev_rising
    print("Old Moon age:", int(24 * age))

    starting_date = prev_rising
