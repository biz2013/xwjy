from .base import *

# send email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

STATIC_ROOT = "/var/www/coinexchange/static/"

MEDIA_ROOT = "/var/www/coinexchange/media/"

ALLOWED_HOSTS = ['52.43.117.129', '172.31.0.229', 'ip-172-31-0-229.us-west-2.compute.internal', 'localhost', '127.0.0.1', '[::1]']

API_TRANS_LIMIT = 10
