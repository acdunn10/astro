"""
Django settings for djastro project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os
from django.core.exceptions import ImproperlyConfigured


def make_path(*args):
    BASE = os.path.abspath(os.path.dirname(__file__))
    return os.path.normpath(os.path.join(BASE, '..', *args))


def get_env_variable(name):
    "Raise an exception if we can't get the environment variable"
    try:
        return os.environ[name]
    except KeyError:  # This idea came from 'Two Scoops', page 39
        raise ImproperlyConfigured("Set the environment variable '{}'".format(name))


def read_special(filename):
    try:
        with open(os.path.join(get_env_variable('PATH_TO_SPECIAL'), filename)) as f:
            return f.read().strip()
    except:
        raise ImproperlyConfigured("Unable to access '{}'".format(filename))


VENV = get_env_variable('VIRTUAL_ENV')

_VPROJFILENAME = os.path.join(VENV, get_env_variable('VIRTUALENVWRAPPER_PROJECT_FILENAME'))
with open(_VPROJFILENAME) as f:
    PROJECT_FOLDER = f.read().strip()

# Move this out of here once it's generated
SECRET_KEY = 'e#yi(lqcn@nj&u#4tkbis5^oy29&z%o-l(odyxh_^%nt*af8fq'
#SECRET_KEY = read_special('path_to_secret_key')

INTERNAL_IPS = ('127.0.0.1',)
SERVER_EMAIL = read_special('SERVER_EMAIL')
DEFAULT_FROM_EMAIL = SERVER_EMAIL
ADMINS = ((read_special('ADMIN_NAME'), read_special('ADMIN_EMAIL')),)
MANAGERS = ADMINS

EMAIL_SUBJECT_PREFIX = '[djastro]'
EMAIL_HOST = read_special('EMAIL_HOST')
EMAIL_HOST_USER = read_special('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = read_special('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True

SESSION_COOKIE_NAME = 'djastro'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
LOGIN_REDIRECT_URL = '/'

STATIC_URL = '/static/'
STATICFILES_DIRS = (make_path('djastro/static'),)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATIC_ROOT = os.path.join(PROJECT_FOLDER, 'static_root')
BOOTSTRAP = '//netdna.bootstrapcdn.com/bootstrap/3.0.3/'
CRISPY_TEMPLATE_PACK = 'bootstrap3'

MEDIA_ROOT = os.path.join(PROJECT_FOLDER, 'media')
MEDIA_URL = '/media/'


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

# TODO - review this
MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# TODO - TEMPLATE_CONTEXT_PROCESSORS

ROOT_URLCONF = 'djastro.urls'

WSGI_APPLICATION = 'djastro.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_FOLDER, 'djastro.sqlite3'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(PROJECT_FOLDER, 'django_cache'),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = False
USE_L10N = False
USE_TZ = True

TEMPLATE_DIRS = (
    make_path('djastro/templates'),
)
