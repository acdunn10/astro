# -*- coding: utf8
"""
    Just for messing around with stuff I don't understand.

    Astronomical symbols in Unicode

    It might be fun to try displaying some of these symbols
    with output from these programs.

    http://en.wikipedia.org/wiki/Astronomical_symbols
"""
import unicodedata


names = ('DEGREE SIGN', 'BLACK SUN WITH RAYS',
         'WHITE SUN WITH RAYS',
         'FIRST QUARTER MOON', 'LAST QUARTER MOON',
         'BLACK STAR', 'WHITE STAR',
         'SUN', 'MERCURY', 'FEMALE SIGN',
         'EARTH', 'MALE SIGN', 'JUPITER',
         'SATURN', 'URANUS', 'NEPTUNE',
         'PLUTO', 'COMET', 'ASCENDING NODE', 'DESCENDING NODE',
         'CONJUNCTION', 'OPPOSITION', )

if __name__ == '__main__':
    for name in names:
        c = unicodedata.lookup(name)
        print("{} {:6d} {:6X} {}".format(c, ord(c), ord(c), unicodedata.name(c)))
