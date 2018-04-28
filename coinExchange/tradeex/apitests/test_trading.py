#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, io, traceback, time, json, copy, math
sys.path.append('../stakingsvc/')
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.test import Client


from unittest.mock import Mock, MagicMock, patch

from tradeapi.data.traderequest import PurchaseAPIRequest
from tradeex.apitests.tradingutils import *
from tradeex.responses.heepaynotify import HeepayNotification
from trading.models import *
from trading.controller import useraccountinfomanager
import json

# match the hy_bill_no in test data test_heepay_confirm.json
TEST_HY_BILL_NO='180102122300364021000081666'

heepay_reponse_template = json.load(io.open('trading/tests/data/heepay_return_success.json', 'r', encoding='utf-8'))

#mock function
def send_buy_apply_request_side_effect(payload):
    json_payload = json.loads(payload)
    json_response = copy.copy(heepay_reponse_template)
    print('copied response template is {0}'.format(json.dumps(json_response)))
    biz_content = json.loads(json_payload['biz_content'])
    print('biz_content json is {0}'.format(json.dumps(biz_content)))
    json_response['out_trade_no'] = biz_content['out_trade_no']
    json_response['hy_bill_no'] = TEST_HY_BILL_NO
    json_response['to_account'] = '15811302702'
    print('copied and templated response is {0}'.format(json.dumps(json_response)))
    return 200, 'Ok', json.dumps(json_response)

# Create your tests here.
class TestPrepurchase(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def setUp(self):
        pass

    def validate_success_prepurchase_response(self, resp_json):
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        return True

    def test_purchase_user_not_found_api_key(self):
        request = PurchaseAPIRequest('api_key_not_exist', 'secrete_not_exist',
                '20180320222600_123', # order id
                0.05, # total fee
                10, # expire_minute
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], '系统错误:通知系统服务')
        #TODO: show user not found?

    def validate_user_info(self, username):
        wallet_count = len(UserWallet.objects.all())
        self.assertTrue(wallet_count==7, "There should be 7 user wallets but have {0}".format(wallet_count))
        for wallet in UserWallet.objects.all():
            print('wallet {0}, user {1} {2}, balance {3}, address {4}, coin {5}'.format(
                wallet.id, wallet.user.id, wallet.user.username, wallet.balance, wallet.wallet_addr,
                wallet.wallet.cryptocurrency.currency_code
            ))

        useraccountInfo = useraccountinfomanager.get_user_accountInfo(User.objects.get(username=username),'AXFund')
        self.assertTrue(useraccountInfo.balance > 0, "the balance of {0} should be larger than 0".format(username))
        self.assertTrue(useraccountInfo.available_balance > 0, "the available balance of {0} should be larger than 0".format(username))
        self.assertTrue(useraccountInfo.paymentmethods, "user {0} should have payment info".format(username))
        self.assertEqual(1, len(useraccountInfo.paymentmethods), "There should be 1 payment method for user {0}".format(username))
        self.assertEqual('heepay', useraccountInfo.paymentmethods[0].provider_code, "user {0}\'s payment method should come from heepay".format(username))
        self.assertTrue(useraccountInfo.paymentmethods[0].account_at_provider, "User {0} should have account at heepay".format(username))

    def create_no_fitting_order(self):
        print('create_no_fitting_order()')
        self.validate_user_info('tttzhang2000@yahoo.com')
        resp = create_axfund_sell_order('tttzhang2000@yahoo.com', 'user@123', 100, 0.5, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 100 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content,'Create order of 100 units hit issue')

        self.validate_user_info('yingzhou61@yahoo.ca')
        resp = create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 200, 0.3, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 200 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 200 units hit issue')

        for order in Order.objects.all():
            print('order {0} order_type {1} sub_type {2}'.format(order.order_id, order.order_type, order.sub_type))

    def create_fitting_order(self, amount):
        print('create_fitting_order({0})'.format(amount))
        self.validate_user_info('tttzhang2000@yahoo.com')
        resp = create_axfund_sell_order('tttzhang2000@yahoo.com', 'user@123', 200, 0.5, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 200 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content,'Create order of 200*0.5 units hit issue')

        self.validate_user_info('yingzhou61@yahoo.ca')
        resp = create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 200, 0.4, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 200*0.4 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 200*0.4 units hit issue')

        resp = create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 150, 0.4, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 150*0.4 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 150*0.4 units hit issue')

        resp = create_axfund_sell_order('tttzhang2000@yahoo.com', 'user@123', 156, 0.4, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 156*0.4 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content,'Create order of 156*0.5 units hit issue')

        for order in Order.objects.all():
            print('matching order {0} order_type {1} sub_type {2}'.format(order.order_id, order.order_type, order.sub_type))

    def test_purchase_no_fitting_order(self):
        self.create_no_fitting_order()
        request = PurchaseAPIRequest('hyq17121610000800000911220E16AB0', '4AE4583FD4D240559F80ED39',
                'order_no_order', # order id
                620, # total fee
                10, # expire_minute
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')

        print('response is {0}'.format(json.dumps(json.loads(response.content), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], '数据错误:通知系统服务')
        #TODO: show user not found?
        
    def test_purchase_order_succeed_bad_payment_acct(self):
        self.create_fitting_order(62)
        # update the tttzhang2000@yahoo.com's heepay account into bad account, since this user's order
        # is selected for the purchase, this update will failed the test.
        updated = UserPaymentMethod.objects.filter(user__username='tttzhang2000@yahoo.com').filter(provider__code='heepay').update(account_at_provider='bad_user_account')
        self.assertTrue(updated, 'change tttzhang2000@yahoo.com\'s heepay account should be successful')
        request = PurchaseAPIRequest('hyq17121610000800000911220E16AB0', '4AE4583FD4D240559F80ED39',
                'order_match', # order id
                62, # total fee
                10, # expire_minute
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')
        self.assertTrue(UserPaymentMethod.objects.filter(user__username='tttzhang2000@yahoo.com').filter(provider__code='heepay').update(account_at_provider='18600701961'),
              'recover tttzhang2000@yahoo.com\'s heepay account should be successful')

        print('response is {0}'.format(json.dumps(json.loads(response.content), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], "收钱方账号不存在")


    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_request_side_effect)
    def test_purchase_order_succeed(self,send_buy_apply_request_function):
        self.create_fitting_order(62)
        app_id = 'hyq17121610000800000911220E16AB0'
        secret_key = '4AE4583FD4D240559F80ED39'
        request = PurchaseAPIRequest(app_id, secret_key,
                'order_match', # order id
                62, # total fee
                10, # expire_minute
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('test_purchase_order_succeed(): send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')
        print('response is {0}'.format(json.dumps(json.loads(response.content), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['return_code'], 'SUCCESS')

        heepay_confirm = json.load(io.open('trading/tests/data/test_heepay_confirm.json', 'r', encoding='utf-8'))
        heepay_confirm['app_id'] = app_id
        heepay_notify = HeepayNotification.parseFromJson(heepay_confirm, secret_key)
        heepay_confirm['sign'] = heepay_notify.sign
        request_str  =json.dumps(heepay_confirm, ensure_ascii=False)
        print('send heepay confirmation request {0}'.format(request_str))
        
        c1 = Client()
        response = c1.post('/tradeex/heepayreply/', request_str,
            content_type='application/json')
        
        self.assertEqual('OK', response.content, "The response to the payment confirmation should be OK")


        
