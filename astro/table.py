''' Calculate a table with the position of the Sun every 4 minutes throughout the year.
    The Sun will move at most just less than one degree at my standard location, which
    provides plenty of accuracy for my usual applications. Also, this can be used for
    any year, results will be no different at degree accuracy.

    It takes about 88 seconds to generate this file.

    Timing indicates that this isn't really all that fast, somewhat surprisingly.
    To be investigated...
'''
import time
import json
from skyfield.api import sun, JulianDate, now
from . import home, timezone


def generate_tables():
    starting = time.monotonic()
    every_four_minutes = range(0, 365 * 1440, 4)
    # We want to start at midnight local time in Columbus.
    jd = JulianDate(utc=(2015, 1, 1, 5, every_four_minutes))
    altitude, azimuth, distance = home(jd).observe(sun).apparent().altaz()

    # Maybe should do this as a binary file, but loading this is pretty fast.
    data = {
        'alt': list(map(int, altitude._degrees)),
        'azi': list(map(int, azimuth._degrees)),
    }

    with open('data/sun.json', 'wt') as f:
        json.dump(data, f)

    print('Calculation time:', time.monotonic() - starting, 'seconds.')


if __name__ == '__main__':
    import pkgutil

    package_data = pkgutil.get_data(__package__, 'data/sun.json').decode('utf-8')
    data = json.loads(package_data)

    # The table of data for the Sun begins at midnight local time
    # on January 1st and has data for every 4 minutes after that.
    # Since it's in the Eastern time zone, that's 05:00 UTC.
    # I could parameterize this better, and maybe I will someday. Otherwise it's
    # easy to change for someplace else.

    start = JulianDate(utc=(2015, 1, 1, 5, 0))  # TODO This will stop working in 2016!
    jd = now()
    diff = (jd.utc_datetime() - start.utc_datetime()).total_seconds()
    index = int(diff / 60 / 4)
    alt, azi = data['alt'][index], data['azi'][index]

    print('Sun: {now:%A %d %B at %H:%M} {alt:3.0f}° high at {azi:03.0f}°'.format(
        now=jd.utc_datetime().astimezone(timezone), alt=alt, azi=azi))
