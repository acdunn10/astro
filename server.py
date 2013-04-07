#!/usr/bin/env python3.3
# -*- coding: utf8
import os
import io
import math
import operator
from collections import namedtuple, ChainMap, OrderedDict
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
        super().__init__(defaults={'observer': 'Columbus'},
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

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)

RISE_KINDS = ('next_rising', 'next_setting',
              'next_transit', 'next_antitransit')



class Astro:
    def __init__(self):
        comets = astro.catalogs.Comets()
        asteroids = astro.catalogs.Asteroids()
        satellites = astro.catalogs.Satellites()
        self.body_names = ChainMap(stars, comets, asteroids, satellites)

    def body_generator(self, *args):
        "individual bodies, e.g., Sun, Moon, or lists, e.g. PLANETS"
        for arg in args:
            if isinstance(arg, (list, tuple)):
                yield from self.body_generator(*arg)
            else:
                if isinstance(arg, type):
                    yield arg()
                elif isinstance(arg, str):
                    try:
                        yield self.body_names[arg]
                    except KeyError:
                        cherrypy.log("compute doesn't know about {}".format(arg))
                        continue

    def compute(self, parameter, *args):
        "parameter is either an Observer or a date"
        for body in self.body_generator(args):
            body.compute(parameter)
            yield body

    def rise_transit_set(self, date, *args):
        observer = config.observer
        observer.date = date
        for body in self.body_generator(args):
            if isinstance(body, ephem.EarthSatellite):
                kind = 'next_pass'
                method = getattr(observer, kind)
                info = method(body)
                args = zip(*[iter(info)] * 2)
                keys = ('rising', 'transit', 'setting')
                for ((date, azalt), key) in zip(args, keys):
                    if date and azalt:
                        yield {
                            'body': body,
                            'kind': kind,
                            'date': date,
                            'azalt': int(math.degrees(azalt)),
                            'key': key,
                            }
            else:
                for kind in RISE_KINDS:
                    method = getattr(observer, kind)
                    try:
                        event_date = method(body)
                        azalt = body.alt if 'transit' in kind else body.az
                        key = kind.split('_')[1]
                        yield {
                            'body': body,
                            'kind': kind,
                            'date': event_date,
                            'azalt': int(math.degrees(azalt)),
                            'key': key,
                            }
                    except ephem.CircumpolarError as e:
                        cherrypy.log(str(e))

    @cherrypy.expose
    def sky(self, **kwargs):
        observer = config.observer
        observer.date = ephem.now()
        bodies = self.compute(observer, ephem.Sun, ephem.Moon,
            PLANETS,
            config.as_list('stars'),
            config.as_list('asteroids'),
            config.as_list('satellites'),
            config.as_list('comets'))
        sort_key = kwargs.get('sort', 'alt')
        sort_reverse = sort_key == 'alt'
        response = [
            format_sky_position(body)
            for body in sorted(
                bodies,
                key=operator.attrgetter(sort_key),
                reverse=sort_reverse)
        ]
        return loader.render_to_string('sky.html', {
            'bodies': response,
            'date': observer.date,
            'local': ephem.localtime(observer.date),
            'refresh_seconds': 6,
            })

    @cherrypy.expose
    def elongation(self):
        bodies = self.compute(ephem.now(), ephem.Moon, PLANETS,
            config.as_list('stars'),
            config.as_list('asteroids'),
            config.as_list('comets'))
        response = [
            "{} {:>13} {}".format(
                get_symbol(body), _(body.elong), body.name)
            for body in sorted(bodies, key=operator.attrgetter('elong'))
        ]
        return plain(response)

    @cherrypy.expose
    def angles(self):
        bodies = self.compute(ephem.now(), ephem.Sun, ephem.Moon,
            PLANETS,
            config.as_list('stars'),
            config.as_list('asteroids'),
            config.as_list('comets'),
            config.as_list('stars', section='separation'))
        angles = (
            Separation(a, b, ephem.separation(a, b))
            for a, b in itertools.combinations(bodies, 2)
            )
        angles = itertools.filterfalse(lambda x:x.is_two_stars(), angles)
        angles = filter(lambda x:x.angle < ephem.degrees('20'), angles)
        return loader.render_to_string('angles.html', {
            'angles': sorted(angles, key=operator.attrgetter('angle')),
            })

    @cherrypy.expose
    def distance(self, **kwargs):
        body = kwargs.get('body', 'earth')
        attr = '{}_distance'.format(body)
        sort_key = kwargs.get('sort', 'mph')

        date = ephem.now()
        bodies = [ephem.Moon, PLANETS,
            config.as_list('asteroids'),
            config.as_list('comets')
        ]
        if attr == 'earth_distance':
            bodies.append(ephem.Sun)
        distances = (
            Distance(date, body, attr)
            for body in self.compute(date, bodies)
            )
        return loader.render_to_string('distance.html', {
            'title': 'Distance from Earth' if body == 'earth' else 'Distance from Sun',
            'distances': sorted(
                distances, key=operator.attrgetter(sort_key)),
            'body': body,
            })

    @cherrypy.expose
    def moon(self):
        f = io.StringIO()
        with astro.utils.redirect_stdout(f):
            astro.moon.main(config.observer)
        return plain(f.getvalue())

    @cherrypy.expose
    def horizon(self):
        date = ephem.now()
        bodies = [ephem.Sun, ephem.Moon, PLANETS,
            config.as_list('stars'),
            config.as_list('asteroids'),
            config.as_list('satellites'),
            config.as_list('comets'),
        ]
        events = list(self.rise_transit_set(date, bodies))
        events.sort(key=operator.itemgetter('date'))
        seconds_to_next_event = int(86400 * (events[0]['date'] - date))
        cherrypy.log("seconds_to_next_event: {}".format(seconds_to_next_event))
        if seconds_to_next_event < 0:
            seconds_to_next_event = 15
        return loader.render_to_string('horizon.html', {
            'events': Table(format_rise_transit_set, events),
            'refresh_seconds': seconds_to_next_event,
            })



