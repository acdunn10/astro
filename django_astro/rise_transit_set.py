import math
import logging
from collections import namedtuple
import ephem
import astro.symbols
get_symbol = astro.symbols.get_symbol
from .body_computer import body_computer
from .configuration import config

logger = logging.getLogger(__name__)

RISE_KINDS = ('next_rising', 'next_setting',
              'next_transit', 'next_antitransit')


class Event(namedtuple('Event', 'body kind date azalt key')):
    header = ('Date', 'Event', 'Body', 'azalt')

    def color(self):
        "The class of the table row"
        if self.body.name == 'Sun':
            return 'sun'
        elif isinstance(self.body, ephem.EarthSatellite):
            return 'satellite'
        elif self.key in ('transit', 'antitransit', 'setting'):
            return self.key
        return 'normal'

    def __str__(self):
        return ' '.join(self.as_columns())

    def as_columns(self):
        return (
            "{:%a %I:%M:%S %p}".format(ephem.localtime(self.date)),
            "{0.key:^7}".format(self),
            "{} {}".format(get_symbol(self.body), self.body.name),
            "{0.azalt}°".format(self),
        )

def rise_transit_set(start_date, *args):
    for body in body_computer.body_generator(args):
        if isinstance(body, ephem.EarthSatellite):
            observer = config.observer
            observer.date = start_date
            kind = 'next_pass'
            method = getattr(observer, kind)
            info = method(body)
            args = zip(*[iter(info)] * 2)
            keys = ('rising', 'transit', 'setting')
            for ((date, azalt), key) in zip(args, keys):
                if date and azalt:
                    yield Event(
                        body=body, kind=kind, date=date, key=key,
                        azalt=int(math.degrees(azalt))
                    )
        else:
            for kind in RISE_KINDS:
                observer = config.observer
                observer.date = start_date
                method = getattr(observer, kind)
                try:
                    date = method(body)
                    azalt = body.alt if 'transit' in kind else body.az
                    key = kind.split('_')[1]
                    yield Event(
                        body=body, kind=kind, date=date, key=key,
                        azalt=int(math.degrees(azalt))
                    )
                except ephem.CircumpolarError as e:
                    logger.info(str(e))


