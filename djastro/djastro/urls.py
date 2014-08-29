from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'djastro.views.home', name='home'),

    # Choose something less obvious for production
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += patterns(
        '',

        (r'^admin/doc/', include('django.contrib.admindocs.urls')),

        url(r'^__debug__/', include(debug_toolbar.urls)),

        # In case you need to serve media files
        url(r'^media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),

        # Bootstrap 3.0.3
        url(r'^Bootstrap/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': 'path/to/bootstrap/bootstrap-3.0.3/dist'}),

    )

