#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../stakingsvc/')
from django.test import TestCase, TransactionTestCase
from django.test import Client
from tradeapi.data.traderequest import PurchaseAPIRequest
from tradeex.apitests.tradingutils import *
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
    
    def create_no_fitting_order(self):
        print('create_no_fitting_order()')
        resp = create_axfund_sell_order('tttzhang2000@yahoo.com', 'user@123', 100, 0.5, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 100 units should return 200")
        self.assertTrue('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 100 units hit issue')
        resp = create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 200, 0.3, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 200 units should return 200")
        self.assertTrue('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 200 units hit issue')


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
        


