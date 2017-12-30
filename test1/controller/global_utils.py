import pytz
import datetime as dt
import subprocess
import json
import logging

from config import context_processor
from controller.global_constants import *
logger = logging.getLogger(__name__)

def user_session_is_valid(request):
    if (REQ_KEY_USERNAME not in request.session) or (REQ_KEY_USERID not in request.session):
       return False
    if (request.session[REQ_KEY_USERNAME] is None) or (request.session[REQ_KEY_USERID] is None):
       return False
    return True

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
