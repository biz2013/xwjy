from .base import *

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
# send email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += ['testsetup',]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(module)s %(name)s %(process)d %(thread)d %(levelname)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'siteTimeRotateFile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(BASE_DIR, "site_test.log"),
            'when': 'D',
            'interval': 1,
            'backupCount': 30,
            'encoding': None,
            'delay': False,
            'utc': False,
            'formatter': 'verbose'
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        # The catch-all logger for messages in the site hierarchy. loggers for 'site', 'site.registration' all go here.
        'site': {
            'handlers': ['siteTimeRotateFile', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'tradeex': {
            'handlers': ['siteTimeRotateFile', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'tradeapi': {
            'handlers': ['siteTimeRotateFile', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # TODO: add django.server, django.template, django.db.backends and other django framework component logging.
        'django': {
            'handlers': ['console', 'siteTimeRotateFile'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'siteTimeRotateFile'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
