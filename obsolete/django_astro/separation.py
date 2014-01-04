from collections import namedtuple
import ephem
import astro.symbols
get_symbol = astro.symbols.get_symbol
import astro.utils
_ = astro.utils.format_angle

class Separation(namedtuple('Separation', 'date body1 body2 angle')):
    "Manage info about the angular separation between two bodies"
    def is_two_stars(self):
        return (
            isinstance(self.body1, ephem.FixedBody) and
            isinstance(self.body1, ephem.FixedBody)
        )

    def trend(self):
        "Returns True if the two bodies are getting closer"
        a = self.body1.copy()
        b = self.body2.copy()
        later = ephem.now() + ephem.hour
        a.compute(later)
        b.compute(later)
        return ephem.separation(a, b) < self.angle

    def __str__(self):
        return ' '.join(self.as_columns())

    def as_columns(self):
        return (
            "{:>12}".format(_(self.angle)),
            "{1} {0.body1.name}".format(self, get_symbol(self.body1)),
            "{1} {0.body2.name}".format(self, get_symbol(self.body2)),
            "{}".format(ephem.constellation(self.body2)[1]),
        )

