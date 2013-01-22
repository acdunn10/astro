# -*- coding: utf8
import ephem
from astro.utils import generate_rise_set
from astro import CITY
import operator

def main():
    year = ephem.now().triple()[0]
    start_date = ephem.Date(str(year))
    end_date = ephem.Date('{}/12/31'.format(year))
    print(year, start_date, end_date)
    rs = []
    for body in (ephem.Sun(), ephem.Moon()):
        for info in generate_rise_set(body, ephem.city(CITY),
                                      start_date, end_date):
            rs.append(info)
    print(len(rs))
    print("Sun and Moon setting azimuths")
    for i in sorted(rs, key=operator.attrgetter('set_az')):
        print("{0.name:6} {0.set_az} {0.set_time}".format(i))
    print("Sun and Moon rising azimuths")
    for i in sorted(rs, key=operator.attrgetter('rise_az')):
        print("{0.name:6} {0.rise_az} {0.rise_time}".format(i))



if __name__ == '__main__':
    main()
