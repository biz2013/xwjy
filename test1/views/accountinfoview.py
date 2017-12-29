#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from config import context_processor
from controller.global_utils import *
from users.models import *
from controller import useraccountinfomanager
from controller.global_constants import *
from controller.global_utils import *
from views.models.returnstatus import ReturnStatus
from views import errorpage

import logging,json

logger = logging.getLogger(__name__)

def update_account_with_receiving_fund(request):
    try:
       client_ip = get_client_ip(request)
       if client_ip != '127.0.0.1':
          message = 'update_account_with_receiving_fund() only accept request from localhost. The client ip is {0}'.format(client_ip)
          loggger.error(message)
          print message
          return HttpResponseForbidden()
       sitesettings = context_processor.settings(request)['settings']
       useraccountinfomanager.update_account_balance_with_wallet_trx(crypto,
            wallet_account_name, lookback_count, min_trx_confirmation):
       return HttpResponse('OK')
    except:
       error_msg = 'update_account_with_receiving_fund hit exception: {0}'.format(sys.exc_info()[0])
       logger.error(error_msg)
       return HttpResponseServerError(error_msg)
