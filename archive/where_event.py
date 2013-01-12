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
    def __init__(self, field, date, value):
        self.field = field
        self.date = date
        self.value = value

    def __str__(self):
        return "{0.field} {0.date}".format(self)


class Where:
    def __init__(self, body, observer):
        self.body = body.copy()
        self.observer = observer
        self.events = [
            Event(name, getattr(body, name), getattr(body, azalt))
            for name, azalt in (('rise_time', 'rise_az'), ('transit_time', 'transit_alt'), ('set_time', 'set_az'))
            ]
        self.events.sort(key=operator.attrgetter('date'))

    earlier = {
        'rise_time': ('setting', 'set', 'set_az'),
        'transit_time': ('rising', 'rise', 'rise_az'),
        'set_time': ('transit', 'transit', 'transit_alt'),
        }

    def insert_earlier_event(self):
        event = self.earlier_or_later(self.events[0],
            self.earlier, 'previous')
        self.events.insert(0, event)

    later = {
        'set_time': ('rising', 'rise', 'rise_az'),
        'rise_time': ('transit', 'transit', 'transit_alt'),
        'transit_time': ('setting', 'set', 'set_az'),
        }

    def append_later_event(self):
        event = self.earlier_or_later(self.events[-1],
            self.later, 'next')
        self.events.append(event)

    def earlier_or_later(self, ev, table, method_prefix):
        method_suffix, name_prefix, azalt = table[ev.field]
        method_name = '{}_{}'.format(method_prefix, method_suffix)
        method = getattr(self.observer, method_name)
        date = method(self.body, start=ev.date)
        field_name = '{}_time'.format(name_prefix)
        value = getattr(self.body, azalt)
        return Event(field_name, date, value)


    def __call__(self, date):
        while date < self.events[0].date:
            self.insert_earlier_event()
        while date > self.events[-1].date:
            self.append_later_event()
        for a, b in pairwise(self.events):
            if a.date <= date <= b.date:
#                 print("[{:2d}] {} Before={} After={}".format(
#                     len(self.events), date, a, b))
                return (a, b)
        assert False,"Oops"

if __name__ == '__main__':
    o = ephem.city('Columbus')
#     s = ephem.Sun()  #Comets()['C/2012 S1 (ISON)']
#     s.compute(o)
#     where = Where(s, o)
#     date = ephem.now()
#     for i in range(30):
#         a, b = where(ephem.Date(date +  i ))
#         print("{0.field} {0.date} {0.value}".format(b))
    bodies = make_all_bodies()
    dct = {}
    for b in bodies:
        b.compute(o)
        #where = Where(b, o)
        #dct[b.name] = where
        print(b.name)




