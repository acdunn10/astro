from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('django_astro.views',
    url(r'^$', 'home', name='astro-home'),
    url(r'^sky/$', 'sky', name='sky'),
    url(r'^angles/$', 'angles', name='angles'),
    url(r'^distance/(?P<body>sun|earth)/(?P<sort>mph|miles)/$',
        'distance', name='distance'),
    url(r'^elongation/$', 'elongation', name='elongation'),
    url(r'^moon/$', 'moon', name='moon'),
    url(r'^horizon/$', 'horizon', name='horizon'),
    url(r'^stars/$', 'print_stars', name='stars'),
    url(r'^cities/$', 'cities', name='cities'),
    url(r'^asteroids/$', 'print_asteroids', name='asteroids'),
    url(r'^comets/$', 'print_comets', name='comets'),
    url(r'^satellites/$', 'print_satellites', name='satellites'),
    url(r'^mercury/$', 'print_mercury', name='mercury'),
    url(r'^separation/$', 'print_separation', name='print-separation'),
)

if settings.DEBUG:
    urlpatterns += patterns('django.contrib.staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
    )
