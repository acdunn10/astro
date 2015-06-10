'''  Where are the Sun, Moon and planets right now?
        python -m astro
'''
from collections import namedtuple
from operator import attrgetter
from skyfield.api import earth, moon, sun, now, nine_planets, Star
from . import home, timezone
from .symbols import get_symbols

Position = namedtuple('Position', 'name alt azi symbol')

ISS = '''
ISS (ZARYA)
1 25544U 98067A   15161.22302630  .00010597  00000-0  16063-3 0  9993
2 25544  51.6438 118.8019 0004283  31.6406 103.5052 15.55218929946950
'''

STARS = {
    'Sirius': Star(ra_hours=(6, 45, 9.3), dec_degrees=(-16, -42, -47.2)),
    'Vega': Star(ra_hours=(18, 36, 52), dec_degrees=(38, 47)),
}


def current():
    'Current positions of the Sun, Moon, Planets and some other interesting stuff.'
    t = now()
    print('The current time is', t.astimezone(timezone).strftime('%H:%M %Z on %A %d %B %Y'))

    # Generate positions for all the interesting stuff.
    def generate_positions(jd):
        symbols = get_symbols()

        for body in (sun, moon) + nine_planets:
            if body != earth:
                alt, azi, _ = home(jd).observe(body).apparent().altaz()
                name = body.jplname.capitalize()
                yield Position(name, alt._degrees, azi._degrees, symbols.get(name.upper(), ' '))

        # Now the stars
        for name, star in STARS.items():
            alt, azi, _ = home(jd).observe(star).apparent().altaz()
            yield Position(name, alt._degrees, azi._degrees, symbols['BLACK STAR'])

        # Earth satellites are special.
        sat = earth.satellite(ISS)
        alt, azi, _ = home(jd).observe(sat).altaz()
        yield Position('ISS', alt._degrees, azi._degrees, ' ')

    for p in sorted(generate_positions(t), key=attrgetter('azi')):
        if p.alt > 0:
            prefix = '↑' if p.azi <= 180 else '↓'
        else:
            prefix = ' '
        print('{1:2s} {0.symbol} {0.name:10s} {0.alt:3.0f}° at {0.azi:03.0f}°'.format(p, prefix))

if __name__ == '__main__':
    current()
