#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, json

from django.test import TestCase
from tradeex.data.tradeapirequest import TradeAPIRequest
from tradeex.client.apiclient import APIClient

TEST_API_USER1_APPKEY = 'api_test_user_appId1'
TEST_API_USER1_SECRET ='api_test_user_secrets1'
TEST_PURCHASE_AMOUNT = 5


# Create your tests here.
class TestSetupUser(TestCase):

    def test_purchase_api_call(self):
        app_id = TEST_API_USER1_APPKEY
        secret_key = TEST_API_USER1_SECRET
        test_out_trade_no = 'order_to_purchase'
        test_purchase_amount = TEST_PURCHASE_AMOUNT
        test_user_heepay_from_account = '13910978598'
        test_attach = 'userid:1'
        test_subject = '人民币充值成功测试'
        test_notify_url = 'http://54.203.195.52/tradeex/api_notify_test/'
        test_return_url = 'http://54.203.195.52/tradeex/api_notify_test/'
        request = TradeAPIRequest(
                'wallet.trade.buy',
                app_id, secret_key,
                test_out_trade_no, # out_trade_no
                total_fee=test_purchase_amount, # total fee
                expire_minute=10, # expire_minute
                payment_provider='heepay', 
                payment_account=test_user_heepay_from_account,
                client_ip='127.0.0.1', #client ip
                attach=test_attach,
                subject=test_subject,
                notify_url=test_notify_url,
                return_url=test_return_url)

        c = APIClient('http://54.203.195.52/tradeex/purchasetoken/')
        request_str = request.getPayload()
        resp_json = c.send_json_request(json.loads(request_str))
        print('reply is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))

