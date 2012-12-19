# -*- coding: utf8
"Calculate some miscellaneous upcoming events"
import ephem

if __name__ == '__main__':
    now = ephem.now()
    print("The time is", now)
    print("The local time is", ephem.localtime(now))
    print("Julian Date:", ephem.julian_date(now))

    print("Next solstice:", ephem.next_solstice(now))
    print("Next equinox:", ephem.next_equinox(now))

    sun = ephem.Sun(now)
    moon = ephem.Moon(now)
    print("Sun-Moon separation:", moon.elong)
    print("Moon phase:", moon.phase)
    print("Next New Moon:", ephem.next_new_moon(now))
    print("Next Full Moon:", ephem.next_full_moon(now))
