#!/usr/bin/env python3.3
# -*- coding: utf8
import os
import operator
import collections
import itertools
import cherrypy
import ephem
from ephem.stars import stars
import logging_tree
from django.template import loader
from django.conf import settings
import astro
import astro.comets
import astro.satellites
import astro.utils

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

BASEDIR = os.path.abspath(os.path.dirname(__file__))
CLOUD_DRIVE_WWW = os.path.expanduser('~/Box Documents/www/')

settings.configure(  # Django configuring for template use
    TEMPLATE_DIRS=(os.path.join(BASEDIR, 'templates'),),
    TEMPLAGE_DEBUG=True,
    TEMPLATE_STRING_IF_INVALID = "INVALID: %s"
    )

OBSERVER = 'Columbus'
PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)
STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux',
         'Regulus', 'Nunki', 'Alcyone', 'Elnath')
ASTEROIDS = ('3753 Cruithne', )
SATELLITES = ('HST', 'ISS (ZARYA)', 'TIANGONG 1')
SPECIAL_STARS = ('Sirius', 'Vega')
COMETS = (
    'C/2012 S1 (ISON)',
    'C/2011 L4 (PANSTARRS)',
    'C/2013 A1 (Siding Spring)',
    )

DMS = """° ’ ”""".split()
HMS = """h ,m ,s""".split(',')

def format_angle(angle, spec=DMS):
    "Formatting degrees and hours"
    return ''.join(itertools.chain(*zip(str(angle).split(':'), spec)))
_ = format_angle

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


class SolarSystemBody:
    @cherrypy.expose
    def index(self):
        self.body.compute()
        return '{0.name}: RA {0.ra}, Decl {0.dec}'.format(self.body)

    @cherrypy.expose
    def sky(self):
        self.body.compute(Observer.default)
        return '{0.name}: {0.alt}° {0.az}°'.format(self.body)

class Sun(SolarSystemBody):
    body = ephem.Sun()

class Moon(SolarSystemBody):
    body = ephem.Moon()



class Astro:
    def __init__(self):
        comets = astro.comets.Comets()
        asteroids = astro.comets.Asteroids()
        satellites = astro.satellites.EarthSatellites()
        self.body_names = collections.ChainMap(stars, comets, asteroids, satellites)
        self.default_bodies = (ephem.Sun, ephem.Moon, PLANETS,
                               SPECIAL_STARS, ASTEROIDS, SATELLITES,
                               COMETS)
        self.solar_system = (ephem.Sun, ephem.Moon, PLANETS,
                             SPECIAL_STARS, ASTEROIDS, COMETS)

    def compute(self, parameter, *args):
        "parameter is either an Observer or a date"
        for arg in args:
            if isinstance(arg, (list, tuple)):
                yield from self.compute(parameter, *arg)
            else:
                if isinstance(arg, type):
                    body = arg()
                elif isinstance(arg, str):
                    try:
                        body = self.body_names[arg]
                    except KeyError:
                        cherrypy.log("compute doesn't know about {}".format(arg))
                        continue
                body.compute(parameter)
                yield body

    @cherrypy.expose
    def index(self):
        now = ephem.now()
        return loader.render_to_string('home.html', {
            'utc_time': now,
            'local_time': ephem.localtime(now),
            })

    @cherrypy.expose
    def sky(self):
        observer = ephem.city(OBSERVER)
        observer.date = ephem.now()
        bodies = self.compute(observer, *self.default_bodies)
        response = [
            "{} {:>12} {:>12} {}".format(get_symbol(body), _(body.alt),
                _(body.az), body.name)
            for body in sorted(bodies,
                key=operator.attrgetter('alt'), reverse=True)
        ]
        return plain(response)

    @cherrypy.expose
    def elongation(self):
        bodies = self.compute(ephem.now(), self.solar_system)
        response = [
            "{} {:>13} {}".format(
                get_symbol(body), _(body.elong), body.name)
            for body in sorted(bodies, key=operator.attrgetter('elong'))
        ]
        return plain(response)

    @cherrypy.expose
    def angles(self):
        bodies = self.compute(ephem.now(), self.solar_system, STARS)
        angles = (
            Separation(a, b, ephem.separation(a, b))
            for a, b in itertools.combinations(bodies, 2)
            )
        angles = itertools.filterfalse(lambda x:x.is_two_stars(), angles)
        angles = filter(lambda x:x.angle < ephem.degrees('30'), angles)
        return loader.render_to_string('angles.html', {
            'angles': sorted(angles, key=operator.attrgetter('angle')),
            })

    @cherrypy.expose
    def distance(self, **kwargs):
        attr = kwargs.get('p', 'earth_distance')  # or sun_distance
        date = ephem.now()
        bodies = [ephem.Moon, PLANETS, ASTEROIDS, COMETS]
        if attr == 'earth_distance':
            bodies.append(ephem.Sun)
        distances = (
            Distance(date, body, attr)
            for body in self.compute(date, bodies)
            )
        return loader.render_to_string('distance.html', {
            'distances': sorted(distances, key=operator.attrgetter('mph')),
            })

    @cherrypy.expose
    def moon(self):
        date = ephem.now()
        moon = ephem.Moon(date)
        # Young or old Moon (within 72 hours of new)
        age_message = ''
        previous_new = ephem.previous_new_moon(date)
        age = 24 * (date - previous_new)
        if age <= 72:
            age_message = "Young Moon: {:.1f} hours".format(age)
        else:
            next_new = ephem.next_new_moon(date)
            age = 24 * (next_new - date)
            if age <= 72:
                age_message = "Old Moon: {:.1f} hours".format(age)
        response = [age_message]
        response.append("Phase {0.moon_phase:.2%}".format(moon))
        distance = astro.utils.miles_from_au(moon.earth_distance)
        moon.compute(ephem.Date(date + ephem.hour))
        moved = astro.utils.miles_from_au(moon.earth_distance) - distance
        response.append(
            'Earth distance:    {:13,.0f} miles, {:+5.0f} mph'.format(
                distance, moved))
        observer = ephem.city(OBSERVER)
        observer.date = date
        moon.compute(observer)
        m2 = moon.copy()
        distance = astro.utils.miles_from_au(moon.earth_distance)
        observer.date = ephem.Date(date + ephem.hour)
        moon.compute(observer)
        moved = astro.utils.miles_from_au(moon.earth_distance) - distance
        response.append(
            'Observer distance: {:13,.0f} miles, {:+5.0f} mph'.format(
                distance, moved))
        response.append("Azimuth {}".format(_(m2.az)))
        response.append("Altitude {}".format(_(m2.alt)))
        response.append("Declination {}".format(_(m2.dec)))
        return plain(response)

    @cherrypy.expose
    def horizon(self):
        response = [
            format_rise_transit_set(event)
            for event in sorted(self.rst_events, key=operator.itemgetter('date'))
            ]
        return plain(response)

