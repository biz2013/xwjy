#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.test_model_manager import ModelManager
from users.models import *
from controller.test_model_manager import ModelManager
from controller.global_constants import *

import logging,json

logger = logging.getLogger(__name__)

def accountinfo(request):
    try:
       if REQ_KEY_USERNAME not in request.session:
          return render(request, 'html/login.html', { 'next_action' : '/accounts/accountinfo/'})
       username = request.session[REQ_KEY_USERNAME]
       manager = ModelManager()
       useraccountInfo = manager.get_user_accountInfo(username)
       return render(request, 'html/myaccount.html', {'useraccountInfo': useraccountInfo})
    except:
       error_msg = 'account info hit exception: {0}'.format(sys.exc_info()[0])
       logger.error(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
