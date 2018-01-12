#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.global_constants import *
from controller.global_utils import *
from controller import ordermanager
from controller import useraccountinfomanager

from views.models.orderitem import OrderItem
from views.models.returnstatus import ReturnStatus
from views import errorpage
from django.contrib.auth.decorators import login_required


logger = logging.getLogger("site.sellorder")

@login_required
def sell_axfund(request):
    try:
       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/mysellorder/'})
       username = request.session[REQ_KEY_USERNAME]
       userId = int(request.session[REQ_KEY_USERID])
       status = None
       if request.method == 'POST':
          units = float(request.POST['quantity'])
          unit_price = float(request.POST['unit_price'])
          unit_price_currency = request.POST['unit_price_currency']
          total_amount = float(request.POST['total_amount'])
          crypto = request.POST['crypto']
          order = OrderItem('', userId, username, unit_price,
              unit_price_currency, units, units, total_amount,
              crypto, None, None)
          status = ordermanager.create_sell_order(order, username)
       accountinfo = useraccountinfomanager.get_user_accountInfo(userId, 'AXFund', True)
       sellorders = ordermanager.get_user_open_sell_orders(userId)
       buyorders = ordermanager.get_pending_incoming_buy_orders_by_user(userId)
       return render(request, 'html/mysellorder.html', {'sellorders': sellorders,
                'buyorders':buyorders, REQ_KEY_USERNAME: username,
                'useraccountInfo': accountinfo,
                'previous_call_status' : status})

    except Exception as e:
       error_msg = '出售美基金遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def cancel_sell_order(request):
    #try:
       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/mysellorder/'})
       username = request.session[REQ_KEY_USERNAME]
       userId = int(request.session[REQ_KEY_USERID])
       if request.method == 'POST':
           orderid = request.POST['order_id']
           ordermanager.cancel_sell_order(userId, orderid, 'AXFund', username)
       accountinfo = useraccountinfomanager.get_user_accountInfo(userId, 'AXFund', True)
       sellorders = ordermanager.get_user_open_sell_orders(userId)
       buyorders = ordermanager.get_pending_incoming_buy_orders_by_user(userId)
       return render(request, 'html/mysellorder.html', {
                'sellorders': sellorders,
                'useraccountInfo': useraccountInfo,
                'buyorders':buyorders, REQ_KEY_USERNAME: username})

    #except Exception as e:
       error_msg = '撤销美基金卖单遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
