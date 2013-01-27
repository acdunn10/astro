""" Generates a table of the positions of the Sun and Moon
    every 4 minutes for the current year.
    I use this in an application where I don't have access
    to the ephem package and only need the approximate locations

    For example:
        python -m annual.sun_moon_position_table > sun-moon.txt

    See get_sun_moon.py for an example of using this table
"""
import ephem
import math

def position_interval(observer, year, interval, *bodies):
    bodies = list(bodies)
    date = ephem.Date(str(year))
    end_date = ephem.Date(str(year+1))
    while date < end_date:
        observer.date = date
        [body.compute(observer) for body in bodies]
        yield (date, bodies)
        date = ephem.Date(date + interval)


if __name__ == '__main__':
    observer = ephem.city('Columbus')
    year = ephem.now().triple()[0]
    for (date, (sun, moon)) in position_interval(observer, 2013,
                        4 * ephem.minute, ephem.Sun(), ephem.Moon()):
        # convert from radians to degrees and then round to ints
        fields = map(math.degrees, (sun.az, sun.alt, moon.az, moon.alt))
        fields = map(int, fields)
        print('{},{},{},{}'.format(*fields))
