import json

with open('sun_position.json') as f:
    sun = json.load(f)

from skyfield.api import now, JulianDate

start = JulianDate(utc=(2015, 1, 1, 5, 0))
jd = now()
print(start, jd)
diff = (jd.utc_datetime() - start.utc_datetime()).total_seconds()
print(diff)
index = int(diff / 60 / 4)
print(index)
print(sun['alt'][index], sun['azi'][index])
