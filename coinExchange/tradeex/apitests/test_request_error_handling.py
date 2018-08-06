#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, io, traceback, time, json, copy, math
import logging

from calendar import timegm
import datetime as dt
from datetime import timedelta
sys.path.append('../stakingsvc/')
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.test import Client


from unittest.mock import Mock, MagicMock, patch

from tradeex.data.tradeapirequest import TradeAPIRequest
from tradeex.data.api_const import *
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
from tradeex.apitests.tradingutils import *
from tradeex.apitests.util_tests import *
from tradeex.responses.heepaynotify import HeepayNotification
from tradeex.controllers.crypto_utils import *
from tradeex.models import *
from trading.models import *
from trading.controller import useraccountinfomanager
import json

TEST_HY_BILL_NO='180102122300364021000081666'
TEST_HY_APPID = 'hyq17121610000800000911220E16AB0'
TEST_HY_KEY='4AE4583FD4D240559F80ED39'
TEST_BUYER_ACCOUNT='13910978598'
TEST_SELLER_ACCOUNT='api_user2_12345'
TEST_API_USER1_APPKEY = 'TRADEEX_USER1_APP_KEY_1234567890ABCDE'
TEST_API_USER2_APPKEY = 'TRADEEX_USER2_APP_KEY_SELLER'
TEST_API_USER1_SECRET='TRADEEX_USER1_APP_SECRET'
TEST_API_USER2_SECRET='TRADEEX_USER2_API_SECRET'

TEST_OUT_TRADE_NO_REDEEM = 'order_to_redeem'

TEST_PURCHASE_AMOUNT = 62
TEST_REDEEM_AMOUNT = 50
TEST_CNY_ADDR="TRADDEX_USER1_EXTERNAL_TEST_ADDR"
TEST_CRYPTO_SEND_COMMENT = ""
TEST_NOTIFY_URL = "http://testurl/"

class TestErrorHandling(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def create_no_fitting_order(self):
        print('create_no_fitting_order()')
        resp = create_axfund_sell_order('tttzhang2000@yahoo.com', 'user@123', 100, 0.5, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 100 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content,'Create order of 100 units hit issue')

        resp = create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 200, 0.3, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 200 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 200 units hit issue')

    def test_purchase_bad_user_account(self):
        #self.create_no_fitting_order()
        request = TradeAPIRequest(
                API_METHOD_PURCHASE,
                'user_does_not_exist',
                'secret_key_not_exist',
                'order_no_order', # order id
                None, # trx_id
                620, # total fee
                10, # expire_minute
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                subject='人民币充值测试-账号不存在',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/api/v1/applypurchase/', request_str,
                          content_type='application/json')

        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(2, len(resp_json))
        self.assertEqual(resp_json['return_code'], 'FAILED')
        self.assertEqual(resp_json['return_msg'], '用户不存在')

    def test_purchase_no_fitting_order(self):
        request = TradeAPIRequest(
                API_METHOD_PURCHASE,
                TEST_API_USER1_APPKEY,
                TEST_API_USER1_SECRET,
                'order_no_order', # order id
                None, # trx_id
                62000, # total fee
                10, # expire_minute
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                subject='人民币充值测试-没有合适卖单',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/api/v1/applypurchase/', request_str,
                          content_type='application/json')

        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'FAILED')
        self.assertEqual(resp_json['return_msg'], '无卖单提供充值')
        #TODO: show user not found?
