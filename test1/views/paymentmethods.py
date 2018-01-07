#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.heepaymanager import HeePayManager
from controller.global_utils import *

# this is for test UI. A fake one
from controller.global_constants import *
from controller import userpaymentmethodmanager
from users.models import *
from views.models.userpaymentmethodview import *
from views.models.orderitem import OrderItem
from views.models.returnstatus import ReturnStatus
from views import errorpage

import logging,json

# logger for user registration
logger = logging.getLogger("site.paymentmethods")

def payment_method(request):
    try:
       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/purchase/'})
       if request.method == 'GET':
           payment_providers = userpaymentmethodmanager.get_payment_providers()
           user_payment_methods = userpaymentmethodmanager.get_user_payment_methods(int(request.session[REQ_KEY_USERID]))
           return render(request, 'html/update_payment_method.html',
              {'user_payment_methods':user_payment_methods,
               'payment_providers': payment_providers})
       else:
           str_val = request.POST['payment_method_id']
           payment_method_id = int(str_val) if len(str_val) > 0 else 0
           payment_provider = request.POST['payment_provider']
           account = request.POST['account']
           record = UserPaymentMethodView(payment_method_id,
                    request.session[REQ_KEY_USERID],
                    payment_provider,
                    '', account, '')
           userpaymentmethodmanager.create_update_user_payment_method(record, request.session[REQ_KEY_USERNAME])
           return redirect('accountinfo')
    except Exception as e:
       error_msg = 'sell_axfund hit exception'
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))