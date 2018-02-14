#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.contrib import messages
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from trading.controller.global_constants import *
from trading.controller.global_utils import *
from trading.controller import ordermanager
from trading.controller import useraccountinfomanager

from trading.views.models.orderitem import OrderItem
from trading.views.models.returnstatus import ReturnStatus
from trading.views import errorpageview
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
          crypto, None, None, 'SELL')

@login_required
def sell_axfund(request):
    try:
       if not request.user.is_authenticated():
          return render(request, 'login.html', { 'next' : '/mysellorder/'})
       accountinfo = useraccountinfomanager.get_user_accountInfo(request.user, 'AXFund')
       if len(accountinfo.paymentmethods) == 0:
           messages.error(request, '请先注册支付方式再挂卖单')
           return redirect('accountinfo')
       if len(accountinfo.paymentmethods[0].account_at_provider) == 0:
           messages.error(request, '请先注册支付账号再挂卖单')
           return redirect('accountinfo')
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
       sellorders = ordermanager.get_sell_transactions_by_user(request.user.id)
       if request.method == 'POST':
           return redirect('sellorder')
       else:
           return render(request, 'html/mysellorder.html',
               {'sellorders': sellorders,
                'useraccountInfo': accountinfo})

    except Exception as e:
       error_msg = '出售美基金遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def confirm_payment(request):
    try:
       if not request.user.is_authenticated():
          return render(request, 'login.html', { 'next_action' : '/mysellorder/'})
       order_id = request.POST['order_id']
       ordermanager.confirm_purchase_order(order_id, request.user.username)
       messages.success(request,'确认付款，交易完成')
       return redirect('sellorder')
    except Exception as e:
       error_msg = '确认付款遇到错误: {0}'.format(sys.exc_info()[0])
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

       return redirect('sellorder')
    except ValueError as ve:
       if ve.args[0] == "ORDER_USED_OR_LOCKED_CANCELLED":
           logger.exception("Cancel hit exception: {0} ".format(ve.args[0]))
           messages.error(request, "您选择的卖单有待完成买单，或在锁定，取消状态")
           return redirect('sellorder')
       else:
           raise
    except Exception as e:
       error_msg = '撤销美基金卖单遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
