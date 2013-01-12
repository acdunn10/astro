import ephem
from astro import Comets
import operator
from astro.sorted_collection import SortedCollection

PLANETS = (ephem.Mercury, ephem.Venus, ephem.Mars,
           ephem.Jupiter, ephem.Saturn,
           ephem.Uranus, ephem.Neptune)
STARS = ('Spica', 'Antares', 'Aldebaran', 'Pollux', 'Regulus')
COMETS = ('C/2012 S1 (ISON)', 'C/2011 L4 (PANSTARRS)')

def make_comets():
    comets = Comets()
    return [comets[name] for name in COMETS]

def make_all_bodies():
    sun = ephem.Sun()
    moon = ephem.Moon()
    planets = [planet() for planet in PLANETS]
    stars = [ephem.star(name) for name in STARS]
    comets = make_comets()
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
        self.events = SortedCollection(key=operator.attrgetter('value'))
        self.events.insert(Event('rise_time', body.rise_time))
        self.events.insert(Event('transit_time', body.transit_time))
        self.events.insert(Event('set_time', body.set_time))
        print('Where - initial list')
        for ev in self.events:
            print(ev)

    def __call__(self, date):
        "We could get stuck here for nearly forever..."
        while True:
            try:
                before = self.events.find_lt(date)
                break
            except ValueError:
                ev = self.events[0]
                print("Searching before {}, oldest is {}".format(date, ev))
                if ev.field == 'rise_time':
                    when = self.observer.previous_setting(self.body, start=ev.value)
                    self.events.insert(Event('set_time', when))
                elif ev.field == 'transit_time':
                    when = self.observer.previous_rising(self.body, start=ev.value)
                    self.events.insert(Event('rise_time', when))
                elif ev.field == 'set_time':
                    when = self.observer.previous_transit(self.body, start=ev.value)
                    self.events.insert(Event('transit_time', when))

        while True:
            try:
                after = self.events.find_ge(date)
                break
            except ValueError:
                ev = self.events[-1]
                print("Searching after {}, newest is {}".format(date, ev))
                if ev.field == 'set_time':
                    when = self.observer.next_rising(self.body, start=ev.value)
                    self.events.insert(Event('rise_time', when))
                elif ev.field == 'rise_time':
                    when = self.observer.next_transit(self.body, start=ev.value)
                    self.events.insert(Event('transit_time', when))
                elif ev.field == 'transit_time':
                    when = self.observer.next_setting(self.body, start=ev.value)
                    self.events.insert(Event('set_time', when))

        print("[{:2d}] {} Before={} After={}".format(
            len(self.events), date, before, after))


if __name__ == '__main__':
    o = ephem.city('Columbus')
    s = Comets()['C/2012 S1 (ISON)']
    s.compute(o)
    where = Where(s, o)
    date = ephem.now()
    for i in range(30):
        where(ephem.Date(date +  i))





