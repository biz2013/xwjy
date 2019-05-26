from .base import *

# send email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

STATIC_ROOT = "/var/www/coinexchange/static/"

MEDIA_ROOT = "/Users/taozhang/workspace/xwjy/coinExchange/media/"

ALLOWED_HOSTS = ['52.43.117.129', '172.31.0.229', 'ip-172-31-0-229.us-west-2.compute.internal', 'localhost', '127.0.0.1', '[::1]', '0.0.0.0']

TRADESITE_PAYMENT_URLPREFIX="http://localhost:8000/trading/payment_qrcode_url/"

API_TRANS_LIMIT = 10

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mydb',
        'USER': 'root',
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
            'filename': './coinexchange.log',
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

API_SITE_URL = {
    'stakinguser1' : 'http://localhost:8080/member/getpaymentqrcode.php?out_trade_no={0}'
}