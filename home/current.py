'''  Where are the Sun, Moon and planets right now?
        python -m home.current
'''
from collections import namedtuple
from operator import attrgetter
from skyfield.api import earth, moon, sun, now, nine_planets
from . import home, timezone

Position = namedtuple('Position', 'name alt azi')

t = now()
print('The current time is', t.astimezone(timezone).strftime('%A %d %B %Y at %H:%M'))


# Generate positions for all the interesting stuff.
def positions(jd):
    for body in (sun, moon) + nine_planets:
        if body != earth:
            alt, azi, _ = home(jd).observe(body).apparent().altaz()
            yield Position(body.jplname.capitalize(), alt._degrees, azi._degrees)

for p in sorted(positions(t), key=attrgetter('azi')):
    if p.alt > 0:
        prefix = '↑' if p.azi <= 180 else '↓'
    else:
        prefix = ' '
    print('{1:2s}{0.name:10s} {0.alt:3.0f}° at {0.azi:03.0f}°'.format(p, prefix))
