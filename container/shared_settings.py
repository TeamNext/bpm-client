# Django settings for container project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'bpm',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '3306',                      # Set to empty string for default.
        'TEST_COLLATION': 'utf8_general_ci'
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

import os
PROJECT_ROOT = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'static'),
)
# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'jen0qt9%a!(d@#-^fx@3byjjalt5ty&78^xg@r&eli^8zwzdl0'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'container.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'container.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bpm.kernel',
    'bpm.logging',
    'bpm.webservice',
    'bpm.scheduler',
    'bpm_client',
    'bpm.contrib.auth',
    'bpm.contrib.hub',
    'bpm.contrib.butler',
    'south',
    'guardian',
    'django.contrib.admin',
    'djsupervisor',
    'django_rq',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)
DEBUG=True
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
        },
    },
    'formatters': {
        'simple': {
            'format': '%(process)d %(levelname)s %(message)s \n'
        },
        'bare': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'simple',
            'filename': os.path.join(PROJECT_ROOT, 'bpm.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5
        },
        'sandbox': {
            'class': 'bpm.logging.BpmLogHandler',
            'formatter': 'bare'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        '__sandbox__': {
            'handlers': ['sandbox'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'bpm': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'bpm.kernel.jobs': {
            'handlers': ['console', 'file', 'sandbox'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'bpm.kernel.executor': {
            'handlers': ['console', 'file', 'sandbox'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'bpm.kernel.sandbox': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'rq': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'bpm.kernel.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

USE_TZ=True
RUN_MODE = 'DEVELOP'    # DEVELOP TEST PRODUCT
WSGI_ENV = os.environ.get("DJANGO_SETTINGS_MODULE", "")
if WSGI_ENV.endswith("production"):
    RUN_MODE = "PRODUCT"
elif WSGI_ENV.endswith("testing"):
    RUN_MODE = "TEST"
else:
    RUN_MODE = "DEVELOP"
if RUN_MODE=='DEVELOP':
    REPO_TYPE = 'hg'
else:
    REPO_TYPE='hg'
REPO_ROOT=os.path.join(PROJECT_ROOT, 'repo')
RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'PASSWORD': '',
    },
    'task-events': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 1,
        'PASSWORD': '',
    }
}
PASSPORT_SERVICE_SIGNIN_URL = 'http://passport.oa.com/modules/passport/signin.ashx'
PASSPORT_SERVICE_SIGNOUT_URL = 'http://passport.oa.com/modules/passport/signout.ashx'
PASSPORT_SERVICE_WSDL = 'http://passport.oa.com/services/passportservice.asmx?WSDL'
AUTHENTICATION_BACKENDS = ('bpm.contrib.auth.backends.TicketBackend',)
ANONYMOUS_USER_ID = -1
BPM_JOB_WORKER = 'bpm.workers.qos.QoSBackend'
QOS_URL = 'http://127.0.0.1:10086/'