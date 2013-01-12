# -*- coding: utf8

import ephem
from .comets import Comets

CITY = 'Columbus'  # my default city

def miles_from_au(au):
    return au * ephem.meters_per_au / 1609.344

