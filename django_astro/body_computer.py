import logging
from collections import namedtuple, ChainMap
import ephem
from ephem.stars import stars
import astro
import astro.catalogs


logger = logging.getLogger(__name__)


class BodyComputer:
    def __init__(self):
        solar_system = {
            'Sun': ephem.Sun(),
            'Moon': ephem.Moon(),
            'Mercury': ephem.Mercury(),
            'Venus': ephem.Venus(),
            'Mars': ephem.Mars(),
            'Jupiter': ephem.Jupiter(),
            'Saturn': ephem.Saturn(),
            'Uranus': ephem.Uranus(),
            'Neptune': ephem.Neptune(),
        }
        comets = astro.catalogs.Comets()
        asteroids = astro.catalogs.Asteroids()
        satellites = astro.catalogs.Satellites()
        self.body_names = ChainMap(
            solar_system, stars, comets, asteroids, satellites)

    def __call__(self, parameter, *args):
        "parameter is either an Observer or a date"
        for body in self.body_generator(args):
            body.compute(parameter)
            yield body

    def body_generator(self, *args):
        "individual bodies, e.g., Sun, Moon, or lists, e.g. PLANETS"
        for arg in args:
            if isinstance(arg, (list, tuple)):
                yield from self.body_generator(*arg)
            else:
                if isinstance(arg, str):
                    try:
                        yield self.body_names[arg]
                    except KeyError:
                        logger.error(
                            "compute doesn't know about {}".format(arg))
                        continue

body_computer = BodyComputer()

