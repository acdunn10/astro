import logging
from django import forms
from ephem.cities import _city_data as ephem_cities

logger = logging.getLogger(__name__)

CITY_CHOICES = [
    (city, city)
    for city in sorted(ephem_cities)
]

class CityChooserForm(forms.Form):
    city = forms.ChoiceField(choices=CITY_CHOICES)
