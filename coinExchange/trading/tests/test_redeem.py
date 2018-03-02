#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
from django.test import TestCase, TransactionTestCase
from django.test import Client
from django.contrib.auth.models import User
from unittest.mock import Mock, MagicMock, patch

from trading.models import *

from trading.controller import redeemmanager
from trading.controller import axfd_utils
from trading.views import redeemview

test_data1 = json.load(open('trading/tests/data/trx_test_data_redeem.json'))

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

    #
    # !!! PAY ATTENTION TO THE ORDER OF FUNCTION, IT IS FILO
    #
    @patch.object(axfd_utils.AXFundUtility, 'unlock_wallet')
    @patch.object(axfd_utils.AXFundUtility, 'send_fund')
    def test_redeem_succeed(self, mock_send_fund, mock_unlock_wallet):
        mock_unlock_wallet.return_value=None
        mock_send_fund.return_value = test_data1
        c = Client()
        c.login(username='tttzhang2000@yahoo.com', password='user@123')
        redeem_req = { 'toaddress': 'redeem_test_address',
          'quantity': '20.0',
          'crypto': 'AXFund'
         }

        response = c.post('/trading/accounts/redeem/', redeem_req, follow=True)
        print('test_redeem_succeed(): return {0}'.format(response.content.decode('utf-8')))

        self.assertTrue('总余额：100.0 可用余额: 79.9999 锁定余额: 20.0001'.encode('utf-8') in response.content)              
