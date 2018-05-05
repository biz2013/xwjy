#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, io, traceback, time, json, copy, math
import logging

from calendar import timegm
import datetime as dt
sys.path.append('../stakingsvc/')
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.test import Client


from unittest.mock import Mock, MagicMock, patch

from tradeapi.data.tradeapirequest import TradeAPIRequest
from tradeex.apitests.tradingutils import *
from tradeex.apitests.util_tests import *
from tradeex.responses.heepaynotify import HeepayNotification
from tradeex.models import *
from trading.models import *
from trading.controller import useraccountinfomanager
import json

# match the hy_bill_no in test data test_heepay_confirm.json
TEST_HY_BILL_NO='180102122300364021000081666'
TEST_HY_APPID = 'hyq17121610000800000911220E16AB0'
TEST_HY_KEY='4AE4583FD4D240559F80ED39'
TEST_BUYER_ACCOUNT='13910978598'
TEST_API_USER1_APPKEY = 'TRADEEX_USER1_APP_KEY_1234567890ABCDE'
TEST_API_USER1_SECRET='TRADEEX_USER1_APP_SECRET'
heepay_reponse_template = json.load(io.open('trading/tests/data/heepay_return_success.json', 'r', encoding='utf-8'))

logger = logging.getLogger('tradeex.apitests.test_trading')

#mock function
def send_buy_apply_request_side_effect(payload):
    json_payload = json.loads(payload)
    biz_content = json.loads(json_payload['biz_content'])
    key_values = {}
    key_values['app_id'] = json_payload['app_id']
    key_values['out_trade_no'] = biz_content['out_trade_no']
    key_values['subject'] = biz_content['subject'] if 'subject' in json_payload else ''
    key_values['total_fee'] = biz_content['total_fee']
    key_values['hy_bill_no'] = TEST_HY_BILL_NO

    buy_order = Order.objects.get(pk=biz_content['out_trade_no'])
    try:
        seller_account = UserPaymentMethod.objects.get(
            user__id=buy_order.reference_order.user.id,
            provider__code = 'heepay')
    except UserPaymentMethod.DoesNotExist:
        logger.error('send_buy_apply_request_side_effec(): cannot find the payment account of the seller that test trans {0} try to buy from'.format(api_trans.api_out_trade_no))
        return 500, 'error', '{}'
    except UserPaymentMethod.MultipleObjectsReturned:
        logger.error('System find more than one payment account of the seller that test trans {0} try to buy from'.format(api_trans.api_out_trade_no))
        return 500, 'error', '{}'

    key_values['to_account'] = seller_account.account_at_provider
    key_values['to_account'] = TEST_BUYER_ACCOUNT
    output_data = jinja2_render('tradeex/apitests/data/heepay_response_template.j2', key_values)
    output_json = json.loads(output_data)
    sign = sign_test_json(output_json, TEST_HY_KEY)
    output_json['sign'] = sign
    return 200, 'Ok', json.dumps(output_json, ensure_ascii=False)

