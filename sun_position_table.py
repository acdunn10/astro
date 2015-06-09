''' Calculate a table with the position of the Sun every 4 minutes throughout the year.
    The Sun will move at most just less than one degree at my standard location, which
    provides plenty of accuracy for my usual applications. Also, this can be used for
    any year, results will be no different at degree accuracy.
'''
import time
from skyfield.api import earth, sun, JulianDate
from pytz import timezone

columbus = earth.topos('39.995 N', '83.004 W')
eastern = timezone('US/Eastern')

starting = time.monotonic()
every_four_minutes = range(0, 365 * 1440, 4)
# We want to start at midnight local time in Columbus.
jd = JulianDate(utc=(2015, 1, 1, 5, every_four_minutes))
altitude, azimuth, distance = columbus(jd).observe(sun).apparent().altaz()

# Maybe should do this as a binary file, but loading this is pretty fast.
sun = {
    'alt': list(map(int, altitude._degrees)),
    'azi': list(map(int, azimuth._degrees)),
}
import json
with open('sun_position.json', 'wt') as f:
    json.dump(sun, f)

print(time.monotonic() - starting)
