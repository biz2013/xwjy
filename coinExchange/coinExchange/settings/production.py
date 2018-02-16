from .base import *

DEBUG=False

# https://docs.djangoproject.com/en/2.0/ref/settings/#allowed-hosts
# A list of strings representing the host/domain names that this Django site can serve. This is a security measure to prevent HTTP Host header attacks, 
# which are possible even under many seemingly-safe web server configurations.
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']