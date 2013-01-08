# -*- coding: utf8
"""
    Calculate rise, set and location for the major planets.

    If the Sun (or Moon) has not yet risen, it prints the next rise and
    set times. If the body has already risen, it returns the rise time and
    also the next set time.
"""
import ephem
from math import degrees
from . import CITY
from .data import AstroData


PLANETS = (
    ('☿', ephem.Mercury),
    ('♀', ephem.Venus),
    ('♂', ephem.Mars),
    ('♃', ephem.Jupiter),
    ('♄', ephem.Saturn),
    ('♅', ephem.Uranus),
    ('♆', ephem.Neptune),
)

def main():
    date = ephem.now()
    observer = ephem.city(CITY)
    observer.date = date
    planets = []
    for symbol, planet in PLANETS:
        planet = planet(observer)
        obj = AstroData(az=planet.az, alt=planet.alt, mag=planet.mag,
            constellation=ephem.constellation(planet)[1],
            symbol='{} {}'.format(symbol, planet.name))
        obj.calculate_rise_and_set(planet, observer)
        planets.append(obj)

    for obj in planets:
        if obj.alt > 0:
            print(obj.sky_position(magnitude=True))
    for obj in planets:
        print(obj.rise_and_set())

if __name__ == '__main__':
    main()
