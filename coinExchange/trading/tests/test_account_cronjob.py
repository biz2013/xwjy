#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase
from django.test import Client
from django.contrib.auth.models import User

from trading.controller import axfd_utils, useraccountinfomanager
from trading.models import *
#from trading.forms import *
from trading.tests.setuptest import *
from unittest.mock import Mock, MagicMock, patch
import datetime as dt
import sys, traceback, time, json, math

test_data1 = json.load(open('trading/tests/data/trx_test_data1.json'))
test_data2 = json.load(open('trading/tests/data/trx_test_data2.json'))
class AccountCronJobTestCase(TransactionTestCase):
    fixtures = ['fixture_for_account_cronjob.json']

    def setUp(self):
        try:
            User.objects.get(username='tttzhang2000@yahoo.com')
        except User.DoesNotExist:
            setup_test()

    @patch.object(axfd_utils.AXFundUtility, 'listtransactions')
    def test_update_account_from_trx(self, mock_listtransactions):
        mock_listtransactions.return_value = test_data1

        # set user's wallet to test address
        updated = UserWallet.objects.filter(user__username='taozhang',
          wallet__cryptocurrency__currency_code='AXFund').update(
          wallet_addr='AGqfmz49fVFpdoKRfaw2zN7CikWAhUsYdE',
          lastupdated_at = dt.datetime.utcnow())
        if not updated:
            self.fail('Did not find userwallet for taozhang')
        taozhang = User.objects.get(username='taozhang')
        print ('taozhang\'s userid is {0}'.format(taozhang.id))
        updated = UserWallet.objects.filter(user__username='yingzhou',
          wallet__cryptocurrency__currency_code='AXFund').update(
          wallet_addr='AboGeCuvs8U8nGGuoe9awZzhUDHTkuiG4Y',
          lastupdated_at = dt.datetime.utcnow())
        if not updated:
            fail('Did not find userwallet for yingzhou')
        yingzhou = User.objects.get(username='yingzhou')
        print ('yingzhou\'s userid is {0}'.format(yingzhou.id))

        #with patch('controller.axfd_utils.axfd_listtransactions') as mock:
        #    instance = mock.return_value
        #    instance.method.return_value = test_data
        c = Client()
        response = c.get('/trading/account/cron/update_receive/')
        self.assertEqual(200, response.status_code)

        user1_wallet = UserWallet.objects.get(user__username='taozhang',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        print ('about to test user_Wallet {0} user {1}'.format(
            user1_wallet.id, user1_wallet.user.id
        ))
        user2_wallet = UserWallet.objects.get(user__username='yingzhou',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        self.assertEqual(101, user1_wallet.balance)
        self.assertEqual(1.2, user2_wallet.balance)
        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63'
            )
            self.assertEqual(2, trans1.user_wallet.user.id)
            self.assertEqual('PROCESSED', trans1.status)
            self.assertTrue(math.fabs(trans1.units - 100.0) < 0.00000001)
            self.assertTrue(math.fabs(trans1.balance_end - trans1.balance_begin - 100.0)<0.00000001)
            self.assertEqual(trans1.locked_balance_begin, trans1.locked_balance_end)
            self.assertTrue(math.fabs(trans1.available_to_trade_end - trans1.available_to_trade_begin - 100.0) < 0.0000001)
            self.assertEqual('CREDIT', trans1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            fail('Could not find userwallettransaction for txid e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63')

        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820'
            )
            self.assertEqual(2, trans1.user_wallet.user.id)
            self.assertEqual('PENDING', trans1.status)
            self.assertTrue(math.fabs(trans1.units - 1.0) < 0.00000001)
            self.assertEqual(0.0, trans1.balance_begin)
            self.assertEqual(0.0, trans1.balance_end)
            self.assertEqual(0.0, trans1.locked_balance_begin)
            self.assertEqual(0.0, trans1.locked_balance_end)
            self.assertEqual(0.0, trans1.available_to_trade_begin)
            self.assertEqual(0.0, trans1.available_to_trade_end)
            self.assertEqual('DEBT', trans1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            fail('Could not find userwallettransaction for txid cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820')

        mock_listtransactions.return_value = test_data2
        c = Client()
        response = c.get('/trading/account/cron/update_receive/')
        self.assertEqual(200, response.status_code)

        user1_wallet = UserWallet.objects.get(user__username='taozhang',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        user2_wallet = UserWallet.objects.get(user__username='yingzhou',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        self.assertEqual(95.8, user1_wallet.balance)
        self.assertEqual(-1.8, user2_wallet.balance)
        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63'
            )
            self.assertEqual(2, trans1.user_wallet.user.id)
            self.assertEqual('PROCESSED', trans1.status)
            self.assertTrue(math.fabs(trans1.units - 100.0) < 0.00000001)
            self.assertTrue(math.fabs(trans1.balance_end - trans1.balance_begin - 100.0)<0.00000001)
            self.assertEqual(trans1.locked_balance_begin, trans1.locked_balance_end)
            self.assertTrue(math.fabs(trans1.available_to_trade_end - trans1.available_to_trade_begin - 100.0) < 0.0000001)
            self.assertEqual('CREDIT', trans1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            fail('Could not find userwallettransaction for txid e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63')

        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820'
            )
            self.assertEqual(2, trans1.user_wallet.user.id)
            self.assertTrue(math.fabs(trans1.units - 1.0) < 0.00000001)
            self.assertTrue(math.fabs(trans1.balance_end - trans1.balance_begin + 1.0) < 0.00000001)
            self.assertEqual(trans1.locked_balance_begin, trans1.locked_balance_end)
            self.assertTrue(math.fabs(trans1.available_to_trade_end - trans1.available_to_trade_begin + 1.0) < 0.0000001)
            self.assertEqual('DEBT', trans1.balance_update_type)
            self.assertEqual('PROCESSED', trans1.status)
        except UserWalletTransaction.DoesNotExist:
            fail('Could not find userwallettransaction for txid cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820')

        # rerun should not make any problem
        mock_listtransactions.return_value = test_data2
        c = Client()
        response = c.get('/trading/account/cron/update_receive/')
        self.assertEqual(200, response.status_code)

        user1_wallet = UserWallet.objects.get(user__username='taozhang',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        user2_wallet = UserWallet.objects.get(user__username='yingzhou',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        self.assertEqual(95.8, user1_wallet.balance)
        self.assertEqual(-1.8, user2_wallet.balance)
        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63'
            )
            self.assertEqual(2, trans1.user_wallet.user.id)
            self.assertEqual('PROCESSED', trans1.status)
            self.assertTrue(math.fabs(trans1.units - 100.0) < 0.00000001)
            self.assertTrue(math.fabs(trans1.balance_end - trans1.balance_begin - 100.0)<0.00000001)
            self.assertEqual(trans1.locked_balance_begin, trans1.locked_balance_end)
            self.assertTrue(math.fabs(trans1.available_to_trade_end - trans1.available_to_trade_begin - 100.0) < 0.0000001)
            self.assertEqual('CREDIT', trans1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            fail('Could not find userwallettransaction for txid e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63')

        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820'
            )
            self.assertEqual(2, trans1.user_wallet.user.id)
            self.assertTrue(math.fabs(trans1.units - 1.0) < 0.00000001)
            self.assertTrue(math.fabs(trans1.balance_end - trans1.balance_begin + 1.0) < 0.00000001)
            self.assertEqual(trans1.locked_balance_begin, trans1.locked_balance_end)
            self.assertTrue(math.fabs(trans1.available_to_trade_end - trans1.available_to_trade_begin + 1.0) < 0.0000001)
            self.assertEqual('DEBT', trans1.balance_update_type)
            self.assertEqual('PROCESSED', trans1.status)
        except UserWalletTransaction.DoesNotExist:
            fail('Could not find userwallettransaction for txid cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820')
