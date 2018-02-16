#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect
from trading.controller.heepaymanager import HeePayManager
from trading.controller.global_utils import *

# this is for test UI. A fake one
from trading.controller.global_constants import *
from trading.controller import userpaymentmethodmanager
from trading.models import *
from trading.views.models.userpaymentmethodview import *
from trading.views.models.orderitem import OrderItem
from trading.views.models.returnstatus import ReturnStatus
from trading.views import errorpageview
from django.contrib.auth.decorators import login_required

import logging,json

# logger for user registration
logger = logging.getLogger("site.paymentmethods")

@login_required
def payment_method(request):
    # TO DO: pass down request.user to controller.

    try:
       if request.method == 'GET':
           payment_providers = userpaymentmethodmanager.get_payment_providers()
           user_payment_methods = userpaymentmethodmanager.get_user_payment_methods(request.user.id)
           return render(request, 'trading/update_payment_method.html',
              {'user_payment_methods':user_payment_methods,
               'payment_providers': payment_providers})
       else:
           str_val = request.POST['payment_method_id']
           payment_method_id = int(str_val) if len(str_val) > 0 else 0
           payment_provider = request.POST['payment_provider']
           account = request.POST['account']

           has_error = False
           if len(payment_provider) == 0:
               has_error = True
               messages.error(request, '请选择支付方式')
           elif len(account) == 0:
               has_error = True
               messages.error(request, '请输入您的账号')
           if has_error:
               return redirect('paymentmethods')
           record = UserPaymentMethodView(payment_method_id,
                    request.user.id,
                    payment_provider,
                    '', account, '')
           userpaymentmethodmanager.create_update_user_payment_method(record, request.user.username)
           return redirect('accountinfo')
    except Exception as e:
       error_msg = 'sell_axfund hit exception'
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
