#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.contrib import messages
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

def read_order_input(request):
    username = request.user.username
    userId = request.user.id
    units = float(request.POST['quantity'])
    unit_price = float(request.POST['unit_price'])
    unit_price_currency = request.POST['unit_price_currency']
    total_amount = float(request.POST['total_amount'])
    crypto = request.POST['crypto']
    return OrderItem('', userId, username, unit_price,
          unit_price_currency, units, units, total_amount,
          crypto, None, None)

@login_required
def sell_axfund(request):
    try:
       if not request.user.is_authenticated():
          return render(request, 'login.html', { 'next' : '/mysellorder/'})
       accountinfo = useraccountinfomanager.get_user_accountInfo(request.user, 'AXFund', True)
       if request.method == 'POST':
          request_source = request.POST['request_source']
          # this indicate that the request come from submit
          # order instead of refresh a response page of previous
          # order
          if len(request_source) > 0:
              order_command = read_order_input(request)
              if order_command.total_units - accountinfo.available_balance < 0:
                  ordermanager.create_sell_order(order_command, request.user.username)
                  messages.success(request,'您的卖单已经成功创建')
              else:
                  messages.error(request, '卖单数量不可以高于可用余额')
       sellorders = ordermanager.get_user_open_sell_orders(request.user.id)
       buyorders = ordermanager.get_pending_incoming_buy_orders_by_user(request.user.id)
       if request.method == 'POST':
           return redirect('sellorder')
       else:
           return render(request, 'html/mysellorder.html',
               {'sellorders': sellorders,
                'buyorders':buyorders,
                'useraccountInfo': accountinfo})

    except Exception as e:
       error_msg = '出售美基金遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def cancel_sell_order(request):
    try:
       if not request.user.is_authenticated():
          return render(request, 'login.html', { 'next_action' : '/mysellorder/'})
       username = request.user.username
       userId = request.user.id
       if request.method == 'POST':
           orderid = request.POST['order_id']
           ordermanager.cancel_sell_order(userId, orderid, 'AXFund', username)
       accountinfo = useraccountinfomanager.get_user_accountInfo(request.user, 'AXFund', True)
       sellorders = ordermanager.get_user_open_sell_orders(userId)
       buyorders = ordermanager.get_pending_incoming_buy_orders_by_user(userId)
       return render(request, 'html/mysellorder.html', {
                'sellorders': sellorders,
                'useraccountInfo': accountinfo,
                'buyorders':buyorders, REQ_KEY_USERNAME: username})

    except Exception as e:
       error_msg = '撤销美基金卖单遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
