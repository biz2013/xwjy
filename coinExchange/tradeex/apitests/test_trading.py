#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../stakingsvc/')
from django.test import TestCase, TransactionTestCase
from django.test import Client
from tradeapi.data.traderequest import *

import json

# Create your tests here.
class TestPrepurchase(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def validate_success_prepurchase_response(self, resp_json):
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        return True

    def test_purchase(self):
        request = PrepurchaseRequest('testapi_key', 'test_secret_key',
                '20180320222600_123', # order id
                0.05, # total fee
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attached='userid:1',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}', request_str)
        response = c.post('/tradeapi/prepurchase/', request_str,
                          content_type='application/json')

        print('response is ' + json.dumps(response.json()))
        resp_json = json.loads(response.content)
        self.assertTrue(self.validate_success_prepurchase_response(resp_json))


