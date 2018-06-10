#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase
from django.test import Client
from django.contrib.auth.models import User

from trading.controller import axfd_utils, useraccountinfomanager
from trading.models import *
from tradeex.controllers.crypto_utils import CryptoUtility
#from trading.forms import *
from trading.tests.setuptest import *
from unittest.mock import Mock, MagicMock, patch
import datetime as dt
import sys, traceback, time, json, math

test_data1 = json.load(open('trading/tests/data/trx_test_data1.json'))
test_data2 = json.load(open('trading/tests/data/trx_test_data2.json'))
test_data_cny_pass1 = json.load(open('trading/tests/data/trx_test_cny_wallet_1.json'))

class AccountCronJobTestCase(TransactionTestCase):
    fixtures = ['fixture_for_account_cronjob.json']

    def setUp(self):
        try:
            User.objects.get(username='tttzhang2000@yahoo.com')
        except User.DoesNotExist:
            setup_test()
            

    @patch.object(CryptoUtility, 'listtransactions_impl')
    @patch.object(axfd_utils.AXFundUtility, 'listtransactions')
    def test_update_account_from_trx(self, mock_listtransactions,mock_listtransactions_impl):
        mock_listtransactions.return_value = test_data1
        mock_listtransactions_impl.return_value = test_data_cny_pass1

        cnywallet = Wallet.objects.get(cryptocurrency__currency_code='CNY')
        axfwallet = Wallet.objects.get(cryptocurrency__currency_code='AXFund')

        operator = User.objects.get(username='admin')

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
            self.fail('Did not find userwallet for yingzhou')
        UserWallet.objects.create(
            user = taozhang,
            wallet = cnywallet,
            wallet_addr = 'PBfMvKuNtJH5yodb13n5FfE7UggNCLh7YP',
            created_by = operator,
            lastupdated_by = operator
        ).save()


        yingzhou = User.objects.get(username='yingzhou')
        print ('yingzhou\'s userid is {0}'.format(yingzhou.id))
        UserWallet.objects.create(
            user = yingzhou,
            wallet = cnywallet,
            wallet_addr = 'PXZCvnATCuvNcJheKsg9LGe5Asf9a5xeEd',
            created_by = operator,
            lastupdated_by = operator
        ).save()

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
        self.assertEqual(100+1-1.2-0.0001, user1_wallet.balance)
        self.assertEqual(1.0 + 2.0 + 1.0 + 0.0001 * 3, user1_wallet.locked_balance)
        self.assertEqual(100+1-1.2-0.0001 - (1.0 + 2.0 + 1.0 + 0.0001 * 3), user1_wallet.available_balance)
        self.assertEqual(round(1.2 - 1.0 - 0.0001, 8), user2_wallet.balance)
        self.assertEqual(round(1.0 + 1.0 + 0.0001 * 2, 8), user2_wallet.locked_balance)
        self.assertEqual(round(1.0 + 1.0 + 0.0001 * 2, 8), user2_wallet.locked_balance)
        try:
            trans_receive_1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63'
            )
            self.assertEqual(2, trans_receive_1.user_wallet.user.id)
            self.assertEqual('PROCESSED', trans_receive_1.status)
            self.assertTrue(math.fabs(trans_receive_1.units - 100.0) < 0.00000001)
            self.assertTrue(math.fabs(trans_receive_1.balance_end - trans_receive_1.balance_begin - 100.0)<0.00000001)
            self.assertEqual(trans_receive_1.locked_balance_begin, trans_receive_1.locked_balance_end)
            self.assertTrue(math.fabs(trans_receive_1.available_to_trade_end - trans_receive_1.available_to_trade_begin - 100.0) < 0.0000001)
            self.assertEqual('CREDIT', trans_receive_1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            self.fail('Could not find userwallettransaction for txid e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63')

        # test pending redeem transaction for user1
        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820',
             transaction_type = 'REDEEM'
            )
            self.assertEqual(2, trans1.user_wallet.user.id)
            self.assertEqual('PENDING', trans1.status)
            self.assertTrue(math.fabs(trans1.units - 1.0) < 0.00000001)
            self.assertEqual(trans1.balance_begin, trans1.balance_end)
            self.assertEqual(trans1.locked_balance_begin + 1.0,  trans1.locked_balance_end)
            self.assertEqual(trans1.available_to_trade_begin - 1.0, trans1.available_to_trade_end)
            self.assertEqual('DEBT', trans1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            self.fail('Could not find redeem userwallettransaction for txid cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820')

        # test pending redeem fee transaction
        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820',
             transaction_type = 'REDEEMFEE'
            )
            self.assertEqual(2, trans1.user_wallet.user.id)
            self.assertEqual('PENDING', trans1.status)
            self.assertTrue(math.fabs(trans1.units - 0.0001) < 0.00000001)
            self.assertEqual(trans1.balance_begin, trans1.balance_end)
            self.assertEqual(trans1.locked_balance_begin + 0.0001,  trans1.locked_balance_end)
            self.assertEqual(trans1.available_to_trade_begin - 0.0001, trans1.available_to_trade_end)
            self.assertEqual('DEBT', trans1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            self.fail('Could not find redeem fee userwallettransaction for txid cbe71c7c0e27227cb2684d8eefcc8a169145fafe9f1c76a7be79de04b7d0c820')

        # test pending redeem transaction for user2
        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='6027fed2199003b34ceb910bd7e1f42914e0c1ea2153d9766e77cfa31cb9255e',
             transaction_type = 'REDEEM'
            )
            self.assertEqual(3, trans1.user_wallet.user.id)
            self.assertEqual('PROCESSED', trans1.status)
            self.assertTrue(math.fabs(trans1.units - 1.0) < 0.00000001)
            self.assertEqual(trans1.balance_begin - 1.0, trans1.balance_end)
            self.assertEqual(trans1.locked_balance_begin,  trans1.locked_balance_end)
            self.assertEqual(trans1.available_to_trade_begin - 1.0, trans1.available_to_trade_end)
            self.assertEqual('DEBT', trans1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            self.fail('Could not find redeem userwallettransaction for txid 6027fed2199003b34ceb910bd7e1f42914e0c1ea2153d9766e77cfa31cb9255e')

        # test pending redeem fee transaction
        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='6027fed2199003b34ceb910bd7e1f42914e0c1ea2153d9766e77cfa31cb9255e',
             transaction_type = 'REDEEMFEE'
            )
            self.assertEqual(3, trans1.user_wallet.user.id)
            self.assertEqual('PROCESSED', trans1.status)
            self.assertTrue(math.fabs(trans1.units - 0.0001) < 0.00000001)
            self.assertEqual(trans1.balance_begin - 0.0001, trans1.balance_end)
            self.assertEqual(trans1.locked_balance_begin,  trans1.locked_balance_end)
            self.assertEqual(trans1.available_to_trade_begin - 0.0001, trans1.available_to_trade_end)
            self.assertEqual('DEBT', trans1.balance_update_type)
        except UserWalletTransaction.DoesNotExist:
            self.fail('Could not find redeem fee userwallettransaction for txid 6027fed2199003b34ceb910bd7e1f42914e0c1ea2153d9766e77cfa31cb9255e')

        #TODO: should test there are 3 pending redeem 0 pending receive trans for user1
        self.assertEqual(3, len(UserWalletTransaction.objects.filter(user_wallet__user__id = 2, user_wallet__wallet__id = axfwallet.id, transaction_type = 'REDEEM', status='PENDING')))
        self.assertEqual(0, len(UserWalletTransaction.objects.filter(user_wallet__user__id = 2, user_wallet__wallet__id = axfwallet.id, transaction_type = 'DEPOSITE', status='PENDING')))
        
        #TODO: should test there are 2 pending redeem 0 pending receive trans for user2
        self.assertEqual(2, len(UserWalletTransaction.objects.filter(user_wallet__user__id = 3, user_wallet__wallet__id = axfwallet.id, transaction_type = 'REDEEM', status='PENDING')))
        self.assertEqual(0, len(UserWalletTransaction.objects.filter(user_wallet__user__id = 2, user_wallet__wallet__id = axfwallet.id, transaction_type = 'DEPOSITE', status='PENDING')))

        # validate the cny transaction
        self.validate_cny_first_run()

        mock_listtransactions.return_value = test_data2
        c = Client()
        response = c.get('/trading/account/cron/update_receive/')
        self.assertEqual(200, response.status_code)

        user1_wallet = UserWallet.objects.get(user__username='taozhang',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        user2_wallet = UserWallet.objects.get(user__username='yingzhou',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        self.assertEqual(100 + 1.0 - 5.2 - 0.0001 * 4, user1_wallet.balance)
        self.assertEqual(0, user1_wallet.locked_balance)
        self.assertEqual(100 + 1.0 - 5.2 - 0.0001 * 4, user1_wallet.available_balance)
        self.assertEqual(1.2 - 1 -1 -1 - 0.0001 * 3, user2_wallet.balance)
        self.assertEqual(0, user2_wallet.locked_balance)
        self.assertEqual(1.2 - 1 -1 -1 - 0.0001 * 3, user2_wallet.available_balance)
        try:
            trans1 = UserWalletTransaction.objects.get(
             reference_wallet_trxId='e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63'
            )
            # test it is the same as the receive trans we read when scan the first time
            # so it approve that nothing happened to this committed trans 
            self.assertEqual(trans_receive_1.user_wallet.user.id, trans1.user_wallet.user.id)
            self.assertEqual(trans_receive_1.status, trans1.status)
            self.assertTrue(trans_receive_1.units, trans1.units)
            self.assertTrue(trans_receive_1.balance_end, trans_receive_1.balance_begin)
            self.assertEqual(trans_receive_1.locked_balance_begin, trans1.locked_balance_end)
            self.assertTrue(trans_receive_1.available_to_trade_end, trans1.available_to_trade_begin)
            self.assertEqual(trans_receive_1.balance_update_type, trans1.balance_update_type)
            self.assertEqual(trans_receive_1.lastupdated_at, trans1.lastupdated_at)
            self.assertEqual(trans_receive_1.lastupdated_by, trans1.lastupdated_by)
        except UserWalletTransaction.DoesNotExist:
            self.fail('Could not find userwallettransaction for txid e8392e991eaa06fc4e37a32c713d69f56b4f14ff823c1adee7b43dc1f98e3b63')

        #Test there is 0 pending transaction
        self.assertEqual(0, len(UserWalletTransaction.objects.filter(user_wallet__user__id = 2, user_wallet__wallet__id = axfwallet.id, status='PENDING')))
        self.assertEqual(0, len(UserWalletTransaction.objects.filter(user_wallet__user__id = 3, user_wallet__wallet__id = axfwallet.id, status='PENDING')))

        # save the trans, prepare to compare it with the trans after another run
        lookup = {}
        all_trans = UserWalletTransaction.objects.all()
        for trans in all_trans:
            lookup[trans.id] = trans

        user_wallet_1 = UserWallet.objects.get(user__id=2, wallet__cryptocurrency__currency_code = 'AXFund')
        user_wallet_2 = UserWallet.objects.get(user__id=3, wallet__cryptocurrency__currency_code = 'AXFund')
        
        # rerun should not make any problem
        mock_listtransactions.return_value = test_data2
        c = Client()
        response = c.get('/trading/account/cron/update_receive/')
        self.assertEqual(200, response.status_code)

        user1_wallet = UserWallet.objects.get(user__username='taozhang',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        user2_wallet = UserWallet.objects.get(user__username='yingzhou',
                  wallet__cryptocurrency__currency_code = 'AXFund')
        self.assertEqual(user_wallet_1.balance, user1_wallet.balance)
        self.assertEqual(user_wallet_1.locked_balance, user1_wallet.locked_balance)
        self.assertEqual(user_wallet_1.available_balance, user1_wallet.available_balance)
        self.assertEqual(user_wallet_1.lastupdated_by, user1_wallet.lastupdated_by)
        self.assertEqual(user_wallet_1.lastupdated_at, user1_wallet.lastupdated_at)
        self.assertEqual(user_wallet_2.balance, user2_wallet.balance)
        self.assertEqual(user_wallet_2.locked_balance, user2_wallet.locked_balance)
        self.assertEqual(user_wallet_2.available_balance, user2_wallet.available_balance)
        self.assertEqual(user_wallet_2.lastupdated_by, user2_wallet.lastupdated_by)
        self.assertEqual(user_wallet_2.lastupdated_at, user2_wallet.lastupdated_at)

        wallet_trans = UserWalletTransaction.objects.all()
        for trans in wallet_trans:
            old_trans = lookup[trans.id]
            self.assertEqual(old_trans.user_wallet.user.id, trans.user_wallet.user.id)
            self.assertEqual(old_trans.lastupdated_at, trans.lastupdated_at)
            self.assertEqual(old_trans.lastupdated_by, trans.lastupdated_by)
            self.assertEqual(old_trans.units, trans.units)
            
    def validate_cny_first_run(self):
        cnywallet = Wallet.objects.get(cryptocurrency__currency_code = 'CNY')
        user1_wallet = UserWallet.objects.get(user__username='taozhang',
                  wallet__cryptocurrency__currency_code = 'CNY')
        user2_wallet = UserWallet.objects.get(user__username='yingzhou',
                  wallet__cryptocurrency__currency_code = 'CNY')
        
        self.assertEqual(100.0, user1_wallet.balance)
        self.assertEqual(0.02 + 0.01, user1_wallet.locked_balance)
        self.assertEqual(100.0 - 0.02 - 0.01, user1_wallet.available_balance)

        user1_wallet_trans = UserWalletTransaction.objects.filter(
            user_wallet__id = user1_wallet.id).order_by('-lastupdated_at')
        self.assertEqual(3, len(user1_wallet_trans))
        debt_count = 0
        for tran in user1_wallet_trans:
            if tran.balance_update_type == 'CREDIT':
                self.assertEqual('PROCESSED', tran.status)
                self.assertEqual(0, tran.balance_begin)

            elif tran.balance_update_type == 'DEBT':
                debt_count = debt_count + 1
                self.assertEqual('PENDING', tran.status)

        self.assertEqual(2, debt_count)
        self.assertEqual(-1.0 - 0.01 + 2.0, user2_wallet.balance)
        self.assertEqual(0, user2_wallet.locked_balance)
        self.assertEqual(-1.0 - 0.01 + 2.0, user2_wallet.available_balance)
        

