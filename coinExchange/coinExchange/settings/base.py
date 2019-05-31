"""
Django settings for coinExchange project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
#BASE_DIR = os.path.join( os.path.dirname(os.path.abspath(__file__)), os.pardir)
currentDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.join(currentDir, os.pardir)
BASE_DIR = os.path.abspath(os.path.join( parentDir, os.pardir))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'a28m%0ualfzm%lj*8fl3xz^l7s#as31u+w#9-ok1@(f=p+b5cw'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tradeex.apps.TradeExchangeConfig',
    'tradeex.apitests',
    'trading.apps.TradingConfig',
    'trading.tests',
    'mathfilters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'coinExchange.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR + '/templates/' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'coinExchange.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mydb',
        'USER': 'mydbuser',
        'PASSWORD': 'aaaaaa',
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

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
#    {
#        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    os.path.join(BASE_DIR, "trading", "static"),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'axfundnoreply@gmail.com'
EMAIL_HOST_PASSWORD = 'CNYFund@019'

#List of the code of supported payment providers for the API
SUPPORTED_API_PAYMENT_PROVIDERS=['heepay', 'weixin', 'alipay','paypal']

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
            'filename': '/var/log/coinexchange/coinexchange.log',
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

# Redirect to home URL after login (Default redirects to /accounts/profile/)
LOGIN_REDIRECT_URL = '/'
HEEPAY_NOTIFY_HOST='www.uuvc.com'
# format for construct the url for heepay return and notify
HEEPAY_NOTIFY_URL_FORMAT='http://{0}:{1}/trading/heepay/confirm_payment/'
HEEPAY_RETURN_URL_FORMAT='https://{0}:{1}/trading/heepay/confirm_payment/'

# These are execution behavior code
TEST_REAL_CALL = False
API_TRANS_LIMIT_IN_CENT = 1000000

PAYMENT_API_STATUS = {
    'weixin' : 'manual',
    'heepay' : 'manual',
    'alipay' : 'manual',
    'paypal' : 'auto'
}
