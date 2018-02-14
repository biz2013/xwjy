import pytz
import datetime as dt
import subprocess
import json
import logging

from trading.controller.global_constants import *
logger = logging.getLogger("site.global_utils")

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
