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
from trading.views.forms.UserPaymentMethodForm import *
from trading.views.forms.UserPaymentMethodImageForm import *
from django.contrib.auth.decorators import login_required

import logging
# logger for user registration
logger = logging.getLogger("site.weixinsetupview")

@login_required
def account_info(request):
    try:
        weixin, weixin_payment_image, weixin_shop_assistant_image = userpaymentmethodmanager.load_weixin_info(request.user)

        if request.method == 'POST':
            form = UserPaymentMethodForm(request.POST, request.FILES, instance = weixin)
            if form.is_valid():
                weixin = form.save()
                weixin_payment_image, weixin_shop_assistant_image = userpaymentmethodmanager.get_weixin_images(weixin.id)
            else: 
                messages.error(request,"输入有错误，请检查")

        payment_image_form = UserPaymentMethodImageForm(instance=weixin_shop_assistant_image)
        return render(request, 'trading/paymentmethod/weixin.html',
            {'user': request.user, 
             'weixin':weixin,
             'payment_provider' : weixin.provider.code if weixin is not None else PAYMENTMETHOD_WEIXIN,
             'weixin_payment_image': weixin_payment_image, 
             'weixin_shop_assistant_image': weixin_shop_assistant_image,
             'payment_image_form' : payment_image_form
            })
    except Exception as e:
        error_msg = 'sell_axfund hit exception'
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def payment_qrcode(request):
    try:
        weixin, weixin_payment_image, weixin_shop_assistant_image = userpaymentmethodmanager.load_weixin_info(request.user)
        if request.method == 'POST':
            form = UserPaymentMethodForm(request.POST, request.FILES, instance=weixin_payment_image)
            if form.is_valid():
                form.save()
                weixin, weixin_payment_image, weixin_shop_assistant_image = userpaymentmethodmanager.load_weixin_info(request.user)
            else: 
                messages.error(request,"输入有错误，请检查")

        return render(request, 'trading/paymentmethod/weixin.html',
            {'user': request.user, 
             'weixin':weixin,
             'payment_provider' : weixin.provider.code if weixin is not None else PAYMENTMETHOD_WEIXIN,
             'weixin_payment_image': weixin_payment_image, 
             'weixin_shop_assistant_image': weixin_shop_assistant_image
            })
    except Exception as e:
        error_msg = 'sell_axfund hit exception'
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def shop_assistant_qrcode(request):
    try:
        weixin, weixin_payment_image, weixin_shop_assistant_image = userpaymentmethodmanager.load_weixin_info(request.user)
        if request.method == 'POST':
            form = UserPaymentMethodImageForm(request.POST, request.FILES, instance=weixin_shop_assistant_image)
            if form.is_valid():
                form.save()
                weixin, weixin_payment_image, weixin_shop_assistant_image = userpaymentmethodmanager.load_weixin_info(request.user)
            else: 
                messages.error(request,"输入有错误，请检查")

        return render(request, 'trading/paymentmethod/weixin.html',
            {'user': request.user, 
             'weixin':weixin,
             'payment_provider' : weixin.provider.code if weixin is not None else PAYMENTMETHOD_WEIXIN,
             'weixin_payment_image': weixin_payment_image, 
             'weixin_shop_assistant_image': weixin_shop_assistant_image
            })
    except Exception as e:
        error_msg = 'sell_axfund hit exception'
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))