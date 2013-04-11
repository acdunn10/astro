#!/usr/bin/env python3.3
# -*- coding: utf8
import os
import io
import math
import operator
from collections import namedtuple, ChainMap
import itertools
import configparser
import cherrypy
import ephem
from ephem.stars import stars
from ephem.cities import _city_data as ephem_cities
import logging_tree
from django.template import loader
from django.conf import settings
import astro
import astro.symbols
get_symbol = astro.symbols.get_symbol
import astro.catalogs
import astro.utils
_ = astro.utils.format_angle
import astro.mercury
import astro.moon

BASEDIR = os.path.abspath(os.path.dirname(__file__))
CLOUD_DRIVE_WWW = os.path.expanduser('~/Box Documents/www/')

settings.configure(  # Django configuring for template use
    TEMPLATE_DIRS=(os.path.join(BASEDIR, 'templates'),),
    TEMPLAGE_DEBUG=True,
    TEMPLATE_STRING_IF_INVALID = "INVALID: %s"
)


class AstroConfig(configparser.ConfigParser):
    def __init__(self):
        super().__init__(
            defaults={'observer': 'Columbus'},
            allow_no_value=True)
        self.load()

    def load(self):
        self.read(os.path.expanduser('~/.astro/config.ini'))

    def as_list(self, option, section=None):
        if section is None:
            section = 'DEFAULT'
        items = self[section][option].split('\n')
        items = [i for i in items if i]
        return [i.split('#')[0].strip() for i in items]

    @property
    def observer(self):  # shortcut for common usage
        return ephem.city(self['DEFAULT']['observer'])

config = AstroConfig()


PLANETS = ('Mercury', 'Venus', 'Mars',
                'Jupiter', 'Saturn',
                'Uranus', 'Neptune')

RISE_KINDS = ('next_rising', 'next_setting',
              'next_transit', 'next_antitransit')


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
                        cherrypy.log(
                            "compute doesn't know about {}".format(arg))
                        continue

body_computer = BodyComputer()


class Event(namedtuple('Event', 'body kind date azalt key')):
    header = ('Date', 'Event', 'Body', 'azalt')

    def color(self):
        "The class of the table row"
        if self.body.name == 'Sun':
            return 'sun'
        elif isinstance(self.body, ephem.EarthSatellite):
            return 'satellite'
        elif self.key in ('transit', 'antitransit', 'setting'):
            return self.key
        return 'normal'

    def __str__(self):
        return ' '.join(self.as_columns())

    def as_columns(self):
        return (
            "{:%a %I:%M:%S %p}".format(ephem.localtime(self.date)),
            "{0.key:^7}".format(self),
            "{} {}".format(get_symbol(self.body), self.body.name),
            "{0.azalt}°".format(self),
        )


def rise_transit_set(start_date, *args):
    for body in body_computer.body_generator(args):
        if isinstance(body, ephem.EarthSatellite):
            observer = config.observer
            observer.date = start_date
            kind = 'next_pass'
            method = getattr(observer, kind)
            info = method(body)
            args = zip(*[iter(info)] * 2)
            keys = ('rising', 'transit', 'setting')
            for ((date, azalt), key) in zip(args, keys):
                if date and azalt:
                    yield Event(
                        body=body, kind=kind, date=date, key=key,
                        azalt=int(math.degrees(azalt))
                    )
        else:
            for kind in RISE_KINDS:
                observer = config.observer
                observer.date = start_date
                method = getattr(observer, kind)
                try:
                    date = method(body)
                    azalt = body.alt if 'transit' in kind else body.az
                    key = kind.split('_')[1]
                    yield Event(
                        body=body, kind=kind, date=date, key=key,
                        azalt=int(math.degrees(azalt))
                    )
                except ephem.CircumpolarError as e:
                    cherrypy.log(str(e))


