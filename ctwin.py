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


class HorizonEvents:
    def __init__(self):
        events = []
        observer = ephem.city('Columbus')
        observer.date = ephem.now()
        for body in make_all_bodies():
            body.compute(observer)
            events.append({'name': body.name, 'rise': body.rise_time})
            events.append({'name': body.name, 'set': body.set_time})
        self.events = events


class Event:
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __str__(self):
        return "{0.field} {0.value}".format(self)


class Where:
    def __init__(self, body, observer):
        self.body = body.copy()
        self.observer = observer
        self.events = [
            Event(name, getattr(body, name))
            for name in ('rise_time', 'transit_time', 'set_time')
            ]
        self.events.sort(key=operator.attrgetter('value'))

    def __call__(self, date):
        "We could get stuck here for nearly forever..."
        while date < self.events[0].value:
            ev = self.events[0]
            print("Searching before {}, oldest is {}".format(date, ev))
            if ev.field == 'rise_time':
                when = self.observer.previous_setting(self.body, start=ev.value)
                self.events.insert(0, Event('set_time', when))
            elif ev.field == 'transit_time':
                when = self.observer.previous_rising(self.body, start=ev.value)
                self.events.insert(0, Event('rise_time', when))
            elif ev.field == 'set_time':
                when = self.observer.previous_transit(self.body, start=ev.value)
                self.events.insert(0, Event('transit_time', when))
        while date > self.events[-1].value:
            ev = self.events[-1]
            print("Searching after {}, newest is {}".format(date, ev))
            if ev.field == 'set_time':
                when = self.observer.next_rising(self.body, start=ev.value)
                self.events.append(Event('rise_time', when))
            elif ev.field == 'rise_time':
                when = self.observer.next_transit(self.body, start=ev.value)
                self.events.append(Event('transit_time', when))
            elif ev.field == 'transit_time':
                when = self.observer.next_setting(self.body, start=ev.value)
                self.events.append(Event('set_time', when))
        for a, b in pairwise(self.events):
            if a.value <= date <= b.value:
                print("[{:2d}] {} Before={} After={}".format(
                    len(self.events), date, a, b))
                return (a, b)
        assert False,"Oops"

if __name__ == '__main__':
    o = ephem.city('Columbus')
    s = ephem.Sun()  #Comets()['C/2012 S1 (ISON)']
    s.compute(o)
    where = Where(s, o)
    date = ephem.now()
    for i in range(30):
        where(ephem.Date(date +  i * ephem.hour))





