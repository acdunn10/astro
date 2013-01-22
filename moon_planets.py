# -*- coding: utf8
import ephem
import collections
import operator
from astro import CITY, PLANETS
from astro.utils import pairwise

def position_interval(year, interval, *bodies):
    bodies = list(bodies)
    date = ephem.Date(str(year))
    end_date = ephem.Date(str(year+1))
    while date < end_date:
        [body.compute(date) for body in bodies]
        yield (date, bodies)
        date = ephem.Date(date + interval)



MoonPlanetSeparation = collections.namedtuple('MoonPlanetSeparation',
    'date moon planet separation')

MoonPlanetDelta = collections.namedtuple('MoonPlanetDelta',
    'date separation delta')

def moon_planet(planet):
    iter = position_interval(2013, ephem.hour, ephem.Moon(), planet)
    for (date, (moon, planet)) in iter:
        yield MoonPlanetSeparation(date, moon, planet, ephem.separation(moon, planet))

def separation(planet):
    for a, b in pairwise(moon_planet(planet)):
        yield MoonPlanetDelta(b.date, b.separation, b.separation - a.separation)

Approach = collections.namedtuple('Approach', 'date separation')

def close_approaches(planet):
    print("Close approaches for", planet.name)
    observer =  ephem.city(CITY)
    for a, b in pairwise(separation(planet)):
        if a.delta < 0 and b.delta > 0:
            observer.date = a.date
            planet.compute(observer)
            print("{:%Y-%m-%d %H:%M:%S} {} Alt={} Az={}".format(ephem.localtime(a.date),
                a.separation, planet.alt, planet.az))

def main():
    for planet in PLANETS:
        close_approaches(planet())
        print(40 * '-')

if __name__ == '__main__':
    main()
