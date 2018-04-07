try:
    from .settings_shared import *
except ImportError:
    pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'em0q#e0^ulf%d9%qy+32m9wyj&#_(fn884va^i%ve9(c3x6__#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'localhost',
    '198.199.122.80',
]


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "gsa",
        "USER": "gsa_admin",
        "PASSWORD": "",
        "HOST": "localhost",
        "PORT": "",
    }
}


# Global Variables
TOKEN_REDIRECT_PATH = "/get_token"
# consumer key
CLIENT_ID = "dj0yJmk9c2VWeGVNc3BWcW5iJmQ9WVdrOVJWaHhja0o2TmpJbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD04NA--"
# consumer secret
CLIENT_SECRET = "06e294a5200ce05a8be8b7d4c03d0bfb8870c30d"
REDIRECT_URI = "http://198.199.122.80"
