# -*- coding: utf8
"""
    sun_and_moon.py will show rise and set for the next day when it gets
    close to rising time. This is some experiments on how best to deal with it.
"""
import ephem
from .sun_and_moon import sun, moon, observer

observer.pressure = 0
observer.horizon = '-0:34'

#body, when = sun, '2012/07/27 10:26:00'
body, when = moon, '2012/07/27 19:45:00'


observer.date = when
for i in range(60):
    body.compute(observer)
    alt = body.alt
    radius = body.radius
    rising = observer.next_rising(body)
    print(observer.date, alt, radius, alt + radius, rising)
    observer.date += ephem.second