def m_to_mi(meters):
    return meters / 1609.344

def format_sky_position(body):
    if body.name == 'Sun':
        color = 'sun'
    elif isinstance(body, ephem.EarthSatellite):
        color = 'satellite'
    elif body.alt < 0:
        color = 'below'
    else:
        color = 'ascending' if body.az < ephem.degrees('180') else 'descending'

    if body.name == 'Moon':
        extra = 'Phase {0.moon_phase:.2%}'.format(body)
    elif isinstance(body, ephem.EarthSatellite):
        eclipsed = 'eclipsed' if body.eclipsed else 'visible'
        extra = "i{:.0f}° Range {:,.0f} miles, {:,.0f} mph. {}".format(
            math.degrees(body._inc), m_to_mi(body.range),
            3600 * m_to_mi(body.range_velocity), eclipsed)
    elif body.name != 'Sun':
        extra = "Mag. {0.mag:+.1f}".format(body)
    else:
        extra = ''

    return (
        color, (
            get_symbol(body),
            '{:>12}'.format(_(body.alt)),
            '{:>12}'.format(_(body.az)),
            body.name,
            extra)
        )

class Table:
    def __init__(self, formatter, iterable):
        self.rows = []
        for event in iterable:
            klass, dct = formatter(event)
            self.rows.append((klass, dct))
        self.header = list(self.rows[0][1].keys())


def format_rise_transit_set(dct):
    key = dct['key']
    if dct['body'].name == 'Sun':
        color = "sun"
    elif isinstance(dct['body'], ephem.EarthSatellite):
        color = "satellite"
    elif key in ('transit', 'antitransit', 'setting'):
        color = key
    else:
        color = "normal"

    return (
        color,  # the class of the table row
        OrderedDict([
            ('date', "{:%a %I:%M:%S %p}".format(ephem.localtime(dct['date']))),
            ('event', "{:^7}".format(key)),
            ('body', "{} {}".format(get_symbol(dct['body']), dct['body'].name)),
            ('azalt', "{}°".format(dct['azalt'])),
        ])
    )


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


class Separation(namedtuple('Separation', 'body1 body2 angle')):
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
    return "{0.mag:+.1f} {0.name:20} {1:>16} {2:>16} {3}".format(
        star,
        _(star.ra, astro.utils.HMS),
        _(star.dec),
        ephem.constellation(star)[1])

def display_city(city):
    latitude, longitude, elevation = ephem_cities[city]
    return "{:20s} {:+6.2f}° {:+7.2f}° {:5.0f}".format(
        city, float(latitude), float(longitude), elevation)

class Root:
    astro = Astro()

    @cherrypy.expose
    def index(self):
        config.load()
        return loader.render_to_string('index.html', {
            'Mercury': '{} Mercury'.format(get_symbol(ephem.Mercury()))
        })

    @cherrypy.expose
    def stars(self):
        response = [
            display_star(ephem.star(name))
            for name in sorted(stars)
        ]
        return plain(response)

    @cherrypy.expose
    def cities(self):
        return plain([
            display_city(city)
            for city in sorted(ephem_cities)
        ])

    @cherrypy.expose
    def asteroids(self):
        return self.display_dict('Asteroids', astro.catalogs.Asteroids())

    @cherrypy.expose
    def comets(self):
        return self.display_dict('Comets', astro.catalogs.Comets())

    @cherrypy.expose
    def satellites(self):
        catalog = astro.catalogs.Satellites()
        return self.display_dict('Satellites', catalog)

    @cherrypy.expose
    def mercury(self):
        f = io.StringIO()
        with astro.utils.redirect_stdout(f):
            astro.mercury.main(config.observer)
        return plain(f.getvalue())

    def display_dict(self, title, catalog):
        response = [str(catalog)] + [
            "#{:5d} {}".format(index, body)
            for index, body in enumerate(sorted(catalog))
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

DEBUG = bool(int(os.environ.get('DEBUG', '1')))

cherrypy.config.update({
    'server.socket_host': '0.0.0.0',
    'server.socket_port': 1025,
    'log.screen': DEBUG,
    'engine.autoreload': DEBUG,
    })

cherrypy.quickstart(Root())
