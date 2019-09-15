#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging

from django.db import transaction
from django.contrib.auth.models import User

from trading.models import *
from trading.config import context_processor
from trading.controller import axfd_utils
from trading.controller.global_constants import *
from trading.views.models.useraccountinfo import *
from trading.views.models.userpaymentmethodview import *
from trading.views.models.userexternalwalletaddrinfo import *

logger = logging.getLogger('site.userpaymentmethodmanager')

ERR_SELLER_WEIXIN_NOT_FULLY_SETUP = 'ERR_SELLER_WEIXIN_NOT_FULLY_SETUP'
ERR_SELLER_PAYPAL_NOT_FULLY_SETUP = 'ERR_SELLER_PAYPAL_NOT_FULLY_SETUP'

def get_payment_providers():
    return PaymentProvider.objects.all()

def get_user_payment_methods(userid):
    methods = UserPaymentMethod.objects.filter(user__id = userid)
    logger.info('get_user_payment_methods({0})'.format(userid))
    method_list = []
    for method in methods:
        record = UserPaymentMethodView(method.id, userid,
            method.provider.code, method.provider.name,
            method.account_at_provider, method.provider_qrcode_image,
            method.client_id, method.client_secret)
        method_list.append(record)
    return method_list

def get_user_payment_method_by_provider(userid, provider_code):
    try:
        return UserPaymentMethod.objects.get(user__id = userid, provider__code = provider_code)
    except UserPaymentMethod.DoesNotExist:
        return None

def get_weixin_paymentmethod(userid):
    return get_user_payment_method_by_provider(userid, PAYMENTMETHOD_WEIXIN)

def get_paypal_paymentmethod(userid):
    return get_user_payment_method_by_provider(userid, PAYMENTMETHOD_PAYPAL)

def get_user_paypal_payment_method(userid):
    try:
        paypal = UserPaymentMethod.objects.get(user__id = userid, provider__code = PAYMENTMETHOD_PAYPAL)
        return UserPaymentMethodView(paypal.id, userid,
                paypal.provider.code, paypal.provider.name,
                paypal.account_at_provider, paypal.provider_qrcode_image,
                paypal.client_id, paypal.client_secret)
    except UserPaymentMethod.DoesNotExist:
        return None

def create_update_user_payment_method(user_payment_method, operator):
    operatorObj = User.objects.get(username=operator)
    if user_payment_method.user_payment_method_id == 0:
        UserPaymentMethod.objects.create(
         user = User.objects.get(pk=user_payment_method.userid),
         provider = PaymentProvider.objects.get(pk=user_payment_method.provider_code),
         account_at_provider = user_payment_method.account_at_provider,
         provider_qrcode_image = user_payment_method.qrcode_image,
         client_id = user_payment_method.client_id,
         client_secret = user_payment_method.client_secret,
         created_by = operatorObj,
         lastupdated_by = operatorObj
        )
    else:
        with transaction.atomic():
            record = UserPaymentMethod.objects.select_for_update().get(id = user_payment_method.user_payment_method_id)
            record.account_at_provider = user_payment_method.account_at_provider
            record.client_id = user_payment_method.client_id
            record.client_secret = user_payment_method.client_secret
            record.lastupdated_by = operatorObj
            record.save()

def get_weixin_images(weixin_id):
    weixin_payment_image = None
    weixin_shop_assistant_image = None
    if weixin_id is not None:
        weixin_images = UserPaymentMethodImage.objects.filter(user_payment_method = weixin_id)
        if weixin_images:
            for img in weixin_images:
                if img.image_tag == 'WXPAYMENTQRCODE':
                    weixin_payment_image = img
                elif img.image_tag == 'WXSHOPASSTQRCODE':
                    weixin_shop_assistant_image = img
    return weixin_payment_image, weixin_shop_assistant_image

def load_weixin_info(user):
    weixin_payment_image = weixin_shop_assistant_image = None
    weixin = get_weixin_paymentmethod(user.id)
    if weixin:
        weixin.lastupdated_by = user
        weixin_payment_image, weixin_shop_assistant_image = get_weixin_images(weixin.id)
        if weixin_payment_image:
            weixin_payment_image.lastupdated_by = user
        if weixin_shop_assistant_image:
            weixin_shop_assistant_image.lastupdated_by = user
    return weixin, weixin_payment_image, weixin_shop_assistant_image