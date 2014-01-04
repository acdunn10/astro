# -*- coding: utf8
"""
    When is Mercury next visible?

    Mercury is a bit hard to see because it never gets very far away
    from the Sun. But every now and then it's more easily seen than
    at other times.

    Calculate the altitude of Mercury at sunrise and sunset for
    the next number of days. If the altitude exceeds our minimum,
    then Mercury should be fairly visible.
"""
import ephem
from .utils import generate_rise_set

MINIMUM_ALTITUDE = ephem.degrees('10')
DAYS_AHEAD = 120

def report(observer, mercury, what, when):
    observer.date = when
    mercury.compute(observer)
    if mercury.alt > MINIMUM_ALTITUDE:
        print("{:7} {:%b %d} Alt {}".format(
            what, ephem.localtime(observer.date).date(),
            mercury.alt))

def main(observer):
    mercury = ephem.Mercury()
    sun = ephem.Sun()
    start_date = ephem.now()
    finish_date = ephem.date(start_date + DAYS_AHEAD)
    print("Over the next {} days, mornings and evenings "
          "when Mercury is a minimum of {} degrees "
          "above the horizon at sunrise or sunset".format(
          DAYS_AHEAD, MINIMUM_ALTITUDE))
    for info in generate_rise_set(sun, observer, start_date, finish_date):
        report(observer, mercury, "Morning", info.rise_time)
        report(observer, mercury, "Evening", info.set_time)

def elongation():
    mercury = ephem.Mercury()
    d = ephem.Date('2013/1/17 11:00:00')
    for m in range(120):
        date = ephem.Date(d + m * ephem.hour)
        mercury.compute(date)
        print(date, mercury.elong)

if __name__ == '__main__':
    main(ephem.city('Columbus'))
    #elongation()

