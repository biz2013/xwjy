#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
from django.test import TestCase, TransactionTestCase
from django.test import Client
from django.contrib.auth.models import User

from trading.models import *

from trading.controller import redeemmanager
from trading.controller.axfd_utils import *
from trading.views import redeemview

class TestRedeem(TransactionTestCase):
    fixtures = ['fixture_test_redeem.json']

    def test_redeem_no_account_address(self):
        c = Client()
        c.login(username='tttzhang2000@yahoo.com', password='user@123')
        redeem_req = { 'toaddress': 'AcinEAwDsYgUDHeZijSDD7AHYNuDdqBn5j',
          'quantity': '20.0',
          'crypto': 'AXFund'
         }
        response = c.post('/trading/accounts/redeem/', redeem_req, follow=True)
        print('test_redeem_no_account_address(): return {0}'.format(response.content.decode('utf-8')))

        self.assertTrue('您的提币地址属于交易平台注入地址，请修改您的提币地址'.encode('utf-8') in response.content)
