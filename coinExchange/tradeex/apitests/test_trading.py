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

from tradeex.data.tradeapirequest import TradeAPIRequest
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
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
TEST_SELLER_ACCOUNT='api_user2_12345'
TEST_API_USER1_APPKEY = 'TRADEEX_USER1_APP_KEY_1234567890ABCDE'
TEST_API_USER2_APPKEY = 'TRADEEX_USER2_APP_KEY_SELLER'
TEST_API_USER1_SECRET='TRADEEX_USER1_APP_SECRET'
TEST_API_USER2_SECRET='TRADEEX_USER2_API_SECRET'
TEST_PURCHASE_AMOUNT = 62
TEST_REDEEM_AMOUNT = 100
TEST_CNY_ADDR="TRADDEX_USER1_EXTERNAL_TEST_ADDR"
TEST_CRYPTO_SEND_COMMENT = ""
TEST_NOTIFY_URL = "http://testurl/"

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
    buyer_account = TEST_BUYER_ACCOUNT
    
    #TODO: ??? Does Heepay purchase request need from account?
    """
    try:
        buyer_account = UserPaymentMethod.objects.get(
            user__id=buy_order.user.id,
            provider__code = 'heepay').account_at_provider
    except UserPaymentMethod.DoesNotExist:
        logger.error('send_buy_apply_request_side_effec(): cannot find the payment account of the buyer that test trans {0} try to sell'.format(biz_content['out_trade_no']))
        return 500, 'error', '{}'
    except UserPaymentMethod.MultipleObjectsReturned:
        logger.error('System find more than one payment account of the buyer that test trans {0} try to sell'.format(biz_content['out_trade_no']))
        return 500, 'error', '{}'
    """

    #TODO: if trans state the buyer account
    try:
        seller_account = UserPaymentMethod.objects.get(
            user__id=buy_order.reference_order.user.id,
            provider__code = 'heepay').account_at_provider
    except UserPaymentMethod.DoesNotExist:
        logger.error('send_buy_apply_request_side_effec(): cannot find the payment account of the seller that test trans {0} try to buy from'.format(biz_content['out_trade_no']))
        return 500, 'error', '{}'
    except UserPaymentMethod.MultipleObjectsReturned:
        logger.error('System find more than one payment account of the seller that test trans {0} try to buy from'.format(biz_content['out_trade_no']))
        return 500, 'error', '{}'

    key_values['from_account'] = buyer_account
    key_values['to_account'] = seller_account
    output_data = jinja2_render('tradeex/apitests/data/heepay_response_template.j2', key_values)
    output_json = json.loads(output_data)
    sign = sign_test_json(output_json, TEST_HY_KEY)
    output_json['sign'] = sign
    return 200, 'Ok', json.dumps(output_json, ensure_ascii=False)

#mock function
def send_buy_apply_for_redeem_side_effect(payload):
    json_payload = json.loads(payload)
    biz_content = json.loads(json_payload['biz_content'])
    key_values = {}
    key_values['app_id'] = json_payload['app_id']
    key_values['out_trade_no'] = biz_content['out_trade_no']
    key_values['subject'] = biz_content['subject'] if 'subject' in json_payload else ''
    key_values['total_fee'] = biz_content['total_fee']
    key_values['hy_bill_no'] = TEST_HY_BILL_NO


    #key_values['from_account'] = seller_account.account_at_provider
    key_values['to_account'] = TEST_SELLER_ACCOUNT
    output_data = jinja2_render('tradeex/apitests/data/heepay_response_template.j2', key_values)
    output_json = json.loads(output_data)
    sign = sign_test_json(output_json, TEST_HY_KEY)
    output_json['sign'] = sign
    return 200, 'Ok', json.dumps(output_json, ensure_ascii=False)


#mock function
def send_fund_for_purchase_test(target_addr, amount, comment):
    logger.debug('come to the mock of send fund()')
    TestCase().assertEqual(TEST_CNY_ADDR, target_addr, "System should send purchase CNY to {0}".format(TEST_CNY_ADDR) )
    amt_in_cent = int(amount*100)
    TestCase().assertEqual(TEST_PURCHASE_AMOUNT, amt_in_cent, "System should come to send {0} unit of CNY".format(amt_in_cent))
    TestCase().assertEqual(TEST_CRYPTO_SEND_COMMENT, comment, "System expects comment like '{0}'".format(TEST_CRYPTO_SEND_COMMENT))
    return { 'txid': 'TEST_TXID'}

