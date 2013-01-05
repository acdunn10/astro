# -*- coding: utf8
"""
"""
import os
import ephem
from math import degrees
import itertools
from . import CITY, MILES_PER_AU


observer = ephem.city(CITY)
sun = ephem.Sun(observer)  # ☼

if sun.alt > 0:
    up_or_down = '⬆' if sun.az <= ephem.degrees('180') else '⬇'
    print('☼ {}{} {} ⇔ '.format(sun.alt, up_or_down, sun.az))
elif sun.alt >= ephem.degrees('-6'):
    print('Civil twilight', sun.alt)
elif sun.alt >= ephem.degrees('-12'):
    print('Nautical twilight', sun.alt)
elif sun.alt >= ephem.degrees('-18'):
    print('Astronomical twilight', sun.alt)
else:
    print("It's dark out there", sun.az)



# def sky_position():
#     current = []
#     for symbol, body in SOURCE:
#         if body.alt > 0:
#             az, alt = [degrees(float(i)) for i in (body.az, body.alt)]
#             up_or_down =
#             current.append('{} {:3.0f}°⇔  {:.0f}°{}'.format(
#                 symbol, az, alt, up_or_down))
#     yield '   '.join(current)
#
#
# def calculate(symbol, body):
#     """
#         Calculate the appropriate rising and setting time. We'll
#         calculate tomorrow's time if the body is not currently
#         above the horizon.
#
#         TODO - this does not work right if the time is near the rise
#         or set. Ignoring this for now.
#     """
#     if body.alt > 0:
#         az, alt = [degrees(float(i)) for i in (body.az, body.alt)]
#         rising_method = observer.previous_rising
#         srise = 'Rose'
#     else:
#         rising_method = observer.next_rising
#         srise = 'Rise'
#     fmt = '{} {:%I:%M %p %a} {:.0f}°⇔'
#     rising = ephem.localtime(rising_method(body))
#     r = fmt.format(srise, rising, degrees(float(body.az)))
#     setting = ephem.localtime(observer.next_setting(body))
#     s = fmt.format('Set', setting, degrees(float(body.az)))
#     yield '{}{}   {}{}'.format(symbol, r, symbol, s)
#
#
# def sun_and_moon():
#     "Rise, set and current position of the Sun and Moon"
#     for symbol, body in SOURCE:
#         for line in calculate(symbol, body):
#             yield line
#
#
#
# def main():
#     for line in itertools.chain(sky_position(), sun_and_moon(), moon_info()):
#         print(line)
#
# if __name__ == '__main__':
#     main()
#
