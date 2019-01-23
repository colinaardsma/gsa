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
    'gsa-dev.us-west-2.elasticbeanstalk.com',
]

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

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

# Global Variables
TOKEN_REDIRECT_PATH = "/get_token"
# consumer key
CLIENT_ID = "dj0yJmk9WElwNkFUbG1MVmZJJmQ9WVdrOVduWldOalpKTXpBbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD03Yw--"
# consumer secret
CLIENT_SECRET = "cff931b83bf07509ef93e8ef107eee5cf5412489"
REDIRECT_URI = "http://gsa-dev.us-west-2.elasticbeanstalk.com"

LOGGING_CONFIG = None
