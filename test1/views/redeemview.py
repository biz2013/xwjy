#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.heepaymanager import HeePayManager
from controller.global_utils import *

# this is for test UI. A fake one
from controller.global_constants import *
from controller.axfd_utils import *
from controller import redeemmanager

from users.models import *
from views import errorpage
from views.models.redeemitem import *
import logging,json
from django.contrib.auth.decorators import login_required

# logger for user registration
logger = logging.getLogger("site.redeemview")

@login_required(login_url='/accounts/login/')
def redeem(request):
    try:
       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/mysellorder/'})
       if request.method=='POST':
           userid = request.session[REQ_KEY_USERID]
           toaddr = request.POST['toaddress']
           amount = float(request.POST['quantity'])
           crypto = request.POST['crypto']
           sitesettings = context_processor.settings(request)['settings']
           axfd_bin_path = sitesettings.axfd_path
           axfd_datadir = sitesettings.axfd_datadir
           wallet_account_name = sitesettings.axfd_account_name
           axfd_tool = AXFundUtility(axfd_bin_path, axfd_datadir,
                wallet_account_name)
           operation_comment = 'UserId:{0},redeem:{1},to:{2}'.format(
               userid, amount, toaddr)
           txid = axfd_tool.send_fund(toaddr, amount,
                   operation_comment)
           redeem_cmd = RedeemItem(userid, toaddr, amount, crypto)
           redeemmanager.redeem(redeem_cmd, request.session[REQ_KEY_USERNAME])
       else:
           return HttpBadRequestResponse('The method can not be GET for redeem')
    except Exception as e:
       error_msg = '提币遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
