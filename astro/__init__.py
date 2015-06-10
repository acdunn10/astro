''' This package is about holding and calculating information via `skyfield` from
    my location in Columbus, Ohio.
'''
from skyfield.api import earth
import pytz

home = earth.topos('39.995 N', '83.004 W', elevation_m=250)
timezone = pytz.timezone('US/Eastern')
