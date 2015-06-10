''' Retrieve the latest two-line elements for satellites that interest us.'''
# TODO: handle retrieve argument.
import argparse
import requests
from skyfield.api import earth, now
from . import home


def retrieve():
    r = requests.get('http://celestrak.com/NORAD/elements/visual.txt')
    r.raise_for_status()
    with open('visual.txt', 'wb') as f:
        f.write(r.content)


def get_satellites():
    satellites = {}
    with open('visual.txt') as f:
        lines = [line.strip() for line in f]
        args = [iter(lines)] * 3
        for name, line1, line2 in zip(*args):
            satellites[name] = earth.satellite('{}\n{}\n{}\n'.format(name, line1, line2))
    return satellites


if __name__ == '__main__':
    for name, sat in get_satellites().items():
        if name.startswith('ISS'):
            position = home(now()).observe(sat).altaz()
            print(position)
            break
