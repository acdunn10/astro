# -*- coding: utf8
"Calculate some miscellaneous upcoming events"
import ephem

if __name__ == '__main__':
    now = ephem.now()
    print("# Dates and Times")
    print("- The current time is", now)
    print("- The local time is", ephem.localtime(now))
    print("- Julian Date:", ephem.julian_date(now))

    print("# Equinoxes & Solstices")
    print("- Previous solstice:", ephem.previous_solstice(now))
    print("- Next solstice:", ephem.next_solstice(now))
    print("- Previous equinox:", ephem.previous_equinox(now))
    print("- Next equinox:", ephem.next_equinox(now))
    print("- Previous Vernal equinox:", ephem.previous_vernal_equinox(now))
    print("- Next Vernal equinox:", ephem.next_vernal_equinox(now))

    sun = ephem.Sun(now)
    moon = ephem.Moon(now)
    print("# Moon")
    print("- Previous new moon:", ephem.previous_new_moon(now))
    print("- Next new moon:", ephem.next_new_moon(now))
    print("- Previous first quarter moon:", ephem.previous_first_quarter_moon(now))
    print("- Next first quarter moon:", ephem.next_first_quarter_moon(now))
    print("- Previous full moon:", ephem.previous_full_moon(now))
    print("- Next full moon:", ephem.next_full_moon(now))
    print("- Previous last quarter moon:", ephem.previous_last_quarter_moon(now))
    print("- Next last quarter moon:", ephem.next_last_quarter_moon(now))
    print("- Sun-Moon separation:", moon.elong)
    print("- Moon phase:", moon.phase)
