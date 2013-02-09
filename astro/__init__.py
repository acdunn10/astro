# -*- coding: utf8
import os
import ephem

VISIBLE_PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn)

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)

SYMBOLS = {
    'Sun': '☼',
    'Moon': '☽',
    'Mercury': '☿',
    'Venus': '♀',
    'Mars': '♂',
    'Jupiter': '♃',
    'Saturn': '♄',
    'Uranus': '♅',
    'Neptune': '♆',
    '_comet': '☄',
    '_star': '★',
    '_satellite': '✺',
    }

CITY = 'Columbus'  # my default city

STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux',
         'Regulus', 'Nunki', 'Alcyone', 'Elnath')

COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')

def astro_config(name):
    "A folder to store stuff we download"
    path = os.path.expanduser('~/.astro')
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(path, name)

