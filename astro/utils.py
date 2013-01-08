#!/usr/bin/env python
# -*- coding: utf8
import itertools
import ephem
import collections

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

RiseSet = collections.namedtuple('RiseSet', 'rise rise_az set set_az')

def generate_rise_set(body, observer, start_date=None, ending_date=None):
    """ Generate pairs of rise and set times for a given body
        starting at a given date, defaulting to right now.
    """
    if start_date is None:
        start_date = ephem.now()
    observer.date = start_date
    while True:
        observer.date = observer.next_rising(body)
        rise_time, rise_az = observer.date, body.az
        observer.date = observer.next_setting(body)
        yield RiseSet(rise_time, rise_az, observer.date, body.az)
        if ending_date is not None and observer.date >= ending_date:
            raise StopIteration


DMS = """° ’ ”""".split()
HMS = """h ,m ,s""".split(',')

def format_angle(angle, spec=DMS):
    "Formatting degrees and hours"
    return ''.join(itertools.chain(*zip(str(angle).split(':'), spec)))


if __name__ == '__main__':
    _ = format_angle
    print(_(ephem.degrees('125:38:29')))
    print(_(ephem.hours('5.872'), HMS))

