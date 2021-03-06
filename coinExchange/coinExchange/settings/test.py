from .base import *

ALLOWED_HOSTS = ['54.203.195.52', 'localhost', '127.0.0.1']
# send email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += ['testsetup',]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mydb',
        'USER': 'tradeAdmin',
        'PASSWORD': 'AXFund@017',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'TEST':{
           'CHARSET': 'UTF8',
           },
      'OPTIONS': {
        'init_command': 'SET default_storage_engine=INNODB',
      }
    }
}

TRADESITE_PAYMENT_URLPREFIX="http://localhost:8000/trading/payment_qrcode_url/"

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
