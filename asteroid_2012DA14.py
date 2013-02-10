#!/usr/bin/env python
import ephem
from astro import CITY
from astro.comets import Asteroids
from astro.utils import miles_from_au

asteroids = Asteroids()
ast = asteroids['2012 DA14']
date = ephem.date('2013/2/15 10:00:00')
observer = ephem.city(CITY)
while date < ephem.date('2013/2/15 20:00:00'):
    ast.compute(date)
    miles = miles_from_au(ast.earth_distance)
    observer.date = date
    ast.compute(observer)
    print('{:13,.0f} miles at {}  Azi={} Alt={}'.format(
        miles, date, ast.az, ast.alt))
    date = ephem.date(date + ephem.minute)

