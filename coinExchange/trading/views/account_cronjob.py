#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.http import HttpResponse, HttpResponseServerError,HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

# this is for test UI. A fake one
from trading.config import context_processor
from trading.controller.axfd_utils import *
from trading.models import *
from trading.controller import useraccountinfomanager
from trading.controller.global_constants import *
from trading.controller.global_utils import *
from trading.views.models.returnstatus import ReturnStatus
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger('site.account_cronjob')

@csrf_exempt
def update_account_with_receiving_fund(request):
    try:
       client_ip = get_client_ip(request)
       if client_ip != '127.0.0.1':
          message = 'update_account_with_receiving_fund() only accept request from localhost. The client ip is {0}'.format(client_ip)
          logger.error(message)
          return HttpResponseForbidden()
       sitesettings = context_processor.settings(request)['settings']
       min_trx_confirmation = sitesettings.min_trx_confirmation
       axfd_tool = AXFundUtility(sitesettings)
       # get all past 10000 transactions in wallet
       trans = axfd_tool.listtransactions()

       logger.info("update_account_with_receiving_fund(): query axfund transactions and update user wallet...")

       useraccountinfomanager.update_account_balance_with_wallet_trx(
            'AXFund', trans, min_trx_confirmation)
       return HttpResponse('OK')
    except Exception as e:
       error_msg = 'update_account_with_receiving_fund hit exception: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return HttpResponseServerError(error_msg)
