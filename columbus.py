' Basic data about my location in Columbus, Ohio.'
from skyfield.api import earth
from pytz import timezone

columbus = earth.topos('39.995 N', '83.004 W', elevation_m=250)
eastern = timezone('US/Eastern')
