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
    'grays-sports-almanac.us-west-2.elasticbeanstalk.com',    #TODO: move this to environments
    'gsa-dev.us-west-2.elasticbeanstalk.com/',
]


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

# TODO: move this into environments
if 'RDS_DB_NAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
else:
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
TOKEN_REDIRECT_PATH = "/localhost_token"
# consumer key
CLIENT_ID = "dj0yJmk9cEQyTkhmUUt5ekN5JmQ9WVdrOWFtRkdUSHB0Tm1zbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD0yYQ--"
# consumer secret
CLIENT_SECRET = "2fdb054293ed5c071e62048411c9f3f204512bcc"
REDIRECT_URI = "http://grays-sports-almanac.appspot.com"
