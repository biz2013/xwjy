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

def get_user_paypal_payment_method(userid):
    methods = UserPaymentMethod.objects.filter(user__id = userid)
    logger.info('get_user_paypal_payment_methods({0})'.format(userid))
    for method in methods:
        if method.provider.code == 'paypal':
            record = UserPaymentMethodView(method.id, userid,
                method.provider.code, method.provider.name,
                method.account_at_provider, method.provider_qrcode_image,
                method.client_id, method.client_secret)
            return record
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

def get_weixin_paymentmethod(userid):
    try:
        return UserPaymentMethod.objects.get(user__id=userid, provider= PAYMENTMETHOD_WEIXIN)
    except UserPaymentMethod.DoesNotExist:
        return None

def get_weixin_images(payment_method_id):
    return UserPaymentMethodImage.objects.filter(user_payment_method = payment_method_id)
    
