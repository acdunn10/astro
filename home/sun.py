import json
import pkgutil
from skyfield.api import now, JulianDate
from . import timezone

package_data = pkgutil.get_data(__package__, 'data/sun.json').decode('utf-8')
sun = json.loads(package_data)

# See generate_tables.py: The table of data for the Sun begins at midnight local time
# on January 1st and has data for every 4 minutes after that.
# Since it's in the Eastern time zone, that's 05:00 UTC.
# I could parameterize this better, and maybe I will someday. Otherwise it's
# easy to change for someplace else.

start = JulianDate(utc=(2015, 1, 1, 5, 0))  # TODO This will stop working in 2016!
jd = now()
diff = (jd.utc_datetime() - start.utc_datetime()).total_seconds()
index = int(diff / 60 / 4)
alt, azi = sun['alt'][index], sun['azi'][index]

print('Sun: {now:%A %d %B at %H:%M} {alt:3.0f}° high at {azi:03.0f}°'.format(
    now=jd.utc_datetime().astimezone(timezone), alt=alt, azi=azi))
