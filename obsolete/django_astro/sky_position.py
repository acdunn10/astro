import math
from collections import namedtuple
import ephem
import astro.symbols
get_symbol = astro.symbols.get_symbol
import astro.utils
_ = astro.utils.format_angle

class SkyPosition(namedtuple('SkyPosition', 'body')):
    def color(self):
        if self.body.name == 'Sun':
            return 'sun'
        elif isinstance(self.body, ephem.EarthSatellite):
            return 'satellite'
        elif self.body.alt < 0:
            return 'below'
        else:
            if self.body.az < ephem.degrees('180'):
                return 'ascending'
            return 'descending'

    def as_columns(self):
        return (
            get_symbol(self.body),
            '{:>12}'.format(_(self.body.alt)),
            '{:>12}'.format(_(self.body.az)),
            self.body.name,
            self.extra(),
        )

    def extra(self):
        if self.body.name == 'Moon':
            return 'Phase {0.moon_phase:.2%}'.format(self.body)
        elif isinstance(self.body, ephem.EarthSatellite):
            eclipsed = 'eclipsed' if self.body.eclipsed else 'visible'
            return "i{:.0f}° Range {:,.0f} miles, {:,.0f} mph. {}".format(
                math.degrees(self.body._inc), m_to_mi(self.body.range),
                3600 * m_to_mi(self.body.range_velocity), eclipsed)
        elif self.body.name != 'Sun':
            return "Mag. {0.mag:+.1f}".format(self.body)
        else:
            return ''


def m_to_mi(meters):
    return meters / 1609.344
