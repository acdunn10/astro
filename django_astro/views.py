import itertools
import operator
import io
from django.shortcuts import render
from django.http import HttpResponse
import ephem
import ephem.stars
from ephem.cities import _city_data as ephem_cities
import astro.utils
import astro.moon
import astro.mercury
import astro.symbols
get_symbol = astro.symbols.get_symbol
import astro.utils
_ = astro.utils.format_angle
from .configuration import config
from .body_computer import body_computer
from .sky_position import SkyPosition
from .separation import Separation
from .distance import Distance
from .rise_transit_set import rise_transit_set, Event

PLANETS = ('Mercury', 'Venus', 'Mars',
           'Jupiter', 'Saturn',
           'Uranus', 'Neptune')

def home(request):
    return render(request, 'astro/home.html', {})

def sky(request):
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
        sort_key = request.GET.get('sort', 'alt')
        sort_reverse = sort_key == 'alt'
        positions.sort(
            key=lambda x: getattr(x.body, sort_key),
            reverse=sort_reverse)
        return render(request, 'astro/sky.html', {
            'observer': observer,
            'positions': positions,
            'date': observer.date,
            'local': ephem.localtime(observer.date),
            'refresh_seconds': 6,
        })


def angles(request):
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
    return render(request, 'astro/angles.html', {
        'angles': sorted(angles, key=operator.attrgetter('angle')),
    })


def sun_distance(request):
    return distance(request, body='earth')


def earth_distance(request):
    return distance(request, body='sun')

def distance(request, body, sort):
    attr = '{}_distance'.format(body)
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
    return render(request, 'astro/distance.html', {
        'title': 'Distance from {}'.format(body.capitalize()),
        'distances': sorted(
            distances, key=operator.attrgetter(sort)),
        'body': body,
    })

def plain_response(func, *args, **kwargs):
    "TODO explain this better"
    def decorator(*args, **kwargs):
        f = io.StringIO()
        with astro.utils.redirect_stdout(f):
            func(*args, **kwargs)
        return render(args[0], 'astro/plain.html', {
            'content': f.getvalue(),
        })
    return decorator


@plain_response
def elongation(request):
    bodies = body_computer(
        ephem.now(),
        'Moon', PLANETS,
        config.as_list('stars'),
        config.as_list('asteroids'),
        config.as_list('comets'))
    for body in sorted(bodies, key=operator.attrgetter('elong')):
        print("{} {:>13} {}".format(
            get_symbol(body), _(body.elong), body.name))


@plain_response
def moon(request):
    astro.moon.main(config.observer)


def horizon(request):
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
    seconds_to_next_event = 1 + max(
        int(86400 * (events[0].date - date)),
        15)
    return render(request, 'astro/horizon.html', {
        'header': Event.header,
        'events': events,
        'refresh_seconds': seconds_to_next_event,
        'observer': config.observer,
    })


@plain_response
def print_mercury(request):
    astro.mercury.main(config.observer)

@plain_response
def print_separation(request):
    body1 = request.GET.get('body1')
    body2 = request.GET.get('body2')
    print("Separation between", body1, "and", body2)

    def generate_separations(body1, body2):
        date = ephem.now()
        body1, body2 = list(body_computer(date, body1, body2))
        while True:
            yield Separation(
                date, body1, body2, ephem.separation(body1, body2))
            date = ephem.Date(date + ephem.hour)
            body1.compute(date)
            body2.compute(date)
    angles = generate_separations(body1, body2)
    for a, b in astro.utils.pairwise(angles):
        if a.angle < b.angle:
            print('Closest approach:', a.date, a.angle)
            break

@plain_response
def print_stars(request):
    for name in sorted(ephem.stars.stars):
        star = ephem.star(name)
        star.compute()
        print(
            "{0.mag:+.1f} {0.name:20} {1:>16} {2:>16} {3}".format(
                star,
                _(star.ra, astro.utils.HMS),
                _(star.dec),
                ephem.constellation(star)[1]))


@plain_response
def print_cities(request):
    for city in sorted(ephem_cities):
        latitude, longitude, elevation = ephem_cities[city]
        print("{:20s} {:+6.2f}° {:+7.2f}° {:5.0f}".format(
            city, float(latitude), float(longitude), elevation))


@plain_response
def print_asteroids(request):
    print_catalog('Asteroids', astro.catalogs.Asteroids())


@plain_response
def print_comets(request):
    print_catalog('Comets', astro.catalogs.Comets())


@plain_response
def print_satellites(request):
    print_catalog('Satellites', astro.catalogs.Satellites())


def print_catalog(title, catalog):
    print("Catalog '{}': {}".format(title, catalog))
    for index, body in enumerate(sorted(catalog), start=1):
        print('#{:5,d} {}'.format(index, body))

