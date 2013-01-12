import ephem
from astro import Comets
from astro.utils import pairwise
import operator

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)
STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux', 'Regulus')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')


def make_all_bodies():
    sun = ephem.Sun()
    moon = ephem.Moon()
    planets = [planet() for planet in PLANETS]
    stars = [ephem.star(name) for name in STARS]
    comet_dct = Comets()
    comets = [comet_dct[name] for name in COMETS]
    return [sun, moon] + planets + comets + stars


class Event:
    def __init__(self, name, field, date, value):
        self.name = name
        self.field = field
        self.date = date
        self.value = value

    def __str__(self):
        return "{0.name} {0.field} {0.date} {0.value}".format(self)

        self.events = [
            Event(name, getattr(body, name), getattr(body, azalt))
            for name, azalt in (('rise_time', 'rise_az'), ('transit_time', 'transit_alt'), ('set_time', 'set_az'))
            ]
        self.events.sort(key=operator.attrgetter('date'))

FIELDS = ('rise_time', 'transit_time', 'set_time')
AZALT = ('rise_az', 'transit_alt', 'set_az')

# if __name__ == '__main__':
#     o = ephem.city('Columbus')
#     bodies = make_all_bodies()
#     events = []
#     for b in bodies:
#         b.compute(o)
#         for fname, azalt in zip(FIELDS, AZALT):
#             events.append(Event(b.name, fname,
#                 getattr(b, fname), getattr(b, azalt)))
#     events.sort(key=operator.attrgetter('date'))
#     for ev in events:
#         if ev.date >= ephem.now():
#             print(ev)

class Calculate:




def main(w):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    w.timeout(1000)
    calculate = Calculate()

    while True:
        try:
            calculate.update(w)
            curses.curs_set(0)
            w.refresh()
            ch = w.getch()
            if ch != -1:
                break
        except KeyboardInterrupt:
            break

if __name__ == '__main__':
    curses.wrapper(main)


