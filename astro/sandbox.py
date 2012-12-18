#!/usr/bin/env python
# -*- coding: utf8
from __future__ import print_function
"""
    Just for messing around with stuff I don't understand.
"""
import unicodedata

"""
    Astronomical symbols in Unicode

    It might be fun to try displaying some of these symbols
    with output from these programs.

    http://en.wikipedia.org/wiki/Astronomical_symbols
"""


names = ('DEGREE SIGN', 'BLACK SUN WITH RAYS',
         'WHITE SUN WITH RAYS',
         'FIRST QUARTER MOON', 'LAST QUARTER MOON',
         'BLACK STAR', 'WHITE STAR',
         'SUN', 'MERCURY', 'FEMALE SIGN',
         'EARTH', 'MALE SIGN', 'JUPITER',
         'SATURN', 'URANUS', 'NEPTUNE', 'NEPTUNE',
         'PLUTO', 'COMET', 'ASCENDING NODE', 'DESCENDING NODE',
         'CONJUNCTION', 'OPPOSITION', )

for name in names:
    c = unicodedata.lookup(name)
    print(c, unicodedata.name(c), 'repr=', repr(c), 'ord=', ord(c))

# Symbols from the Wikipedia page referenced above
values = (9737, 9789)

for value in values:
    c = unichr(value)
    print(c, value, 'repr=', repr(c), 'ord=', ord(c))