class Astro:
    def __init__(self):
        pass

    @cherrypy.expose
    def sky(self, **kwargs):
        observer = config.observer
        observer.date = ephem.now()
        positions = [
            SkyPosition(body)
            for body in body_computer(
                observer, 'Sun', 'Moon', PLANETS,
                config.as_list('stars'),
                config.as_list('asteroids'),
                config.as_list('satellites'),
                config.as_list('comets')
            )
        ]
        sort_key = kwargs.get('sort', 'alt')
        sort_reverse = sort_key == 'alt'
        positions.sort(
            key=lambda x: getattr(x.body, sort_key),
            reverse=sort_reverse)
        return loader.render_to_string('sky.html', {
            'positions': positions,
            'date': observer.date,
            'local': ephem.localtime(observer.date),
            'refresh_seconds': 6,
        })

    @cherrypy.expose
    def elongation(self):
        return print_elongation()

    @cherrypy.expose
    def separation(self, body1, body2):
        return print_separation(body1, body2)

    @cherrypy.expose
    def angles(self):
        date = ephem.now()
        bodies = body_computer(
            date, 'Sun', 'Moon', PLANETS,
            config.as_list('stars'),
            config.as_list('asteroids'),
            config.as_list('comets'),
            config.as_list('stars', section='separation'))
        angles = (
            Separation(date, a, b, ephem.separation(a, b))
            for a, b in itertools.combinations(bodies, 2)
        )
        angles = itertools.filterfalse(lambda x: x.is_two_stars(), angles)
        angles = filter(lambda x: x.angle < ephem.degrees('20'), angles)
        return loader.render_to_string('angles.html', {
            'angles': sorted(angles, key=operator.attrgetter('angle')),
        })

    @cherrypy.expose
    def distance(self, **kwargs):
        body = kwargs.get('body', 'earth')
        attr = '{}_distance'.format(body)
        sort_key = kwargs.get('sort', 'mph')

        date = ephem.now()
        bodies = [
            PLANETS, 'Moon',
            config.as_list('asteroids'),
            config.as_list('comets')
        ]
        if attr == 'earth_distance':
            bodies.append('Sun')
        distances = (
            Distance(date, body, attr)
            for body in body_computer(date, bodies)
        )
        return loader.render_to_string('distance.html', {
            'title': 'Distance from {}'.format(body.capitalize()),
            'distances': sorted(
                distances, key=operator.attrgetter(sort_key)),
            'body': body,
        })

    @cherrypy.expose
    def moon(self):
        return print_moon()

    @cherrypy.expose
    def horizon(self):
        """ Rise, transit and set and satellite passes"""
        date = ephem.now()
        bodies = [
            'Sun', 'Moon', PLANETS,
            config.as_list('stars'),
            config.as_list('asteroids'),
            config.as_list('satellites'),
            config.as_list('comets'),
        ]
        events = list(rise_transit_set(date, bodies))
        events.sort(key=operator.attrgetter('date'))
        seconds_to_next_event = max(
            int(86400 * (events[0].date - date)),
            15)
        cherrypy.log("seconds_to_next_event: {}".format(seconds_to_next_event))
        return loader.render_to_string('horizon.html', {
            'header': Event.header,
            'events': events,
            'refresh_seconds': seconds_to_next_event,
        })


def m_to_mi(meters):
    return meters / 1609.344


class SkyPosition(namedtuple('SkyPosition', 'body')):
    def color(self):
        if self.body.name == 'Sun':
            return 'sun'
        elif isinstance(self.body, ephem.EarthSatellite):
            return 'satellite'
        elif self.body.alt < 0:
            return 'below'
        else:
            if self.body.az < ephem.degrees('180'):
                return 'ascending'
            return 'descending'

    def as_columns(self):
        return (
            get_symbol(self.body),
            '{:>12}'.format(_(self.body.alt)),
            '{:>12}'.format(_(self.body.az)),
            self.body.name,
            self.extra(),
        )

    def extra(self):
        if self.body.name == 'Moon':
            return 'Phase {0.moon_phase:.2%}'.format(self.body)
        elif isinstance(self.body, ephem.EarthSatellite):
            eclipsed = 'eclipsed' if self.body.eclipsed else 'visible'
            return "i{:.0f}° Range {:,.0f} miles, {:,.0f} mph. {}".format(
                math.degrees(self.body._inc), m_to_mi(self.body.range),
                3600 * m_to_mi(self.body.range_velocity), eclipsed)
        elif self.body.name != 'Sun':
            return "Mag. {0.mag:+.1f}".format(self.body)
        else:
            return ''


class Distance:
    "Manage info about the distance between two bodies"
    def __init__(self, date, body, attr):
        self.body = body
        self.au = getattr(body, attr)
        self.miles = astro.utils.miles_from_au(self.au)
        x = body.copy()
        x.compute(ephem.date(date + ephem.hour))
        moved = astro.utils.miles_from_au(getattr(x, attr)) - self.miles
        self.trend = moved < 0
        self.mph = abs(moved)

    def __str__(self):
        return ' '.join(self.as_columns())

    def as_columns(self):
        "makes the table display easier"
        return (
            "{0.mph:8,.0f}".format(self),
            "{0.au:5.2f}".format(self),
            "{0.miles:13,.0f}".format(self),
            get_symbol(self.body),
            "{0.body.name}".format(self)
        )


class Separation(namedtuple('Separation', 'date body1 body2 angle')):
    "Manage info about the angular separation between two bodies"
    def is_two_stars(self):
        return (
            isinstance(self.body1, ephem.FixedBody) and
            isinstance(self.body1, ephem.FixedBody)
        )

    def trend(self):
        "Returns True if the two bodies are getting closer"
        a = self.body1.copy()
        b = self.body2.copy()
        later = ephem.now() + ephem.hour
        a.compute(later)
        b.compute(later)
        return ephem.separation(a, b) < self.angle

    def __str__(self):
        return ' '.join(self.as_columns())

    def as_columns(self):
        return (
            "{:>12}".format(_(self.angle)),
            "{1} {0.body1.name}".format(self, get_symbol(self.body1)),
            "{1} {0.body2.name}".format(self, get_symbol(self.body2)),
            "{}".format(ephem.constellation(self.body2)[1]),
        )


