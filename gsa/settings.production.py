try:
    from .settings_shared import *
except ImportError:
    pass

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'em0q#e0^ulf%d9%qy+32m9wyj&#_(fn884va^i%ve9(c3x6__#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

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
CLIENT_ID = ""
# consumer secret
CLIENT_SECRET = ""
REDIRECT_URI = ""
