#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, math
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect
from trading.controller.heepaymanager import HeePayManager
from trading.controller.global_utils import *

# this is for test UI. A fake one
from trading.controller.global_constants import *
from trading.controller.axfd_utils import *
from trading.controller.coin_utils import *
from trading.controller import redeemmanager

from django.conf import settings
from trading.models import *
from trading.config import context_processor
from trading.views import errorpageview
from trading.views.models.redeemitem import *
import logging,json, math
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest

# logger for user registration
logger = logging.getLogger("site.redeemview")

@login_required(login_url='/accounts/login/')
def redeem(request):
    try:
       if request.method=='POST':
           userid = request.user.id
           toaddr = request.POST['toaddress']
           amount = float(request.POST['quantity'])
           crypto = request.POST['crypto']
           logger.info('[{0}] redeem request: amount{1} toaddress {2} crypto {3}'.format(
                request.user.username, amount, toaddr, crypto))
           if not redeemmanager.check_send_to_address(crypto, toaddr):
               logger.info('[{0}] redeem request: Failed the address check'.format(request.user.username))
               messages.error(request, "您的提币地址属于交易平台注入地址，请修改您的提币地址")
               return redirect('accountinfo')
           logger.info('[{0}] redeem request: Pass the address check'.format(request.user.username))
           redeem_cmd = RedeemItem(userid, toaddr, amount, crypto)
           axfd_tool = get_coin_utils(crypto)

           redeemmanager.redeem(redeem_cmd,request.user.username, axfd_tool)
           return redirect('accountinfo')
       else:
           return HttpResponseBadRequest('The method can not be GET for redeem')
    except ValueError as ve:
       if ve.args[0].startswith(VE_REDEEM_EXCEED_LIMIT):
           logger.error(ve.args[0])
           messages.error(request,"您的提币数量大于您现有的基金可使用余额，请从新输入提币数量")
           return redirect('accountinfo')
       elif ve.args[0].startswith(VE_ILLEGAL_BALANCE):
           logger.error(ve.args[0])
           messages.error(request,"请检查您的余额是否正确再尝试提币")
           return redirect('accountinfo')    
              
    except Exception as e:
       error_msg = '[{0}] 提币遇到错误: {1}'.format(request.user.username, sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
