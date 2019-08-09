#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json, sys

from unittest.mock import Mock, MagicMock, patch
from django.test import TransactionTestCase
from django.test import Client

from trading.controller.coin_utils import CoinUtils

from tradeex.models import *
from trading.models import *

logger = logging.getLogger('tradeex.apitests.test_api_user')

class TestAPIUser(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    @patch.object(CoinUtils, 'create_wallet_address')
    def test_create_user(self, mock_create_wallet_address):
        cny_wallet_address = 'PEsgfqtqbAp7xE1uRgen89RhmZr4w1YE5W'
        mock_create_wallet_address.return_value = cny_wallet_address
        request_json = {}
        request_json['email'] = 'tttzhang2000@gmail.com'
        request_json['payment_account'] = '18600701961'
        request_json['external_cny_addr'] = 'EXTERNAL_CNY_ADDRESS'

        try:
            request_str = json.dumps(request_json, ensure_ascii=False)
            print('create user: {0}'.format(request_str))
            c = Client()
            resp = c.post('/api/v1/apiuser/', request_str,
                            content_type='application/json')

            self.assertEqual(200, resp.status_code)
            resp_str = resp.content.decode('utf-8')
            print('Create user test get response : {0}'.format(resp_str))
            resp_json = json.loads(resp_str)
        
            self.assertEqual('OK', resp_json['result'].upper())

            user_name = 'tttzhang2000@gmail.com'
            user = APIUserAccount.objects.get(user__username = user_name)

            payment = UserPaymentMethod.objects.get(user__id = user.user.id)
            self.assertEqual('18600701961', payment.account_at_provider) 
            self.assertEqual('heepay', payment.provider.code)
            self.assertEqual(0, len(UserWalletTransaction.objects.filter(user_wallet__user__id = user.user.id)))
            axf_wallet = UserWallet.objects.get(wallet__cryptocurrency__currency_code='AXFund', user__id=user.user.id)
            self.assertEqual(0, axf_wallet.balance)
            self.assertEqual(0, axf_wallet.locked_balance)
            self.assertEqual(0, axf_wallet.available_balance)

            cny_wallet = UserWallet.objects.get(wallet__cryptocurrency__currency_code='CNY', user__id=user.user.id)
            self.assertEqual(0, cny_wallet.balance)
            self.assertEqual(0, cny_wallet.locked_balance)
            self.assertEqual(0, cny_wallet.available_balance)
            self.assertEqual(cny_wallet_address, cny_wallet.wallet_addr)

            user_external_addr = UserExternalWalletAddress.objects.get(
                user__id = user.user.id, cryptocurrency__currency_code='CNY',
                address = 'EXTERNAL_CNY_ADDRESS')
            self.assertIsNotNone(user_external_addr)

        except:
            self.fail('test_create_user encounter exeption {0}'.format(
                sys.exc_info()[0]
            ))


