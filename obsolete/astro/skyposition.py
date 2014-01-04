import ephem
import operator
import math
from .symbols import get_symbol
from .utils import format_angle as _

class SkyPosition(list):
    def __init__(self, location, bodies):
        super().__init__(bodies)
        self.location = location

    def calculate(self):
        observer = ephem.Observer()
        observer.lat = str(self.location.lat)
        observer.lon = str(self.location.lon)
        observer.date = ephem.now()
        for body in self:
            body.compute(observer)

    def __str__(self):
        s = []
        above_horizon = True
        for body in sorted(self, key=operator.attrgetter('alt'), reverse=True):
            if above_horizon and body.alt < 0:
                s.append(10 * '-')
                above_horizon = False
            s.append(format_sky_position(body))
        return '\n'.join(s)

def format_sky_position(body):
    "Formatting details for update_position"
    symbol = get_symbol(body)
    if body.name == 'Moon':
        extra = "Phase {0.moon_phase:.2%}".format(body)
    elif isinstance(body, ephem.EarthSatellite):
        extra = "i{1:.0f}° {2:,.0f} {3:,.0f} {0}".format(
            not body.eclipsed, math.degrees(body._inc), m_to_mi(body.range),
            m_to_mi(body.range_velocity))
    elif body.name != 'Sun':
        extra = "{0.mag:+.1f}".format(body)
    else:
        extra = ''
    return "{} {:>12} {:>12} {} {}".format(get_symbol(body), _(body.alt),
            _(body.az), body.name, extra)
