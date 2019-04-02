#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect
from trading.controller.global_utils import *

# this is for test UI. A fake one
from trading.controller.global_constants import *
from trading.controller import userpaymentmethodmanager
from trading.models import *
from trading.views.models.returnstatus import ReturnStatus
from trading.views import errorpageview
from django.contrib.auth.decorators import login_required

import logging
# logger for user registration
logger = logging.getLogger("site.weixinsetupview")

def get_weixin_images(weixin_id):
    weixin_payment_image = None
    weixin_shop_assistant_image = None
    if weixin_id is not None:
        weixin_images = userpaymentmethodmanager.get_weixin_images(weixin_id)
        if weixin_images:
            for img in weixin_images:
                if img.image_tag == 'WXPAYMENTQRCODE':
                    weixin_payment_image = img
                elif img.image_tag == 'WXSHOPASSTQRCODE':
                    weixin_shop_assistant_image = img
    return weixin_payment_image, weixin_shop_assistant_image
@login_required
def account_info(request):
    try:
        weixin_payment_image = weixin_shop_assistant_image = None
        if request.method == 'GET':
            weixin = userpaymentmethodmanager.get_weixin_paymentmethod(request.user.id)
            weixin_payment_image, weixin_shop_assistant_image = get_weixin_images((UserPaymentMethod(weixin)).id)
        else:
            form = UserPaymenthodForm(request.POST, request.FILES)
            if form.is_valid():
                weixin = form.save()
                weixin_payment_image, weixin_shop_assistant_image = get_weixin_images(weixin.id)
                
        return render(request, 'trading/paymentmethod/weixin.html',
            {'weixin':weixin,
            'weixin_payment_image': weixin_payment_image, 
            'weixin_shop_assistant_image': weixin_shop_assistant_image})
    except Exception as e:
        error_msg = 'sell_axfund hit exception'
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

def payment_qrcode(request):
    return render(request, 'trading/paymentmethod/weixin.html')

def shop_assistant_qrcode(request):
    return render(request, 'trading/paymentmethod/weixin.html')