# Create your tests here.
class TestPrepurchase(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def setUp(self):
        pass

    def validate_success_prepurchase_response(self, resp_json):
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        return True

    def test_purchase_user_not_found_api_key(self):
        request = TradeAPIRequest('api_key_not_exist', 'secrete_not_exist',
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


    def get_api_trans(self, target_out_trade_no):
        try:
            return APIUserTransaction.objects.get(api_out_trade_no = target_out_trade_no)
        except APIUserTransaction.DoesNotExist:
            self.fail('System cannot find the api trans for out_trade_no {0}'.format(target_out_trade_no))
        except APIUserTransaction.MultipleObjectsReturned:
            self.fail('System find more than one api trans for out_trade_no {0}'.format(target_out_trade_no))

    def validate_api_trans_before_confirm(self, api_trans, expected_app_id, 
            expected_secret_key, expected_out_trade_no, **kwargs):
        self.assertEqual(expected_app_id, api_trans.api_user.apiKey, 'api_trans api_key is not expected')
        self.assertEqual(expected_secret_key, api_trans.api_user.secretKey, 'api_trans secret_key is not expected')
        self.assertEqual(expected_out_trade_no, api_trans.api_out_trade_no, 'api_trans out trade no is not expected')
        if kwargs:
            for key, value in kwargs.items():
                if key == 'expected_subject':
                    self.assertEqual(value, api_trans.subject, 'api_trans subject is not expected')
                elif key == 'expected_attach':
                    self.assertEqual(value, api_trans.attach, 'api_trans attach is not expected')
                elif key == 'expected_total_fee':
                    self.assertEqual(value, api_trans.total_fee, 'api_trans total_fee is not expected')
                elif key == 'expected_return_url':
                    self.assertEqual(value, api_trans.return_url, 'api_trans return_url is not expected')
                elif key == 'expected_notify_url':
                    self.assertEqual(value, api_trans.notify_url, 'api_trans notify_url is not expected')

    
    def create_heepay_confirm(self, template_path, api_trans, trade_status, payment_time):
        key_values = {}
        key_values['app_id'] = TEST_HY_APPID
        key_values['out_trade_no'] = api_trans.reference_order.order_id
        key_values['subject'] = api_trans.subject if api_trans.subject else ''
        key_values['total_fee'] = api_trans.total_fee
        key_values['hy_bill_no'] = TEST_HY_BILL_NO
        key_values['trade_status'] = trade_status
        key_values['from_account'] = TEST_BUYER_ACCOUNT
        try:
            seller_account = UserPaymentMethod.objects.get(
                user__id=api_trans.reference_order.reference_order.user.id,
                provider__code = 'heepay')
        except UserPaymentMethod.DoesNotExist:
            self.fail('System cannot find the payment account of the seller that test trans {0} try to buy from'.format(api_trans.api_out_trade_no))
        except UserPaymentMethod.MultipleObjectsReturned:
            self.fail('System find more than one payment account of the seller that test trans {0} try to buy from'.format(api_trans.api_out_trade_no))

        key_values['to_account'] = seller_account.account_at_provider
        key_values['payment_time'] = payment_time
        output_data = jinja2_render('tradeex/apitests/data/heepay_confirm_template.j2', key_values)
        output_json = json.loads(output_data)
        logger.debug('create_heepay_confirm(): about to sign heepay confirmation')
        sign = sign_test_json(output_json, TEST_HY_KEY)
        output_json['sign'] = sign
        # TODO: this is to validate the sign
        #HeepayNotification.parseFromJson(output_json, api_trans.api_user.secretKey, False)
        return output_json

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

        api_users = APIUserAccount.objects.all()
        self.assertEqual(1, len(api_users),'there should be one api user')
        for api_user in api_users:
            print('Before test, found user with apiKey {0}'.format(api_user.apiKey))
        self.create_fitting_order(62)

        # these are the app_id and secret from fixture apiuseraccount        
        # TODO: validate this is tradeex_api_user1
        app_id = TEST_API_USER1_APPKEY
        secret_key = TEST_API_USER1_SECRET
        test_out_trade_no = 'order_match'
        test_purchase_amount = 62
        test_user_heepay_from_account = '12738456'
        test_attach = 'userid:1'
        test_subject = '人民币充值成功测试'
        test_notify_url = 'http://testurl'
        test_return_url = 'http://testurl'
        request = TradeAPIRequest(app_id, secret_key,
                test_out_trade_no, # out_trade_no
                test_purchase_amount, # total fee
                10, # expire_minute
                'heepay', 
                test_user_heepay_from_account,
                '127.0.0.1', #client ip
                attach=test_attach,
                subject=test_subject,
                notify_url=test_notify_url,
                return_url=test_return_url)
        c = Client()
        request_str = request.getPayload()
        print('test_purchase_order_succeed(): send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')
        print('response is {0}'.format(json.dumps(json.loads(response.content), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content)
        self.assertEqual(resp_json['return_code'], 'SUCCESS')

        api_trans = self.get_api_trans(test_out_trade_no)
        self.validate_api_trans_before_confirm(api_trans, app_id, 
            secret_key, test_out_trade_no, expected_total_fee=test_purchase_amount,
            expected_from_account=test_user_heepay_from_account,
            expected_subject = test_subject, expected_attach = test_attach,
            expected_return_url = test_return_url, 
            expected_notify_url = test_notify_url)
        
        logger.info('finish issue purchase request, about to test receiving heepay notification')

        #NOTE: the trade status is case-sensitive thing
        heepay_confirm = self.create_heepay_confirm('tradeex/apitests/data/heepay_confirm_template.j2', 
            api_trans, 'Success', timegm(dt.datetime.utcnow().utctimetuple()))
        self.assertTrue(heepay_confirm, 'There is problem when the heepay confirmation data')
        request_str  =json.dumps(heepay_confirm, ensure_ascii=False)
        print('send heepay confirmation request {0}'.format(request_str))
        
        c1 = Client()
        response = c1.post('/trading/heepay/confirm_payment/', request_str,
            content_type='application/json')
        
        #TODO: test sending coin is execute
        #TODO: test notification is sent
        #TODO: test the notification is correct
        self.assertEqual('OK', response.content.decode('utf-8'), "The response to the payment confirmation should be OK")


         

        
