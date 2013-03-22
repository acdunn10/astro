#!/usr/bin/env python3.3
# -*- coding: utf8
import os
import operator
import itertools
import cherrypy
import ephem
import logging_tree
from django.template import loader
from django.conf import settings

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
    )

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)
STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux',
         'Regulus', 'Nunki', 'Alcyone', 'Elnath')
ASTEROIDS = ('3753 Cruithne', )
SATELLITES = ('HST', 'ISS (ZARYA)', 'TIANGONG 1')
SPECIAL_STARS = ('Sirius',)  # I just like this one

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



class Observer:
    default = ephem.city('Columbus')

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
        self.planets = [planet() for planet in PLANETS]
        self.sun = ephem.Sun()
        self.moon = ephem.Moon()
        self.stars = [ephem.star(name) for name in STARS]
        self.special = [ephem.star(name) for name in SPECIAL_STARS]
        self.comets = []
        self.asteroids = []
        self.satellites = []

        self.except_stars = [self.sun, self.moon] + \
                            self.planets + self.comets + \
                            self.asteroids
        self.all_bodies = self.except_stars + self.stars
        self.everything = self.all_bodies + self.special
        self.sky_bodies = self.except_stars + \
            self.satellites + self.special

    @cherrypy.expose
    def index(self):
        now = ephem.now()
        return loader.render_to_string('index.html', {
            'utc_time': now,
            'local_time': ephem.localtime(now),
            })

    @cherrypy.expose
    def sky(self):
        observer = Observer.default
        observer.date = ephem.now()
        body_list = self.sky_bodies
        [body.compute(observer) for body in body_list]
        response = [
            "{} {:>12} {:>12} {}".format(get_symbol(body), _(body.alt),
                _(body.az), body.name)
            for body in sorted(body_list,
                key=operator.attrgetter('alt'), reverse=True)
        ]
        return plain(response)

    @cherrypy.expose
    def elongation(self):
        body_list = self.planets + self.comets + self.asteroids +\
            [self.moon] + self.special
        [body.compute(ephem.now()) for body in body_list]
        response = [
            "{} {:>13} {}".format(
                get_symbol(body), _(body.elong), body.name)
            for body in sorted(body_list, key=operator.attrgetter('elong'))
        ]
        return plain(response)

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

class Root:
    sun = Sun()
    moon = Moon()
    astro = Astro()

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('/astro/')

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
