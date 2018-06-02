#!/usr/bin/python
# -*- coding: utf-8 -*-

from unittest.mock import Mock, MagicMock, patch
from django.test import TransactionTestCase
from django.test import Client

ADDRESS_COUNTER = 0
def create_wallet_address_mock():
    global ADDRESS_COUNTER
    ADDRESS_COUNTER = ADDRESS_COUNTER + 1
    return 'FAKETESTCNYWALLETADDRESS_{0}'.format(ADDRESS_COUNTER)

# Create your tests here.
class TestSetupUser(TransactionTestCase):
    fixtures = ['olddata-formatted.json']

    def setUp(self):
        pass

    @patch('tradeex.controllers.crypto_utils.CryptoUtility.create_wallet_address', side_effect=create_wallet_address_mock)
    def test_setupuser(self, create_wallet_address_function):
        c = Client()
        response = c.get('/setuptest/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('ok', response.content.decode('utf-8'))

        # call second time
        response = c.get('/setuptest/')
        self.assertEqual(200, response.status_code)
        self.assertEqual('ok', response.content.decode('utf-8'))
        

