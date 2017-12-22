import pytz
import datetime as dt

from controller.global_constants import *

def user_session_is_valid(request):
    if (REQ_KEY_USERNAME not in request.session) or (REQ_KEY_USERID not in request.session):
       return False
    if (request.session[REQ_KEY_USERNAME] is None) or (request.session[REQ_KEY_USERID] is None):
       return False
    return True
