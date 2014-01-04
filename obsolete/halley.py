""" Comet Halley

    See: <http://mpcapp1.cfa.harvard.edu/cgi-bin/returnprepeph.cgi?d=c&o=0001P>
    The magnitude and angular size fields are fake
"""
import ephem

halley = ephem.readdb("1P/Halley,e,162.1870,59.4137,112.2789,17.870621,0.0130465,0.967813,0,02/16.4380/1986,2000,g 6.5,4.0")

# halley = ephem.EllipticalBody()
# halley._inc = ephem.degrees('162.1870')  # Inclination
# halley._Om = ephem.degrees('59.4137')  # Longitude of ascending node
# halley._om = ephem.degrees('112.2789')  # Argument of perihelion
# halley._a = 17.870621  #  Mean distance from sun
# halley._M = ephem.degrees('0')  # Mean anomaly, set to 0
# halley._epoch_M = ephem.date('1986/02/16.4380')  # Date for measurement
# halley._e = 0.967813  # Eccentricity
# halley._epoch = halley._epoch_M
# # faked the following


date = ephem.date('2013/2/10')
halley.compute(date)
print(halley.ra, halley.dec)
print(halley.elong)
print(halley.sun_distance)


