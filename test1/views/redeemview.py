#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, math
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
import logging,json, math
from django.contrib.auth.decorators import login_required

# logger for user registration
logger = logging.getLogger("site.redeemview")

@login_required(login_url='/accounts/login/')
def redeem(request):
    try:
       if not request.user.is_authenticated():
          return render(request, 'login.html', { 'next' : '/accounts/accountinfo/'})
       if request.method=='POST':
           userid = request.user.id
           toaddr = request.POST['toaddress']
           amount = float(request.POST['quantity'])
           crypto = request.POST['crypto']
           sitesettings = context_processor.settings(request)['settings']
           axfd_bin_path = sitesettings.axfd_path
           axfd_datadir = sitesettings.axfd_datadir
           axfd_passphrase = sitesettings.axfd_passphrase
           wallet_account_name = sitesettings.axfd_account_name
           axfd_account = sitesettings.axfd_account_name
           lookback_count = sitesettings.axfd_list_trans_count
           axfd_tool = AXFundUtility(axfd_bin_path, axfd_datadir,
                wallet_account_name)
           axfd_tool.unlock_wallet(axfd_passphrase, 15)
           operation_comment = 'UserId:{0},redeem:{1},to:{2}'.format(
               userid, amount, toaddr)
           trx = axfd_tool.send_fund(axfd_account, toaddr, amount,
                   operation_comment,lookback_count)
           redeem_cmd = RedeemItem(userid, toaddr, amount, crypto)
           redeemmanager.redeem(redeem_cmd,request.user.username,
              trx['txid'], math.fabs(trx['fee']),
              operation_comment)
           return redirect('accountinfo')
       else:
           return HttpBadRequestResponse('The method can not be GET for redeem')
    except Exception as e:
       error_msg = '提币遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
