#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase
from django.test import Client
from django.contrib.auth.models import User

from mock import Mock, MagicMock, patch
from controller import axfd_utils, useraccountinfomanager, loginmanager
from users.models import *
from test1.forms import *
from setuptest import *
import sys, traceback, time, json

test_data = json.load(open('tests/data/trx_test_data1.json'))
class AccountCronJobTestCase(TransactionTestCase):
    fixtures = ['fixture_for_tests.json']

    def setUp(self):
        try:
            User.objects.get(username='taozhang')
        except User.DoesNotExist:
            setup_test()

    @patch.object(axfd_utils.AXFundUtility, 'listtransactions')
    def test_update_account_from_trx(self, mock_listtransactions):
        print 'testdata is {0}'.format(test_data)
        mock_listtransactions.return_value = test_data

        #with patch('controller.axfd_utils.axfd_listtransactions') as mock:
        #    instance = mock.return_value
        #    instance.method.return_value = test_data
        c = Client()
        response = c.get('/account/cron/update_receive/')
        self.assertEqual(200, response.status_code)
        #useraccountinfomanager.update_account_balance_with_wallet_trx(
        #   'AXFund', '', 1000, 8)

        user1_wallet = UserWallet.objects.get(user__username='taozhang',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        user2_wallet = UserWallet.objects.get(user__username='yingzhou',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        self.assertEqual(0.6, user1_wallet.balance)
        self.assertEqual(190.0, user2_wallet.balance)
        user1_trans = UserWalletTransaction.objects.get(
             reference_wallet_trxId='df3e329ef6f4880a349acaaf36e66c5a35bab704b782323f6239abc2751d84ab'
        )
        user1_trans.status = 'PROCESSED'
        user2_trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='5f0c2a916b482c0bc6c15c9019b87f65716b9b2c218b09bbd3dcd1f4ef2d00f7'
        )
        user2_trans1.status = 'PROCESSED'
        user2_trans2 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='df3e329ef6f4880a349acaaf36e66c5a35bab704b782323f6239abc2751d84ab'
        )
        user2_trans2.status = 'PROCESSED'
        user2_trans3 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='ece467bb111f0f9209bac43556dd380f5f2cde571e014aada89c2c7b58f45d4f'
        )
        user2_trans2.status = 'PENDING'
