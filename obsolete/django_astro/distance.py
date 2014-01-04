import ephem
import astro.utils
import astro.symbols
get_symbol = astro.symbols.get_symbol

class Distance:
    "Manage info about the distance between two bodies"
    def __init__(self, date, body, attr):
        self.body = body
        self.au = getattr(body, attr)
        self.miles = astro.utils.miles_from_au(self.au)
        x = body.copy()
        x.compute(ephem.date(date + ephem.hour))
        moved = astro.utils.miles_from_au(getattr(x, attr)) - self.miles
        self.trend = moved < 0
        self.mph = abs(moved)

    def __str__(self):
        return ' '.join(self.as_columns())

    def as_columns(self):
        "makes the table display easier"
        return (
            "{0.mph:8,.0f}".format(self),
            "{0.au:5.2f}".format(self),
            "{0.miles:13,.0f}".format(self),
            get_symbol(self.body),
            "{0.body.name}".format(self)
        )
