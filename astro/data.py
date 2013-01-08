# -*- coding: utf8
import ephem
from math import degrees
from .utils import format_angle as _

class AstroData:
    symbol = '★'
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def sky_position(self, always_show=False, magnitude=True):
        "Depends on symbol, az and alt, also mag and constellation"
        if magnitude and hasattr(self, 'mag'):
            smag = 'Mag. {:.2f}'.format(self.mag)
        else:
            smag = ''
        if hasattr(self, 'constellation'):
            smag = smag + '•' + self.constellation
        if self.alt > 0 or always_show:
            up_or_down = '⬆' if self.az <= ephem.degrees('180') else '⬇'
            return '{} {}{} {}⇔ {}'.format(
                self.symbol, _(self.alt), up_or_down, _(self.az), smag)
        return ''

    def calculate_rise_and_set(self, body, observer):
        observer.pressure = 0
        if isinstance(body, (ephem.Sun, ephem.Moon)):
            observer.horizon = '-0:34'
        else:
            observer.horizon = '0'
        if self.alt > 0:
            self.rise = observer.previous_rising(body)
            self.az_rise = body.az
        else:
            self.rise = observer.next_rising(body)
            self.az_rise = body.az
        self.set = observer.next_setting(body)
        self.az_set = body.az

    def rise_and_set(self):
        "Depends on calculate_rise_and_set having been called"
        s = [self.symbol]
        s.append('Rose' if self.alt > 0 else 'Rise')
        s.append('{:%I:%M %p %a} {:.0f}°⇔'.format(
            ephem.localtime(self.rise), degrees(self.az_rise)))
        s.append('Set {:%I:%M %p %a} {:.0f}°⇔'.format(
            ephem.localtime(self.set), degrees(self.az_set)))
        return ' '.join(s)


class SunData(AstroData):
    symbol = '☼'

    def twilight(self):
        if self.alt >= ephem.degrees('-6'):
            s = 'Civil'
        elif self.alt >= ephem.degrees('-12'):
            s = 'Nautical'
        elif self.alt >= ephem.degrees('-18'):
            s = 'Astronomical'
        return '{} {} Twilight, {}'.format(self.symbol,
            s, _(self.alt))

class MoonData(AstroData):
    symbol = '☽'

    def phase_and_distance(self):
        s = [self.symbol]
        phase_change = "⬆" if self.waxing else "⬇"
        distance_change = "⬆" if self.receding else "⬇"
        s.append('Phase {0.phase:.2f}%{1}'.format(self, phase_change))
        s.append(' {0.earth_distance:,.1f}{1} miles, {0.mph:.1f}mph'.format(
            self, distance_change))
        return ' '.join(s)

    def young_and_old(self):
        if self.age <= 72:
            which = 'young' if self.young else 'old'
            return '{0.symbol} {1} Moon {0.age:.1f} hours'.format(
                self, which)
