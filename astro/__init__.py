# -*- coding: utf8

import ephem
from .comets import Comets

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)

CITY = 'Columbus'  # my default city

def miles_from_au(au):
    return au * ephem.meters_per_au / 1609.344

