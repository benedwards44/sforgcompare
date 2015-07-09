import os
import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '=@w(^&c*piw%@b!&n3ssiqc=e(r-4u31n4emxicb#*5ftwkiwg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEMPLATE_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG

ADMINS = (
    ('Ben Edwards', 'ben@benedwards.co.nz'),
)

POSTMARK_API_KEY     = os.environ.get('POSTMARK_API_KEY')
POSTMARK_SENDER      = 'ben@tquila.com'
POSTMARK_TEST_MODE   = False
POSTMARK_TRACK_OPENS = False

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'compareorgs',
)

MIDDLEWARE_CLASSES = (
    'sslify.middleware.SSLifyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# Add in request context processor
from django.conf import global_settings
TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
)

ROOT_URLCONF = 'sforgcompare.urls'

WSGI_APPLICATION = 'sforgcompare.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
import dj_database_url

DATABASES = {
    'default': dj_database_url.config()
}

# Celery settings
BROKER_POOL_LIMIT = 1

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), "templates"),
)

STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, 'static'),
)

STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

SALESFORCE_CONSUMER_KEY = '3MVG99qusVZJwhsnmdmjq1uHdUla25CKqXcVfJZBNH.S.AfNwV2hKu0opXFQu0gBSs8fBj8otutrcaqjQxCOT'
SALESFORCE_CONSUMER_SECRET = '8518319892876668470'
SALESFORCE_REDIRECT_URI = 'https://sforgcompare.herokuapp.com/oauth_response'
SALESFORCE_API_VERSION = 33

# EMAIL SERVER SETTINGS
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'ben@benedwards.co.nz'
EMAIL_HOST_PASSWORD = '656y58nz'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR + '/debug.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
