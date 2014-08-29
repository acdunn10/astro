from .base import *

DEBUG = True
TEMPLATE_DEBUG = True

# If you run https: then set the following to False for runserver
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Emails will go to the console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Serve the local copy of Bootstrap
BOOTSTRAP = '/Bootstrap/'

# Enable admindocs
INSTALLED_APPS += ['django.contrib.admindocs']

# Enable django-debug-toolbar
INSTALLED_APPS += ['debug_toolbar']
DEBUG_TOOLBAR_PATCH_SETTINGS = False
MIDDLEWARE_CLASSES.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
