# -*- coding: utf8
import ephem

SYMBOLS = {
    'Sun': '☼',
    'Moon': '☽',
    'Mercury': '☿',
    'Venus': '♀',
    'Earth': '♁',
    'Mars': '♂',
    'Jupiter': '♃',
    'Saturn': '♄',
    'Uranus': '♅',
    'Neptune': '♆',
    '_comet': '☄',
    '_star': '★',
    '_satellite': '✺',
    }


def get_symbol(body):
    "Get the traditional planetary symbols, among others"
    if isinstance(body, (ephem.HyperbolicBody, ephem.ParabolicBody, ephem.EllipticalBody)):
        key = '_comet'
    elif isinstance(body, ephem.FixedBody):
        key = '_star'
    elif isinstance(body, ephem.EarthSatellite):
        key = '_satellite'
    else:
        key = body.name
    return SYMBOLS.get(key, '?')
