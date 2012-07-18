#!/usr/bin/env python
# -*- coding: utf8
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
