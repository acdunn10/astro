""" Generates a table of the positions of the Sun and Moon
    every 4 minutes for the current year.
    I use this in an application where I don't have access
    to the ephem package and only need the approximate locations

    For example:
        python -m annual.sun_moon_position_table > sun-moon.txt

"""
import ephem
import math

CITY = 'Columbus'
MINUTES = 4

def position_interval(observer, year, interval, *bodies):
    bodies = list(bodies)
    date = ephem.Date(str(year))
    end_date = ephem.Date(str(year+1))
    while date < end_date:
        observer.date = date
        [body.compute(observer) for body in bodies]
        yield (date, bodies)
        date = ephem.Date(date + interval)

def print_position_table():
    observer = ephem.city(CITY)
    year = ephem.now().triple()[0]
    for (date, (sun, moon)) in position_interval(observer, year,
                        MINUTES * ephem.minute, ephem.Sun(), ephem.Moon()):
        # convert from radians to degrees and then round to ints
        fields = map(math.degrees, (sun.az, sun.alt, moon.az, moon.alt))
        fields = map(int, fields)
        print('{},{},{},{}'.format(*fields))
print_position_table()
