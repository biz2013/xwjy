#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../stakingsvc/')
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.test import Client
from tradeapi.data.traderequest import PurchaseAPIRequest
from tradeex.apitests.tradingutils import *
from trading.models import *
from trading.controller import useraccountinfomanager
import json

# Create your tests here.
class TestPrepurchase(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def setUp(self):
        pass

    def validate_success_prepurchase_response(self, resp_json):
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        return True

    def test_purchase_user_not_found_api_key(self):
        request = PurchaseAPIRequest('api_key_not_exist', 'secrete_not_exist',
                '20180320222600_123', # order id
                0.05, # total fee
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')

        print('response is {0}'.format(json.dumps(json.loads(response.content), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], '参数错误')
        #TODO: show user not found?

    def validate_user_info(self, username):
        wallet_count = len(UserWallet.objects.all())
        self.assertTrue(wallet_count==6, "There should be 4 user wallets but have {0}".format(wallet_count))
        for wallet in UserWallet.objects.all():
            print('wallet {0}, user {1} {2}, balance {3}, address {4}, coin {5}'.format(
                wallet.id, wallet.user.id, wallet.user.username, wallet.balance, wallet.wallet_addr,
                wallet.wallet.cryptocurrency.currency_code
            ))

        useraccountInfo = useraccountinfomanager.get_user_accountInfo(User.objects.get(username=username),'AXFund')
        self.assertTrue(useraccountInfo.balance > 0, "the balance of {0} should be larger than 0".format(username))
        self.assertTrue(useraccountInfo.available_balance > 0, "the available balance of {0} should be larger than 0".format(username))
        self.assertTrue(useraccountInfo.paymentmethods, "user {0} should have payment info".format(username))
        self.assertEqual(1, len(useraccountInfo.paymentmethods), "There should be 1 payment method for user {0}".format(username))
        self.assertEqual('heepay', useraccountInfo.paymentmethods[0].provider_code, "user {0}\'s payment method should come from heepay".format(username))
        self.assertTrue(useraccountInfo.paymentmethods[0].account_at_provider, "User {0} should have account at heepay".format(username))

    def create_no_fitting_order(self):
        print('create_no_fitting_order()')
        self.validate_user_info('tttzhang2000@yahoo.com')
        resp = create_axfund_sell_order('tttzhang2000@yahoo.com', 'user@123', 100, 0.5, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 100 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content,'Create order of 100 units hit issue')

        self.validate_user_info('yingzhou61@yahoo.ca')
        resp = create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 200, 0.3, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 200 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 200 units hit issue')

        for order in Order.objects.all():
            print('order {0} order_type {1} sub_type {2}'.format(order.order_id, order.order_type, order.sub_type))

    def test_purchase_no_fitting_order(self):
        self.create_no_fitting_order()
        request = PurchaseAPIRequest('test_api_key1', 'user_secret_1',
                'order_no_order', # order id
                620, # total fee
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')

        print('response is {0}'.format(json.dumps(json.loads(response.content), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], '系统问题')
        #TODO: show user not found?
        


