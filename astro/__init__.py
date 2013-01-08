# -*- coding: utf8

import ephem
from math import degrees
from .files import astro_path

CITY = 'Columbus'  # my default city

def miles_from_au(au):
    return au * ephem.meters_per_au / 1609.344

