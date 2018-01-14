#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging

from django.db import transaction
from django.contrib.auth.models import User

from users.models import *
from config import context_processor
from controller import axfd_utils
from views.models.useraccountinfo import *
from views.models.userpaymentmethodview import *
from views.models.userexternalwalletaddrinfo import *

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
            method.account_at_provider, method.provider_qrcode_image)
        method_list.append(record)
    return method_list

def create_update_user_payment_method(user_payment_method, operator):
    operatorObj = User.objects.get(username=operator)
    if user_payment_method.user_payment_method_id == 0:
        UserPaymentMethod.objects.create(
         user = User.objects.get(pk=user_payment_method.userid),
         provider = PaymentProvider.objects.get(pk=user_payment_method.provider_code),
         account_at_provider = user_payment_method.account_at_provider,
         provider_qrcode_image = user_payment_method.qrcode_image,
         created_by = operatorObj,
         lastupdated_by = operatorObj
        )
    else:
        with transaction.atomic():
            record = UserPaymentMethod.objects.select_for_update().get(id = user_payment_method.user_payment_method_id)
            record.account_at_provider = user_payment_method.account_at_provider
            record.lastupdated_by = operatorObj
            record.save()
