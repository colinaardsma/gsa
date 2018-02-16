try:
    from .settings_shared import *
except ImportError:
    pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'em0q#e0^ulf%d9%qy+32m9wyj&#_(fn884va^i%ve9(c3x6__#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}


# Global Variables
TOKEN_REDIRECT_PATH = "/get_token"
# consumer key
CLIENT_ID = "dj0yJmk9YWE1SnlhV0lUbndoJmQ9WVdrOU9FUmhUelV6TkdVbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD1lMQ--"
# consumer secret
CLIENT_SECRET = "55d6606ea0bec9a1468d3ea01bbf1c9991dbf93f"
REDIRECT_URI = "http://grays-sports-almanac.appspot.com"
