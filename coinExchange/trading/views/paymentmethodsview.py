#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.contrib import messages
from django.http.response import HttpResponseNotAllowed,HttpResponseBadRequest,HttpResponseNotFound,HttpResponseServerError
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
           client_id = request.POST['client_id']
           client_secret = request.POST['client_secret']

           has_error = False
           if len(payment_provider) == 0:
               has_error = True
               messages.error(request, '请选择支付方式')
           elif len(account) == 0 and len(client_id) == 0:
               has_error = True
               messages.error(request, '请输入您的账号或Client_ID')
           elif len(client_id) != 0 and len(client_secret) == 0:
               has_error = True
               messages.error(request, '请输入您的Client_Secret')
           if has_error:
               return redirect('paymentmethods')
           record = UserPaymentMethodView(payment_method_id,
                    request.user.id,
                    payment_provider,
                    '', account, '', client_id, client_secret)
           userpaymentmethodmanager.create_update_user_payment_method(record, request.user.username)
           return redirect('accountinfo')
    except Exception as e:
       error_msg = 'sell_axfund hit exception'
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

def payment_method_to_Chinese(method):
    if method == PAYMENTMETHOD_WEIXIN:
        return '微信支付'
    elif method = PAYMENTMETHOD_HEEPAY:
        return '汇钱包'
    elif method == PAYMENTMETHOD_ALIPAY:
        return '支付宝'
    elif method == PAYMENTMETHOD_PAYPAL:
        return 'PayPal'
    else:
        return method

def show_payment_qrcode(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    buyorder_id = request.GET['key']
    if not buyorder_id:
        return HttpResponseBadRequest('请求没有购买单据')

    try:
        order = Order.objects.get(order_id=buyorder_id)
        payment_method = order.reference_order.seller_payment_method if order.reference_order.seller_payment_method 
            else userpaymentmethodmanager.load_weixin_info(order.reference_order.user.id)
        if not payment_method:
            logger.error('show_payment_qrcode(): Cannot find valid seller payment method for sell order {0} referenced by purchase order {1}'.format(
                order.reference_order.order_id, order.order_id
            ))
            return HttpResponseServerError('对应卖单没有付款方式')
        
        if not payment_method.qrcode:
            logger.error('show_payment_qrcode(): sell order {0} referenced by purchase order {1} does not have payment qrcode'.format(
                order.reference_order.order_id, order.order_id
            ))
            return HttpResponseServerError('对应卖单没有付款方式的二维码')


        return render(request, 'trading/paymentmethodqrcode.html',
            {'payment_method': payment_method_to_Chinese(payment_method.provider.code),
             'total_amount': order.total_amount,
             'unit_price_currency': order.reference_order.unit_price_currency,
             'order_units': order.units
            }
        )
    except Order.DoesNotExist:
        logger.error("show_payment_qrcode(): Can not find related purchase order {0}".format(buyorder_id))
        return HttpResponseNotFound('没有找到购买单据')