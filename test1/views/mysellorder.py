#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.test_model_manager import ModelManager
from controller.global_constants import *
from controller import ordermanager

from users.models import *
from views.models.returnstatus import ReturnStatus
from views import errorpage


logger = logging.getLogger(__name__)

def sell_axfund(request):
    #try:
       if REQ_KEY_USERNAME not in request.session:
          return render(request, 'html/login.html', { 'next_action' : '/mysellorder/'})
       username = request.session[REQ_KEY_USERNAME]
       userId = int(request.session[REQ_KEY_USERID])
       #userId = int(request.session['nothing'])
       manager = ModelManager()
       status = None
       if request.method == 'POST':
          units = float(request.POST['quantity'])
          unit_price = float(request.POST['unit_price'])
          unit_price_currency = request.POST['unit_price_currency']
          crypto_currency = request.POST['crypto']
          status = ordermanager.create_sell_order(userId, units, unit_price,
                        unit_price_currency, crypto_currency, username)
       accountinfo = manager.get_user_accountInfo(username)
       sellorders = manager.get_open_sell_orders_by_user(username)
       buyorders = manager.get_pending_incoming_buy_orders_by_user(username)
       return render(request, 'html/mysellorder.html', {'sellorders': sellorders,
                'buyorders':buyorders,'username': username,
                'previous_call_status' : status})

    #except:
       error_msg = 'sell_axfund hit exception: {0}'.format(sys.exc_info()[0])
       logger.error(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
