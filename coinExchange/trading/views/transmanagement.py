#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.http.response import HttpResponseBadRequest
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from tradeex.data.api_const import *
from trading.models import *
from trading.controller import useraccountinfomanager, userpaymentmethodmanager
from trading.controller import ordermanager
from trading.controller.global_constants import *
from trading.controller.global_utils import *
from trading.views.models.returnstatus import ReturnStatus
from trading.views import errorpageview
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.accountinfo")

@login_required
def gettrans(request):
    try:
       useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
       request.session[REQ_KEY_USERACCOUNTINFO] = useraccountInfo.tojson()
       buyorders = None
       keyword = ''
       if request.method == 'POST':
           keyword = request.POST['keyword']
           buyorders = ordermanager.search_orders(keyword, None, None)

       return render(request, 'trading/admin/transmanagement.html', 
              {'useraccountInfo': useraccountInfo,
               REQ_KEY_USERNAME: request.user.username,
               'search_keyword': keyword,
               'buyorders' : buyorders,
               'bootstrap_datepicker': True
              })
    except Exception as e:
       error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def cancel_purchase(request):
    try:
       if request.method == 'POST':
           buyorderid = request.POST['order_id']
           keyword = request.POST['search_keyword']
           purchase_order = Order.objects.get(order_id=buyorderid)
           ordermanager.cancel_purchase_order(purchase_order, 
              TRADE_STATUS_USERABANDON, 
              PAYMENT_STATUS_USERABANDON, request.user)
           useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
           request.session[REQ_KEY_USERACCOUNTINFO] = useraccountInfo.tojson()
           buyorders = ordermanager.search_orders(keyword, None, None)
       else:
           return HttpResponseBadRequest('撤销买单只能允许POST')

       return render(request, 'trading/admin/transmanagement.html', 
              {'useraccountInfo': useraccountInfo,
               REQ_KEY_USERNAME: request.user.username,
               'search_keyword': keyword,
               'buyorders' : buyorders,
               'bootstrap_datepicker': True
              })
    except Exception as e:
       error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
    