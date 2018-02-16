try:
    from .settings_shared import *
except ImportError:
    pass


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'em0q#e0^ulf%d9%qy+32m9wyj&#_(fn884va^i%ve9(c3x6__#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '10.211.55.2',
    'mbp',
]


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "colin.aardsma",
        "USER": "colin.aardsma",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    }
}


# Global Variables
TOKEN_REDIRECT_PATH = "/localhost_token"
# consumer key
CLIENT_ID = "dj0yJmk9cEQyTkhmUUt5ekN5JmQ9WVdrOWFtRkdUSHB0Tm1zbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD0yYQ--"
# consumer secret
CLIENT_SECRET = "2fdb054293ed5c071e62048411c9f3f204512bcc"
REDIRECT_URI = "http://grays-sports-almanac.appspot.com"