def format_rise_transit_set(dct):
    key = dct['key']
    if dct['body'].name == 'Sun':
        color = 3
    elif isinstance(dct['body'], ephem.EarthSatellite):
        color = 4
    elif key == 'transit':
        color = 1
    elif key == 'setting':
        color = 2
    else:
        color = 0

    return (
        get_symbol(dct['body']),
        "{:%a %I:%M:%S %p}".format(ephem.localtime(dct['date'])),
        "{:^7}".format(key),
        dct['body'].name,
        "{}°".format(dct['azalt']),
        )

    return (
        "{} {:%a %I:%M:%S %p} {:^7} {} {}°".format(
            get_symbol(dct['body']), ephem.localtime(dct['date']), key,
            dct['body'].name, dct['azalt']),
        curses.color_pair(color)
        )


class Distance:
    "Manage info about the distance between two bodies"
    def __init__(self, date, body, attr):
        self.body = body
        self.miles = astro.utils.miles_from_au(getattr(body, attr))
        x = body.copy()
        x.compute(ephem.date(date + ephem.hour))
        moved = astro.utils.miles_from_au(getattr(x, attr)) - self.miles
        self.trend = moved < 0
        self.mph = abs(moved)

    def __str__(self):
        return "{0.mph:8,.0f} mph {0.miles:13,.0f} {1} {0.body.name}".format(
                self, get_symbol(self.body))

    def as_columns(self):
        "makes the table display easier"
        return (
            "{0.mph:8,.0f} mph".format(self),
            "{0.miles:13,.0f} miles".format(self),
            get_symbol(self.body),
            "{0.body.name}".format(self)
            )


class Separation(collections.namedtuple('Separation', 'body1 body2 angle')):
    "Manage info about the angular separation between two bodies"
    def is_two_stars(self):
        return all([isinstance(self.body1, ephem.FixedBody),
                   isinstance(self.body2, ephem.FixedBody)])

    def trend(self):
        "Returns True if the two bodies are getting closer"
        arrows = "UD" #
        a = self.body1.copy()
        b = self.body2.copy()
        later = ephem.now() + ephem.hour
        a.compute(later)
        b.compute(later)
        return ephem.separation(a, b) < self.angle

    def __str__(self):
        "Formatting details for update_angles"
        return "{1:>12}  {2}  {0.body1.name} ⇔ {3} {0.body2.name} ({4})".format(
            self, _(self.angle), get_symbol(self.body1),
            get_symbol(self.body2),
            ephem.constellation(self.body2)[1])

    def as_columns(self):
        return (
            "{:>12}".format(_(self.angle)),
            "{1}  {0.body1.name} ⇔ {2} {0.body2.name}".format(self,
                get_symbol(self.body1), get_symbol(self.body2)),
            "{}".format(ephem.constellation(self.body2)[1]),
            )

def plain(response):
    s = '\n'.join(response) if isinstance(response, list) else response
    return loader.render_to_string('plain.html', {
        'content': s
        })


class StaticFiles:
    pass

cherrypy.tree.mount(
    StaticFiles(),
    '/static/',
    config = {
        '/': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': CLOUD_DRIVE_WWW,
        }
    }
)

def display_star(star):
    star.compute()
    return "{0.mag:+.1f} {0.name:20} {1:>16} {2:>16} {3}".format(star,
        _(star.ra, HMS), _(star.dec), ephem.constellation(star)[1])

class Root:
    sun = Sun()
    moon = Moon()
    astro = Astro()

    @cherrypy.expose
    def index(self):
        return loader.render_to_string('index.html', {})

    @cherrypy.expose
    def stars(self):
        response = [
            display_star(ephem.star(name))
            for name in sorted(stars.keys())
        ]
        return plain(response)

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def config(self):
        return cherrypy.config

    @cherrypy.tools.response_headers(headers=(('Content-Type','text/plain'),))
    @cherrypy.expose
    def logging(self):
        return logging_tree.format.build_description()


cherrypy.config.update({
    'server.socket_host': '0.0.0.0',
    'server.socket_port': 8000,
    })

cherrypy.quickstart(Root())