class StaticFiles:
    pass

cherrypy.tree.mount(
    StaticFiles(),
    '/static/',
    config={
        '/': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': CLOUD_DRIVE_WWW,
        }
    }
)


def plain_text(func, *args, **kwargs):
    """ Decorator for a function which prints to stdout. We
        redirect the output to a string and then return it
        as a text/plain response.
    """
    def decorator(*args, **kwargs):
        f = io.StringIO()
        with astro.utils.redirect_stdout(f):
            func(*args, **kwargs)
        return plain(f.getvalue())
    return decorator


def plain(response):
    s = '\n'.join(response) if isinstance(response, list) else response
    return loader.render_to_string('plain.html', {
        'content': s
    })


@plain_text
def print_catalog(title, catalog):
    print("Catalog '{}': {}".format(title, catalog))
    for index, body in enumerate(sorted(catalog), start=1):
        print('#{:5,d} {}'.format(index, body))


@plain_text
def print_loaded_comets():
    print("Loaded comets")
    efields = ('_inc', '_Om',  '_om', '_a', '_e', '_M', '_epoch_M', '_epoch')
    for body in body_computer(ephem.now(), config.as_list('comets')):
        print(body.name)
        print(body)
        print(body.writedb())
        if isinstance(body, ephem.EllipticalBody):
            print(dir(body))
            for name in efields:
                print('{} = "{}"'.format(name, getattr(body, name)))
            P = math.sqrt(body._a * body._a * body._a)
            print('Orbital period:', P)
            p = body._Om + body._om
            print('Longitude of perihelion', p)
            n = 0.9856076686 / P
            print('Mean daily motion', n)
            T = ephem.Date(body._epoch_M - body._M / n)
            print('Epoch of perihelion', T)
            q = body._a * (1 - body._e)
            print('Perihelion distance', q)
        print(20 * '-')


@plain_text
def print_separation(body1, body2):
    print("Separation between", body1, "and", body2)
    def generate_separations(body1, body2):
        date = ephem.now()
        body1, body2 = list(body_computer(date, body1, body2))
        while True:
            sep = Separation(date, body1, body2, ephem.separation(body1, body2))
            yield sep
            date = ephem.Date(date + ephem.hour)
            body1.compute(date)
            body2.compute(date)
    angles = generate_separations(body1, body2)
    for a, b in astro.utils.pairwise(angles):
        if a.angle < b.angle:
            print('Closest approach:', a.date, a.angle)
            break



@plain_text
def print_mercury():
    astro.mercury.main(config.observer)


@plain_text
def print_moon():
    astro.moon.main(config.observer)


@plain_text
def print_elongation():
    bodies = body_computer(
        ephem.now(),
        'Moon', PLANETS,
        config.as_list('stars'),
        config.as_list('asteroids'),
        config.as_list('comets'))
    for body in sorted(bodies, key=operator.attrgetter('elong')):
        print("{} {:>13} {}".format(
            get_symbol(body), _(body.elong), body.name))


@plain_text
def print_stars():
    for name in sorted(stars):
        star = ephem.star(name)
        star.compute()
        print(
            "{0.mag:+.1f} {0.name:20} {1:>16} {2:>16} {3}".format(
                star,
                _(star.ra, astro.utils.HMS),
                _(star.dec),
                ephem.constellation(star)[1]))


@plain_text
def print_cities():
    for city in sorted(ephem_cities):
        latitude, longitude, elevation = ephem_cities[city]
        print("{:20s} {:+6.2f}° {:+7.2f}° {:5.0f}".format(
            city, float(latitude), float(longitude), elevation))


class Root:
    astro = Astro()

    @cherrypy.expose
    def index(self):
        config.load()
        return loader.render_to_string('index.html', {
        })

    @cherrypy.expose
    def stars(self):
        return print_stars()

    @cherrypy.expose
    def cities(self):
        return print_cities()

    @cherrypy.expose
    def asteroids(self):
        return print_catalog('Asteroids', astro.catalogs.Asteroids())

    @cherrypy.expose
    def comets(self):
        return print_catalog('Comets', astro.catalogs.Comets())

    @cherrypy.expose
    def db(self):
        return print_loaded_comets()

    @cherrypy.expose
    def satellites(self):
        catalog = astro.catalogs.Satellites()
        return print_catalog('Satellites', catalog)

    @cherrypy.expose
    def mercury(self):
        return print_mercury()

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def config(self):
        return cherrypy.config

    @cherrypy.tools.response_headers(headers=(('Content-Type', 'text/plain'),))
    @cherrypy.expose
    def logging(self):
        return logging_tree.format.build_description()

DEBUG = bool(int(os.environ.get('DEBUG', '1')))

cherrypy.config.update({
    'server.socket_host': '0.0.0.0',
    'server.socket_port': 1025,
    'log.screen': DEBUG,
    'engine.autoreload': DEBUG,
})

cherrypy.quickstart(Root())
