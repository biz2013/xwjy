#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase
from django.test import Client
from tarderequest import *

# Create your tests here.
class TestRedeem(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def validate_success_prepurchase_response(self, resp_json):
        return False

    def purchase(self):
        request = TradeRequest('testapi_key', 'test_secret_key',
                20180320222600_123, # order id
                0.05, # total fee
                '127.0.0.1', #client ip
                attached='userid:1',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        response = c.post('/tradapi/prepurchase/',
                            json.dumps(request),
                            content_type="application/json")

        resp_json = json.loads(response.content)
        self.assertTrue(self.validate_success_prepurchase_response(resp_json))
