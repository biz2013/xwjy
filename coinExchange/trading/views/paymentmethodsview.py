#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.http.response import HttpResponse, HttpResponseNotAllowed,HttpResponseBadRequest,HttpResponseNotFound,HttpResponseServerError
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from trading.controller.heepaymanager import HeePayManager
from trading.controller.global_utils import *

# this is for test UI. A fake one
from trading.controller.global_constants import *
from trading.controller import userpaymentmethodmanager
from trading.models import *
from tradeex.models import *
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
    elif method == PAYMENTMETHOD_HEEPAY:
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
        payment_method = order.reference_order.seller_payment_method if order.reference_order.seller_payment_method else userpaymentmethodmanager.load_weixin_info(order.reference_order.user.id)
        if not payment_method:
            logger.error('show_payment_qrcode(): Cannot find valid seller payment method for sell order {0} referenced by purchase order {1}'.format(
                order.reference_order.order_id, order.order_id
            ))
            return HttpResponseServerError('对应卖单没有付款方式')
        
        if not payment_method.provider_qrcode_image:
            logger.error('show_payment_qrcode(): sell order {0} referenced by purchase order {1} does not have payment qrcode'.format(
                order.reference_order.order_id, order.order_id
            ))
            return HttpResponseServerError('对应卖单没有付款方式的二维码')


        return render(request, 'trading/paymentmethodqrcode.html',
            {'payment_method': payment_method_to_Chinese(payment_method.provider.code),
             'total_amount': order.total_amount,
             'unit_price_currency': order.reference_order.unit_price_currency,
             'order_units': order.units,
             'qrcode_url': payment_method.provider_qrcode_image.url
            }
        )
    except Order.DoesNotExist:
        logger.error("show_payment_qrcode(): Can not find related purchase order {0}".format(buyorder_id))
        return HttpResponseNotFound('没有找到购买单据')

<<<<<<< HEAD
@never_cache
=======
>>>>>>> d281f40eae4a6e4e0240aba881fd940b11569a86
def get_payment_qrcode_image(request):
    if request.method == 'POST':
        logger.error("get_payment_qrcode_image(): encounter illegal POST request")
        return HttpResponseNotAllowed("读取付款二维码需要用GET请求")
    
    buyorder_id = out_trade_no = None
    try:
        payment_methpd = None
        order = NotImplementedError
        if 'key' in request.GET:
            buyorder_id = request.GET['key']
            order = Order.objects.get(order_id=buyorder_id)
        elif 'out_trade_no' in request.GET:
            out_trade_no = request.GET['out_trade_no']
            api_tran = APIUserTransaction.objects.get(api_out_trade_no = out_trade_no)
            order = api_tran.reference_order
            if not order:
                return HttpResponseBadRequest('没有找到相关out_trade_no的购买单据')
        else:
            return HttpResponseBadRequest('请求没有out_trade_no或key')

        if order.order_type != 'BUY':
            logger.error('get_payment_qrcode_image(): The order found by {0}:{1} is not a BUY order'.format(
                'buy order id' if buyorder_id else 'out_trade_no', 
                buyorder_id if buyorder_id else out_trade_no))
            return HttpResponseBadRequest('请求的相关单据不是买单')

        payment_method = order.reference_order.seller_payment_method if order.reference_order.seller_payment_method else userpaymentmethodmanager.load_weixin_info(order.reference_order.user.id)
        if not payment_method:
            logger.error('get_payment_qrcode_image(): Cannot find valid seller payment method for sell order {0} referenced by purchase order {1}'.format(
                order.reference_order.order_id, order.order_id
            ))
            return HttpResponseServerError('对应卖单没有付款方式')
        if not payment_method.provider_qrcode_image:
            logger.error('get_payment_qrcode_image(): sell order {0} referenced by purchase order {1} does not have payment qrcode'.format(
                order.reference_order.order_id, order.order_id
            ))
            return HttpResponseServerError('对应卖单没有付款方式的二维码')
    
        qrcode_file = os.path.join("upload", "paymentmethod", payment_method.provider.code, payment_method.provider_qrcode_image.path)
        logger.debug("get_payment_qrcode_image: qrcode is at {0}".format(qrcode_file))
        if not os.path.exists(qrcode_file):
            logger.error("get_payment_qrcode_image: qrcode image at {0} does not exist".format(qrcode_file))
            return HttpResponseNotFound("对应二维码图像找不到")
        
        name, extension = os.path.splitext(qrcode_file)
        content_types = { 'png': "image/pmg",
            'jpg': "image/jpeg",
            'jpeg' : "image/jpeg",
            'gif' : "image/gif"
        }

        img_content_type = content_types.get(extension, "image/png")
        logger.debug("get_payment_qrcode_image: image content type is {0}".format(img_content_type))
        image_data = open(qrcode_file, "rb").read()
        return HttpResponse(image_data, content_type=img_content_type)
    except Order.DoesNotExist:
        logger.error("get_payment_qrcode_image(): Can not find related purchase order {0}".format(buyorder_id))
        return HttpResponseNotFound('没有找到购买单据{0}'.format(buyorder_id))
    except APIUserTransaction.DoesNotExist:
        logger.error("get_payment_qrcode_image(): Can not find api user transaction based on out_trade_no {0}".format(out_trade_no))
        return HttpResponseNotFound('没有找到out_trade_no相关的充值请求'.format(buyorder_id))
    except:
        error_msg = 'get_payment_qrcode_image()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return HttpResponseServerError(content='请求遇到错误')      

        

    
