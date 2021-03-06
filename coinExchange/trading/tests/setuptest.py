#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase
from django.test import Client
from django.contrib.auth.models import User

from trading.models import *

from trading.controller.heepaymanager import HeePayManager
from trading.views.models.orderitem import OrderItem
from trading.views.models.userpaymentmethodview import UserPaymentMethodView
from trading.views.models.registration import SignUpForm
from trading.controller import ordermanager, loginmanager
from trading.controller import userpaymentmethodmanager
from trading.controller.global_utils import *

import sys, io, traceback, time, json, copy
from unittest.mock import Mock, MagicMock, patch
from calendar import timegm
from datetime import datetime as dt

def setup_test():
    form = SignUpForm(data={'username':'taozhang','password1':'user@123', 'password2':'user@123', 'email':'tttzhang2000@yahoo.com'})
    form.full_clean()
    if not form.is_valid():
        print ('-{0}'.format(form.errors))
        raise ValueError('bad form')
    loginmanager.create_login(form, 'taozhang')
    seller = User.objects.get(username='taozhang')
    # prepare seller payment method
    seller_paymentmethod = UserPaymentMethodView(0, seller.id,
       'heepay', '汇钱包', '15811302702', '', '', '')
    userpaymentmethodmanager.create_update_user_payment_method(
           seller_paymentmethod, 'taozhang')

    form = SignUpForm(data={'username':'yingzhou','password1':'user@123', 'password2':'user@123', 'email':'yingzhou61@yahoo.ca'})
    if not form.is_valid():
        raise ValueError('bad form for buyer')
    loginmanager.create_login(form, 'yingzhou')
    buyer = User.objects.get(username='yingzhou')
    # prepare buyer payment method
    buyer_paymentmethod = UserPaymentMethodView(0, buyer.id,
       'heepay', '汇钱包', '13641388306', '', '','')
    userpaymentmethodmanager.create_update_user_payment_method(
           buyer_paymentmethod, 'yingzhou')

    form = SignUpForm(data={'username':'taozhang2','password1':'user@123', 'password2':'user@123', 'email':'taozhang@salesforce.com'})
    form.full_clean()
    if not form.is_valid():
        print ('-{0}'.format(form.errors))
        raise ValueError('bad form')
    loginmanager.create_login(form, 'taozhang2')
    seller = User.objects.get(username='taozhang2')
    # prepare seller payment method
    seller_paymentmethod = UserPaymentMethodView(0, seller.id,
       'heepay', '汇钱包', '15811302701', '', '','')
    userpaymentmethodmanager.create_update_user_payment_method(
           seller_paymentmethod, 'taozhang2')

    form = SignUpForm(data={'username':'yingzhou2','password1':'user@123', 'password2':'user@123', 'email':'yingzhou62@yahoo.ca'})
    if not form.is_valid():
        raise ValueError('bad form for buyer')
    loginmanager.create_login(form, 'yingzhou2')
    buyer = User.objects.get(username='yingzhou2')
    # prepare buyer payment method
    buyer_paymentmethod = UserPaymentMethodView(0, buyer.id,
       'heepay', '汇钱包', '13641388305', '','','')
    userpaymentmethodmanager.create_update_user_payment_method(
           buyer_paymentmethod, 'yingzhou2')
