#!/usr/bin/env python
# -*- coding: utf8
"""
    http://spaceflight.nasa.gov/realdata/sightings/cities/view.cgi?
        country=United_States&region=Ohio&city=Columbus
    http://celestrak.com/NORAD/elements/

    Need to keep the station data up-to-date
"""
from __future__ import print_function
import ephem
import defaults

observer = ephem.city(defaults.CITY)
#observer.date = '2012/07/28 06:30:00'

STATION = """ISS (ZARYA)
1 25544U 98067A   12227.22427898  .00009398  00000-0  14372-3 0  1100
2 25544  51.6408 192.4920 0001718  53.6477  53.9616 15.55134406787042
""".strip().split('\n')

PASSES = 20

station = ephem.readtle(*STATION)
station.compute(observer)
print("Now:", station.az, station.alt)
for i in range(PASSES):
    info = observer.next_pass(station)
    print(ephem.localtime(info[2]).replace(microsecond=0), info[3])
    observer.date = info[-2] + ephem.minute
