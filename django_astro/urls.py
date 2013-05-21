from django.conf.urls import patterns, include, url

urlpatterns = patterns('django_astro.views',
    url(r'^$', 'home', name='home'),
    url(r'^sky/$', 'sky', name='sky'),
    url(r'^angles/$', 'angles', name='angles'),
    url(r'^sun_distance/$', 'sun_distance', name='sun-distance'),
    url(r'^earth_distance/$', 'earth_distance', name='earth-distance'),
    url(r'^elongation/$', 'elongation', name='elongation'),
    url(r'^moon/$', 'moon', name='moon'),
    url(r'^horizon/$', 'horizon', name='horizon'),
    url(r'^stars/$', 'print_stars', name='stars'),
    url(r'^cities/$', 'print_cities', name='cities'),
    url(r'^asteroids/$', 'print_asteroids', name='asteroids'),
    url(r'^comets/$', 'print_comets', name='comets'),
    url(r'^satellites/$', 'print_satellites', name='satellites'),
    url(r'^mercury/$', 'print_mercury', name='mercury'),
    url(r'^separation/$', 'print_separation', name='print-separation'),
)
