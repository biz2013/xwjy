#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json, sys

from unittest.mock import Mock, MagicMock, patch
from django.test import TransactionTestCase
from django.test import Client

from tradeex.models import *
from tradeex.controllers.crypto_utils import *
from trading.models import *

logger = logging.getLogger('tradeex.apitests.test_api_user')

class TestAPIUser(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    @patch.object(CryptoUtility, 'create_wallet_address')
    def test_create_user(self, mock_create_wallet_address):
        mock_create_wallet_address.return_value = 'PEsgfqtqbAp7xE1uRgen89RhmZr4w1YE5W'
        request_json = {}
        request_json['email'] = 'tttzhang2000@gmail.com'
        request_json['payment_account'] = '18600701961'

        try:

            request_str = json.dumps(request_json, ensure_ascii=False)
            print('create user: {0}'.format(request_str))
            c = Client()
            resp = c.post('/setup_create_api_user/', request_str,
                            content_type='application/json')

            self.assertEqual(200, resp.status_code)
            self.assertEqual('OK', resp.content.decode('utf-8').upper())

            user = APIUserAccount.objects.get(user__username='tttzhang2000@gmail.com')
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

        except:
            self.fail('test_create_user encounter exeption {0}'.format(
                sys.exc_info()[0]
            ))


