#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, io, traceback, time, json, copy, math
import logging
import http.client

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

logger = logging.getLogger('tradeex.apitests.test_error_handling2')

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


def send_buy_apply_fail_side_effect(payload):
    json_payload = json.loads(payload)
    biz_content = json.loads(json_payload['biz_content'])
    if biz_content['subject'] == 'heepay_return_503':
        return 503, 'Server Error', 'BAD REQUEST'
    elif biz_content['subject'] == 'heepay_throw_except':
        conn = http.client.HTTPSConnection('wallet.heepay.com')
        pay_url = '/Api/v1/PayApply'
        logger.info('the payload is {0}'.format(payload))
        headers = {"Content-Type": "application/json",
               "charset": "UTF-8"}
        conn.request('POST', pay_url, payload.encode('utf-8'), headers)
        response = conn.getresponse()


class TestErrorHandling2(TestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def test_signature_failure(self):
        request = TradeAPIRequest(
            API_METHOD_PURCHASE,
            TEST_API_USER1_APPKEY,
            TEST_API_USER1_SECRET,
            'order_no_order', # order id
            total_fee=100,
            expire_minute=10, # expire_minute
            payment_provider='heepay', 
            payment_account='123456',
            client_ip='127.0.0.1', #client ip
            attach='userid:1',
            subject='签名不符测试',
            notify_url='http://notify_url',
            return_url='http://return_url')
        request_json = json.loads(request.getPayload())
        # disturb the sign

        request_json['sign'] = request_json['sign'][:len(request_json['sign'])-2]
        request_str = json.dumps(request_json, ensure_ascii = False)
        c = Client()
        response = c.post('/api/v1/applypurchase/', request_str,
                    content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual('FAIL', resp_json['return_code'])
        self.assertEqual('签名不符', resp_json['return_msg'])

        request = TradeAPIRequest(
            API_METHOD_REDEEM,
            TEST_API_USER1_APPKEY,
            TEST_API_USER1_SECRET,
            'order_no_order', # order id
            total_fee=100,
            expire_minute=10, # expire_minute
            payment_provider='heepay', 
            payment_account='123456',
            client_ip='127.0.0.1', #client ip
            attach='userid:1',
            subject='签名不符测试',
            notify_url='http://notify_url',
            return_url='http://return_url')
        request_json = json.loads(request.getPayload())
        # disturb the sign
        request_json['sign'] = request_json['sign'][:len(request_json['sign'])-2]
        request_str = json.dumps(request_json, ensure_ascii = False)
        c = Client()
        response = c.post('/api/v1/applyredeem/', request_str,
                    content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual('FAIL', resp_json['return_code'])
        self.assertEqual('签名不符', resp_json['return_msg'])

        request = TradeAPIRequest(
            API_METHOD_QUERY,
            TEST_API_USER1_APPKEY,
            TEST_API_USER1_SECRET,
            'order_no_order', # order id
            trx_bill_no='FAKETRANSID',
            timestamp = timegm(dt.datetime.utcnow().utctimetuple())
        )

        request_json = json.loads(request.getPayload())
        # disturb the sign
        request_json['sign'] = request_json['sign'][:len(request_json['sign'])-2]
        request_str = json.dumps(request_json, ensure_ascii = False)
        c = Client()
        response = c.post('/api/v1/checkstatus/', request_str,
                    content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual('FAIL', resp_json['return_code'])
        self.assertEqual('签名不符', resp_json['return_msg'])

    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_fail_side_effect)
    def test_heepay_request_failure(self, send_json_request_function):
        create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 200, 0.51, 'CNY')
        request = TradeAPIRequest(
                API_METHOD_REDEEM,
                TEST_API_USER2_APPKEY,
                TEST_API_USER2_SECRET,
                'order_no_order', # order id
                None, # trx_id
                10000, # total fee
                10, # expire_minute
                'heepay', '12345',
                '127.0.0.1', #client ip
                attach='userid:1',
                subject='heepay_return_503',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        response = c.post('/api/v1/applyredeem/', request_str,
                          content_type='application/json')
        
        