#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.heepaymanager import HeePayManager
from controller.global_utils import *

# this is for test UI. A fake one
from controller.global_constants import *
from controller import redeemmanager

from users.models import *
from views import errorpage
from views.models.redeemitem import *
import logging,json

# logger for user registration
logger = logging.getLogger("site.redeemview")

def redeem(request):
    try:
       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/mysellorder/'})
       if request.method=='POST':
           userid = request.session[REQ_KEY_USERID]
           toaddr = request.POST['toaddress']
           amount = request.POST['quantity']
           crypto = request.POST['crypto']
           redeem_cmd = RedeemItem(userid, toaddr, amount, crypto)
           redeemmanager.redeem(redeem_cmd, request.session[REQ_KEY_USERNAME])
       else:
           return HttpBadRequestResponse('The method can not be GET for redeem')
    except Exception as e:
       error_msg = '提币遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
