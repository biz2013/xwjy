from .base import *

ALLOWED_HOSTS = ['54.218.104.21', 'localhost', '127.0.0.1']
# send email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

STATIC_ROOT = "/var/www/coinexchange/static/"

MEDIA_ROOT = "/var/www/coinexchange/media/"

ALLOWED_HOSTS = ['54.203.195.52', 'ip-172-31-0-229.us-west-2.compute.internal', 'localhost', '127.0.0.1', '[::1]']
