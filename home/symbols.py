# -*- coding: utf8
"""
    Astronomical symbols in Unicode

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


def get_symbols():
    symbols = {name: unicodedata.lookup(name) for name in names}
    symbols['MOON'] = symbols['FIRST QUARTER MOON']
    symbols['MARS'] = symbols['MALE SIGN']
    symbols['VENUS'] = symbols['FEMALE SIGN']
    return symbols


if __name__ == '__main__':
    for name in names:
        c = unicodedata.lookup(name)
        print("{} {:6d} {:6X} {}".format(c, ord(c), ord(c), unicodedata.name(c)))
        assert unicodedata.name(c) == name
