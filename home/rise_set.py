import json
import datetime
import pkgutil
from collections import namedtuple
from skyfield.api import now, JulianDate
from . import timezone

Position = namedtuple('Position', 'date alt azi')

package_data = pkgutil.get_data(__package__, 'data/sun.json').decode('utf-8')
sun = json.loads(package_data)


def every_four_minutes(date):
    while True:
        yield date
        date += datetime.timedelta(minutes=4)


def gen():
    start = JulianDate(utc=(2015, 1, 1, 5, 0))  # TODO This will stop working in 2016!
    date = start.utc_datetime()
    for date, alt, azi in zip(every_four_minutes(date), sun['alt'], sun['azi']):
        yield Position(date.astimezone(timezone), alt, azi)


def sign(x):
    return x > 0


position = iter(gen())
current = next(position).alt
for pos in position:
    if sign(pos.alt) != sign(current):
        which = 'Rise' if pos.alt > 0 else 'Set '
        print('{1} {0.date:%d %B %H:%M}'.format(pos, which))
        current = pos.alt