#mock function
def send_json_request_for_purchase_test(payload, trackId='', response_format='json'):
    logger.debug('come to mock to send notification back to buyer')
    TestCase().assertEqual('text', response_format, "System ask for text response")
    #TODO: more validation on payload
    return 'OK'

#mock function
def send_json_request_for_redeem_test(payload, trackId='', response_format='json'):
    logger.debug('come to mock to send notification back to buyer')
    TestCase().assertEqual('text', response_format, "System ask for text response")
    #TODO: more validation on payload
    return 'OK'

# Create your tests here.
class TestPrepurchase(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def setUp(self):
        pass


    def validate_success_prepurchase_response(self, resp_json):
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        return True

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
        
        # for purchase transaction, the transaction's reference order is the purchase order
        if api_trans.action == 'wallet.trade.buy':
            purchase_order = api_trans.reference_order
        # for redeem transaction, we need to get the purchase order of the sell order that 
        # the transaction put forwarder
        elif api_trans.action == 'wallet.trade.sell':
            purchase_order = Order.objects.get(reference_order__order_id=api_trans.reference_order.order_id, order_type='BUY')
        
        key_values['out_trade_no'] = purchase_order.order_id
        key_values['subject'] = api_trans.subject if api_trans.subject else ''
        key_values['total_fee'] = api_trans.total_fee
        key_values['hy_bill_no'] = TEST_HY_BILL_NO
        key_values['trade_status'] = trade_status

        # Let's assume there's no from account for heepay
        #key_values['from_account'] = TEST_BUYER_ACCOUNT
        try:
            seller_account = UserPaymentMethod.objects.get(
                user__id=purchase_order.reference_order.user.id,
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

    def test_purchase_bad_user_account(self):
        self.create_no_fitting_order()
        request = TradeAPIRequest(
                'wallet.trade.buy',
                'user_does_not_exist',
                'secret_key_not_exist',
                'order_no_order', # order id
                None, # trx_id
                620, # total fee
                10, # expire_minute
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                subject='人民币充值测试-账号不存在',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')

        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], '未找到您的账户:通知系统服务')
        #TODO: show user not found?

    def test_purchase_no_fitting_order(self):
        self.create_no_fitting_order()
        request = TradeAPIRequest(
                'wallet.trade.buy',
                TEST_API_USER1_APPKEY,
                TEST_API_USER1_SECRET,
                'order_no_order', # order id
                None, # trx_id
                620, # total fee
                10, # expire_minute
                'heepay', '12738456',
                '127.0.0.1', #client ip
                attach='userid:1',
                subject='人民币充值测试-没有合适卖单',
                notify_url='http://testurl',
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')

        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], '数据错误:通知系统服务')
        #TODO: show user not found?
        
    def test_purchase_order_succeed_bad_payment_acct(self):
        self.create_fitting_order(62)
        # update the tttzhang2000@yahoo.com's heepay account into bad account, since this user's order
        # is selected for the purchase, this update will failed the test.
        updated = UserPaymentMethod.objects.filter(user__username='tttzhang2000@yahoo.com').filter(provider__code='heepay').update(account_at_provider='bad_user_account')
        self.assertTrue(updated, 'change tttzhang2000@yahoo.com\'s heepay account should be successful')
        request = TradeAPIRequest(
                'wallet.trade.buy',
                TEST_API_USER1_APPKEY,
                TEST_API_USER1_SECRET,
                'order_match', # order id
                None, # trx _id
                62, # total fee
                10, # expire_minute
                'heepay', 'not_exist',
                '127.0.0.1', #client ip
                attach='userid:1',
                subject='人民币充值测试-没有付款账号',
                notify_url=TEST_NOTIFY_URL,
                return_url='http://retururl')
        c = Client()
        request_str = request.getPayload()
        print('send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')
        self.assertTrue(UserPaymentMethod.objects.filter(user__username='tttzhang2000@yahoo.com').filter(provider__code='heepay').update(account_at_provider='18600701961'),
              'recover tttzhang2000@yahoo.com\'s heepay account should be successful')

        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], "收钱方账号不存在")


    @patch('tradeex.controllers.crypto_utils.CryptoUtility.send_fund', side_effect=send_fund_for_purchase_test)
    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_request_side_effect)
    @patch('tradeex.client.apiclient.APIClient.send_json_request', side_effect=send_json_request_for_purchase_test)
    def test_purchase_order_succeed(self,send_fund_function,
            send_buy_apply_request_function,
            send_json_request_function):

        # create test sell orders
        self.create_fitting_order(62)

        # these are the app_id and secret from fixture apiuseraccount        
        # TODO: validate this is tradeex_api_user1
        app_id = TEST_API_USER1_APPKEY
        secret_key = TEST_API_USER1_SECRET
        test_out_trade_no = 'order_to_purchase'
        test_purchase_amount = TEST_PURCHASE_AMOUNT
        test_user_heepay_from_account = '12738456'
        test_attach = 'userid:1'
        test_subject = '人民币充值成功测试'
        test_notify_url = 'http://testurl'
        test_return_url = 'http://testurl'
        request = TradeAPIRequest(
                'wallet.trade.buy',
                app_id, secret_key,
                test_out_trade_no, # out_trade_no
                total_fee=test_purchase_amount, # total fee
                expire_minute=10, # expire_minute
                payment_provider='heepay', 
                payment_account=test_user_heepay_from_account,
                client_ip='127.0.0.1', #client ip
                attach=test_attach,
                subject=test_subject,
                notify_url=test_notify_url,
                return_url=test_return_url)
        c = Client()
        request_str = request.getPayload()
        print('test_purchase_order_succeed(): send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')
        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'SUCCESS')

        api_trans = self.get_api_trans(test_out_trade_no)
        global TEST_CRYPTO_SEND_COMMENT
        TEST_CRYPTO_SEND_COMMENT = 'userId:{3},amount:{0},trxId:{1},out_trade_no:{2}'.format(
            float(TEST_PURCHASE_AMOUNT)/100.0, api_trans.transactionId, 
            api_trans.api_out_trade_no, api_trans.api_user.user.id )
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

    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_for_redeem_side_effect)
    @patch('tradeex.client.apiclient.APIClient.send_json_request', 
            side_effect=send_json_request_for_redeem_test)
    def test_redeem_order_succeed(self,send_buy_apply_request_function,
            send_json_request_function):
        try:
            api_users = APIUserAccount.objects.get(pk=TEST_API_USER2_APPKEY)
        except:
            self.fail('test_purchase_order_succeed() did not find api user {0}'.format(
                TEST_API_USER2_APPKEY
            ))

        # these are the app_id and secret from fixture apiuseraccount        
        # TODO: validate this is tradeex_api_user1
        app_id = TEST_API_USER2_APPKEY
        secret_key = TEST_API_USER2_SECRET
        test_out_trade_no = 'order_to_redeem'
        test_purchase_amount = TEST_REDEEM_AMOUNT
        test_user_heepay_to_account = '12738456'
        test_attach = 'userid:1'
        test_subject = '人民币提现成功测试'
        test_notify_url = 'http://testurl'
        test_return_url = 'http://testurl'
        request = TradeAPIRequest(
                'wallet.trade.sell',
                app_id, secret_key,
                test_out_trade_no, # out_trade_no
                total_fee=test_purchase_amount, # total fee
                expire_minute=10, # expire_minute
                payment_provider='heepay', 
                payment_account=test_user_heepay_to_account,
                client_ip='127.0.0.1', #client ip
                attach=test_attach,
                subject=test_subject,
                notify_url=test_notify_url,
                return_url=test_return_url)
        c = Client()
        request_str = request.getPayload()
        print('test_purchase_order_succeed(): send request {0}'.format(request_str))
        response = c.post('/tradeex/selltoken/', request_str,
                          content_type='application/json')
        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        self.assertEqual(resp_json['return_code'], 'SUCCESS')

        c2 = Client()
        c.login(username='tttzhang2000@yahoo.com', password='user@123')

        purchase_request = {}
        api_trans = APIUserTransaction.objects.get(api_out_trade_no=test_out_trade_no)
        purchase_request['reference_order_id'] = api_trans.reference_order.order_id
        purchase_request['owner_user_id'] = api_trans.reference_order.user.id
        purchase_request['quantity']=api_trans.reference_order.units
        purchase_request['unit_price'] = api_trans.reference_order.unit_price
        logger.debug('test_redeem_order_succeed(): seller payment provider {0}'.format(
            api_trans.payment_provider
        ))
        purchase_request['seller_payment_provider']=api_trans.payment_provider.code
        purchase_request['crypto'] = 'AXFund'
        purchase_request['total_amount'] = api_trans.reference_order.total_amount
        #TODO: why purchase donot set unit_price currency
        purchase_response = c.post('/trading/purchase/createorder2/', purchase_request, follow=True)
        print('------------------------------')
        print(purchase_response.content.decode('utf-8'))

        api_trans = self.get_api_trans(test_out_trade_no)
        self.validate_api_trans_before_confirm(api_trans, app_id, 
            secret_key, test_out_trade_no, expected_total_fee=test_purchase_amount,
            expected_subject = test_subject, expected_attach = test_attach,
            expected_return_url = test_return_url, 
            expected_notify_url = test_notify_url)
        
        logger.info('finish issue redeem request. About simulate buyer purchase')

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

    @patch('tradeex.controllers.crypto_utils.CryptoUtility.send_fund', side_effect=send_fund_for_purchase_test)
    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_request_side_effect)
    @patch('tradeex.client.apiclient.APIClient.send_json_request', side_effect=send_json_request_for_purchase_test)
    def test_status_query(self,send_fund_function,
            send_buy_apply_request_function,
            send_json_request_function):

        try:
            api_users = APIUserAccount.objects.get(pk=TEST_API_USER1_APPKEY)
        except:
            self.fail('test_purchase_order_succeed() did not find api user {0}'.format(
                TEST_API_USER1_APPKEY
            ))

        # create test sell orders
        self.create_fitting_order(62)

        # these are the app_id and secret from fixture apiuseraccount        
        # TODO: validate this is tradeex_api_user1
        app_id = TEST_API_USER1_APPKEY
        secret_key = TEST_API_USER1_SECRET
        test_out_trade_no = 'order_to_purchase'
        test_purchase_amount = TEST_PURCHASE_AMOUNT
        test_user_heepay_from_account = '12738456'
        test_attach = 'userid:1'
        test_subject = '人民币充值成功测试'
        test_notify_url = 'http://testurl'
        test_return_url = 'http://testurl'
        request = TradeAPIRequest(
                'wallet.trade.buy',
                app_id, secret_key,
                test_out_trade_no, # out_trade_no
                total_fee= test_purchase_amount, # total fee
                expire_minute = 10, # expire_minute
                payment_provider = 'heepay', 
                payment_account = test_user_heepay_from_account,
                client_ip = '127.0.0.1', #client ip
                attach=test_attach,
                subject=test_subject,
                notify_url=test_notify_url,
                return_url=test_return_url,
                timestamp = timegm(dt.datetime.utcnow().utctimetuple()))
        c = Client()
        request_str = request.getPayload()
        print('test_purchase_order_succeed(): send request {0}'.format(request_str))
        response = c.post('/tradeex/purchasetoken/', request_str,
                          content_type='application/json')

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'SUCCESS')

        api_trans = self.get_api_trans(test_out_trade_no)        
        logger.info('finish issue purchase request, about to query the status')
        query_request = TradeAPIRequest(
            "wallet.trade.query",
            app_id, secret_key,
            test_out_trade_no, # out_trade_no    
            trx_bill_no=api_trans.transactionId,
            timestamp = timegm(dt.datetime.utcnow().utctimetuple())
        )

        c_query = Client()
        request_str = query_request.getPayload()
        print('test_status_query(): send request right after purchase command {0}'.format(request_str))
        response = c_query.post('/tradeex/checkorderstatus/', request_str,
                          content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        print('Status right after purchase command is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))
        self.assertEqual('SUCCESS', resp_json['return_code'], 'The query should return SUCCCESS')
        self.assertEqual('InProgress', resp_json['trade_status'], 'The transaction should be in progress')
    
        logger.info('about to test receiving heepay notification')
        global TEST_CRYPTO_SEND_COMMENT
        TEST_CRYPTO_SEND_COMMENT = 'userId:{3},amount:{0},trxId:{1},out_trade_no:{2}'.format(
            float(TEST_PURCHASE_AMOUNT)/100.0, api_trans.transactionId, 
            api_trans.api_out_trade_no, api_trans.api_user.user.id)

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
        c_query = Client()
        request_str = query_request.getPayload()
        print('test_status_query(): send request right after purchase command {0}'.format(request_str))
        response = c_query.post('/tradeex/checkorderstatus/', request_str,
                          content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        print('Status right after purchase command is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))
        self.assertEqual('SUCCESS', resp_json['return_code'], 'The query should return SUCCCESS')
        self.assertEqual('Success', resp_json['trade_status'], 'The transaction should be in progress')
        
