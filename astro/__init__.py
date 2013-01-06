# -*- coding: utf8

import ephem
from math import degrees

CITY = 'Columbus'  # my default city

from .files import astro_path

def miles_from_au(au):
    return au * ephem.meters_per_au / 1609.344

class AstroData:
    symbol = '★'
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def sky_position(self):
        "Depends on symbol, az and alt"
        if self.alt <= 0:
            return ''
        up_or_down = '⬆' if self.az <= ephem.degrees('180') else '⬇'
        return '{0.symbol} {0.alt}°{1} {0.az}°⇔ '.format(
            self, up_or_down)

    @property
    def rise_and_set(self):
        s = [self.symbol]
        s.append('Rose' if self.alt > 0 else 'Rise')
        s.append('{:%I:%M %p %a} {:.0f}°⇔'.format(
            ephem.localtime(self.rise), degrees(self.az_rise)))
        s.append('Set {:%I:%M %p %a} {:.0f}°⇔'.format(
            ephem.localtime(self.set), degrees(self.az_set)))
        return ' '.join(s)

class SunData(AstroData):
    symbol = '☼'

    @property
    def show_twilight(self):
        if hasattr(self, 'twilight'):
            return '{0.twilight} Twilight, {0.alt}'.format(self)

class MoonData(AstroData):
    symbol = '☽'

    @property
    def phase_and_distance(self):
        s = [self.symbol]
        phase_change = "⬆" if self.waxing else "⬇"
        distance_change = "⬆" if self.receding else "⬇"
        s.append('Phase {0.phase:.2f}%{1}'.format(self, phase_change))
        s.append(' {0.earth_distance:,.1f}{1} miles, {0.mph:.1f}mph'.format(
            self, distance_change))
        return ' '.join(s)

    @property
    def young_and_old(self):
        if self.young:
            return '{0.symbol} Young Moon {0.young:.1f} hours'.format(self)
        elif self.old:
            return '{0.symbol} Old Moon {0.old:.1f} hours'.format(self)
