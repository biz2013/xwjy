#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, io, traceback, time, json, copy, math
import logging

from calendar import timegm
import datetime as dt
from datetime import timedelta
sys.path.append('../stakingsvc/')
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.test import Client


from unittest.mock import Mock, MagicMock, patch

from tradeex.data.tradeapirequest import TradeAPIRequest
from tradeex.data.api_const import *
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
from tradeex.apitests.tradingutils import *
from tradeex.apitests.util_tests import *
from tradeex.responses.heepaynotify import HeepayNotification
from tradeex.controllers.crypto_utils import *
from tradeex.models import *
from trading.models import *
from trading.controller import useraccountinfomanager, ordermanager
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

TEST_OUT_TRADE_NO_REDEEM = 'order_to_redeem'

TEST_PURCHASE_AMOUNT = 6200
TEST_REDEEM_AMOUNT = 5000
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
    key_values['subject'] = biz_content['subject']
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
    key_values['subject'] = biz_content['subject']
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
def unlock_wallet_for_purchase_test(timeout_in_sec):
    pass

#mock function
def send_fund_for_purchase_test(target_addr, amount, comment):
    logger.info('send_fund_for_purchase_test():come to the mock of send fund()')
    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& send_fund_for_purchase_test &&&&&&&&&&&&&&&&&&&&&&&&')
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
class TestTradingAPI(TransactionTestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def setUp(self):
        pass


    def validate_success_prepurchase_response(self, resp_json):
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        return True

    def validate_user_info(self, username):
        useraccountInfo = useraccountinfomanager.get_user_accountInfo(User.objects.get(username=username),'AXFund')
        self.assertTrue(useraccountInfo.balance > 0, "the balance of {0} should be larger than 0".format(username))
        self.assertTrue(useraccountInfo.available_balance > 0, "the available balance of {0} should be larger than 0".format(username))
        self.assertTrue(useraccountInfo.paymentmethods, "user {0} should have payment info".format(username))
        self.assertEqual(1, len(useraccountInfo.paymentmethods), "There should be 1 payment method for user {0}".format(username))
        self.assertEqual('heepay', useraccountInfo.paymentmethods[0].provider_code, "user {0}\'s payment method should come from heepay".format(username))
        self.assertTrue(useraccountInfo.paymentmethods[0].account_at_provider, "User {0} should have account at heepay".format(username))

    def validate_purchase_first_state(self,request_obj, resp_json):
        api_trans = None
        try:
            api_trans = APIUserTransaction.objects.get(api_out_trade_no=TEST_OUT_TRADE_NO_REDEEM)
        except APIUserTransaction.DoesNotExist:
            self.fail('There should be one api user transaction record for {0} API call'.format(TEST_OUT_TRADE_NO_REDEEM))
        except APIUserTransaction.MultipleObjectsReturned:
            self.fail('There should not be more than one api user transaction record for {0} API call'.format(TEST_OUT_TRADE_NO_REDEEM))

        self.assertEqual(api_trans.action, API_METHOD_REDEEM)
        self.assertTrue(api_trans.reference_order)
        self.assertEqual('SELL', api_trans.reference_order.order_type)
        self.assertEqual('ALL_OR_NOTHING', api_trans.reference_order.sub_type)
        self.assertEqual('API', api_trans.reference_order.order_source)
        self.assertTrue(math.fabs(round(request_obj.total_fee/100.0, 8) - api_trans.reference_order.total_amount) < 0.00000001)

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

        show_order_overview()

    def create_fitting_order(self, amount):
        print('create_fitting_order({0})'.format(amount))
        self.validate_user_info('tttzhang2000@yahoo.com')
        resp = create_axfund_sell_order('tttzhang2000@yahoo.com', 'user@123', 200, 0.5, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 200 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content,'Create order of 200*0.5 units hit issue')

        resp = create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 156, 0.4, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 150*0.4 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 150*0.4 units hit issue')

        resp = create_axfund_sell_order('tttzhang2000@yahoo.com', 'user@123', 156, 0.4, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 156*0.4 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content,'Create order of 156*0.5 units hit issue')        

        self.validate_user_info('yingzhou61@yahoo.ca')
        resp = create_axfund_sell_order('yingzhou61@yahoo.ca', 'user@123', 150, 0.4, 'CNY')
        self.assertEqual(200, resp.status_code, "Create order of 200*0.4 units should return 200")
        self.assertFalse('系统遇到问题'.encode('utf-8') in resp.content, 'Create order of 200*0.4 units hit issue')

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


    """
    def test_purchase_order_succeed_bad_payment_acct(self):
        self.create_fitting_order(62)
        # update the tttzhang2000@yahoo.com's heepay account into bad account, since this user's order
        # is selected for the purchase, this update will failed the test.
        updated = UserPaymentMethod.objects.filter(user__username='tttzhang2000@yahoo.com').filter(provider__code='heepay').update(account_at_provider='bad_user_account')
        self.assertTrue(updated, 'change tttzhang2000@yahoo.com\'s heepay account should be successful')
        request = TradeAPIRequest(
                API_METHOD_PURCHASE,
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
        response = c.post('/api/v1/applypurchase/', request_str,
                          content_type='application/json')
        self.assertTrue(UserPaymentMethod.objects.filter(user__username='tttzhang2000@yahoo.com').filter(provider__code='heepay').update(account_at_provider='18600701961'),
              'recover tttzhang2000@yahoo.com\'s heepay account should be successful')

        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'FAIL')
        self.assertEqual(resp_json['return_msg'], "收钱方账号不存在")
    """

    # happy path for purchasing from 3rd party by using weixing (manual)
    def test_purchase_order_from_3rdParty_success_by_weixing(self):
        return True

    # 3rd party purchase request fail when
    def test_purchase_order_from_3rdParty_fail_by_missing_externalAddress(self):
        # API_USER2 is from www.3rdparty.com, check tradeex/apitests/fixtures/fixture_test_tradeapi.json, "model": "tradeex.apiuseraccount".
        request = TradeAPIRequest(
            API_METHOD_PURCHASE,
            TEST_API_USER2_APPKEY, TEST_API_USER2_SECRET,
            "any_out_trade_no",  # out_trade_no
            total_fee=TEST_PURCHASE_AMOUNT,  # total fee
            expire_minute=10,  # expire_minute
            payment_provider='heepay',
            payment_account='12738456',
            client_ip='127.0.0.1',  # client ip
            attach='userid:1',
            subject='人民币充值成功测试',
            notify_url='http://testurl',
            return_url='http://testurl',
            # external_cny_rec_address = "xxxxx", missing this variable is the reason why it fails.
        )

        c = Client()
        request_str = request.getPayload()
        print('test_purchase_order_from_3rdParty_fail_by_missing_externalAddress(): send request {0}'.format(request_str))
        response = c.post('/api/v1/applypurchase/', request_str,
                          content_type='application/json')
        resp_json = json.loads(response.content.decode('utf-8'))
        print('response is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))

        self.assertEqual('FAIL', resp_json['return_code'])
        self.assertEqual('请提供相应的支付账号', resp_json['return_msg'])

    @patch('tradeex.controllers.crypto_utils.CryptoUtility.unlock_wallet', side_effect=unlock_wallet_for_purchase_test)
    @patch('tradeex.controllers.crypto_utils.CryptoUtility.send_fund', side_effect=send_fund_for_purchase_test)
    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_request_side_effect)
    @patch('tradeex.client.apiclient.APIClient.send_json_request', side_effect=send_json_request_for_purchase_test)
    def test_purchase_order_succeed(self,send_json_request_function,
            send_buy_apply_request_function,
            send_fund_function,
            unlock_wallet_function):

        # create test sell orders
        self.create_fitting_order(62)
        print('-----------------------------------------------')
        print('test_purchase_order_succeed(): check userwallet and orders after creating sell orders')
        show_user_wallet_overview()
        show_order_overview()

        tttzhang2000_axf_wallets_prev = UserWallet.objects.get(user__username='tttzhang2000@yahoo.com', wallet__cryptocurrency__currency_code='AXFund')
        yingzhou_axf_wallets_prev = UserWallet.objects.get(user__username='yingzhou61@yahoo.ca', wallet__cryptocurrency__currency_code='AXFund')
        testuser1_axf_wallets_prev = UserWallet.objects.get(user__username='tradeex_api_user1', wallet__cryptocurrency__currency_code='AXFund')
        testuser1_cny_wallets_prev = UserWallet.objects.get(user__username='tradeex_api_user1', wallet__cryptocurrency__currency_code='CNY')
        master_cny_wallets_prev = UserWallet.objects.get(user__username='admin', wallet__cryptocurrency__currency_code='CNY')
        
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
                API_METHOD_PURCHASE,
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
        response = c.post('/api/v1/applypurchase/', request_str,
                          content_type='application/json')
        print('response is {0}'.format(json.dumps(json.loads(response.content.decode('utf-8')), ensure_ascii=False)))

        # no send fund is called
        unlock_wallet_function.assert_not_called()
        send_fund_function.assert_not_called()
        print('send_buy_apply_request_function called {0}'.format(send_buy_apply_request_function.call_count))
        send_buy_apply_request_function.assert_called_once()

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))

        self.assertEqual('SUCCESS', resp_json['return_code'])
        self.assertEqual('执行完成', resp_json['return_msg'])
        self.assertEqual('SUCCESS', resp_json['result_code'])
        self.assertEqual('下单申请成功', resp_json['result_msg'])
        self.assertEqual('UNKNOWN', resp_json['trade_status'])
        self.assertEqual(test_attach, resp_json['attach'])
        self.assertEqual(test_subject, resp_json['subject'])
        self.assertEqual(test_out_trade_no, resp_json['out_trade_no'])
        self.assertEqual(test_purchase_amount, int(resp_json['total_fee']))
        self.assertEqual(TEST_API_USER1_APPKEY, resp_json['api_key'])

        api_trans = self.get_api_trans(test_out_trade_no)
        self.assertEqual(resp_json['trx_bill_no'], api_trans.transactionId)
        self.assertEqual(TEST_HY_BILL_NO, api_trans.reference_bill_no)

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

        buy_order = api_trans.reference_order
        self.assertTrue(buy_order, "api_trans should have buyorder")
        self.assertEqual('BUY', buy_order.order_type)
        self.assertEqual('ALL_OR_NOTHING', buy_order.sub_type)
        self.assertEqual('API', buy_order.order_source)
        self.assertEqual(test_purchase_amount, int(round(buy_order.total_amount,2) * 100))
        self.assertEqual(155, buy_order.units)
        self.assertEqual(156, buy_order.reference_order.units)
        # yingzhou's sell order with 156 is older than the tttzhang2000's order with same amount
        # we will need to pick the older order, so system grab the first one 
        self.assertEqual('yingzhou61@yahoo.ca', buy_order.reference_order.user.username)
        self.assertEqual('OPEN', buy_order.reference_order.status)
        self.assertEqual(155, buy_order.reference_order.units_locked)
        self.assertEqual(1.0, buy_order.reference_order.units_available_to_trade)


        print('-----------------------------------------------')
        print('test_purchase_order_succeed(): show wallet and orders after send api request')
        show_user_wallet_overview()
        show_order_overview()

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

        print('-----------------------------------------------')
        print('test_purchase_order_succeed(): check userwallet and orders after heepay confirmation')
        show_user_wallet_overview()
        show_order_overview()

        self.assertEqual('OK', response.content.decode('utf-8'), "The response to the payment confirmation should be OK")

        print('!!!!!!!!!!!!!!!---called count {0}'.format(send_fund_function.call_count))
        # verify this has been called once and money has transfered
        send_fund_function.assert_called_once()
        send_json_request_function.called_once()

        tttzhang2000_axf_wallets = UserWallet.objects.get(user__username='tttzhang2000@yahoo.com', wallet__cryptocurrency__currency_code='AXFund')
        yingzhou_axf_wallets = UserWallet.objects.get(user__username='yingzhou61@yahoo.ca', wallet__cryptocurrency__currency_code='AXFund')
        testuser1_axf_wallets = UserWallet.objects.get(user__username='tradeex_api_user1', wallet__cryptocurrency__currency_code='AXFund')
        testuser1_cny_wallets = UserWallet.objects.get(user__username='tradeex_api_user1', wallet__cryptocurrency__currency_code='CNY')
        master_cny_wallets = UserWallet.objects.get(user__username='admin', wallet__cryptocurrency__currency_code='CNY')

        # after making purchase, nothing changed for the account not selected as seller
        self.assertEqual(tttzhang2000_axf_wallets.balance, tttzhang2000_axf_wallets_prev.balance)
        self.assertEqual(tttzhang2000_axf_wallets.locked_balance, tttzhang2000_axf_wallets_prev.locked_balance)
        self.assertEqual(tttzhang2000_axf_wallets.available_balance, tttzhang2000_axf_wallets_prev.available_balance)

        #after confirmed purchase, seller's axf wallet changed
        self.assertEqual(yingzhou_axf_wallets.balance, yingzhou_axf_wallets_prev.balance - buy_order.units)
        self.assertEqual(yingzhou_axf_wallets.locked_balance, yingzhou_axf_wallets_prev.locked_balance - buy_order.units)
        self.assertEqual(yingzhou_axf_wallets.available_balance, yingzhou_axf_wallets_prev.available_balance)

        #after confirmed purchase, buyer axf wallet changed
        self.assertEqual(testuser1_axf_wallets.balance, testuser1_axf_wallets_prev.balance + buy_order.units )
        self.assertEqual(testuser1_axf_wallets.locked_balance, testuser1_axf_wallets_prev.locked_balance)
        self.assertEqual(testuser1_axf_wallets.available_balance, testuser1_axf_wallets_prev.available_balance + buy_order.units)

        self.assertEqual(testuser1_cny_wallets.balance, testuser1_cny_wallets_prev.balance + buy_order.total_amount)
        # the amount is locked because we made external transfer after the purchase
        self.assertEqual(testuser1_cny_wallets.locked_balance, testuser1_cny_wallets_prev.locked_balance + buy_order.total_amount)
        # nothing changed on available balance since purchased amount was transferred out
        self.assertEqual(testuser1_cny_wallets.available_balance, testuser1_cny_wallets_prev.available_balance)
        
        # before any pay or purchase, nothing is changed on master wallet
        self.assertEqual(master_cny_wallets.balance, master_cny_wallets_prev.balance - buy_order.total_amount)
        self.assertEqual(master_cny_wallets.locked_balance, master_cny_wallets_prev.locked_balance)
        self.assertEqual(master_cny_wallets.available_balance, master_cny_wallets_prev.available_balance - buy_order.total_amount)

        tttzhang2000_axf_wallets_prev = tttzhang2000_axf_wallets
        yingzhou_axf_wallets_prev = yingzhou_axf_wallets
        testuser1_axf_wallets_prev = testuser1_axf_wallets
        testuser1_cny_wallets_prev = testuser1_cny_wallets
        master_cny_wallets_prev = master_cny_wallets

        buy_order.refresh_from_db()
        self.assertTrue('PAID', buy_order.status)
        self.assertTrue('OPEN', buy_order.reference_order)
        self.assertEqual(155, buy_order.reference_order.units_locked)
        self.assertEqual(1.0, buy_order.reference_order.units_available_to_trade)

        c = Client()
        c.login(username='yingzhou', password='user@123')
        response = c.get('/trading/account/cron/order_batch_process/')

        print('-------------------------------------------------------------------------------')
        print('test_purchase_order_succeed(): show overview after order process routine executed')
        show_user_wallet_overview()
        show_order_overview()

        send_fund_function.assert_called_once()
        send_json_request_function.called_once()

        tttzhang2000_axf_wallets = UserWallet.objects.get(user__username='tttzhang2000@yahoo.com', wallet__cryptocurrency__currency_code='AXFund')
        yingzhou_axf_wallets = UserWallet.objects.get(user__username='yingzhou61@yahoo.ca', wallet__cryptocurrency__currency_code='AXFund')
        testuser1_axf_wallets = UserWallet.objects.get(user__username='tradeex_api_user1', wallet__cryptocurrency__currency_code='AXFund')
        testuser1_cny_wallets = UserWallet.objects.get(user__username='tradeex_api_user1', wallet__cryptocurrency__currency_code='CNY')
        master_cny_wallets = UserWallet.objects.get(user__username='admin', wallet__cryptocurrency__currency_code='CNY')

        # after making purchase, nothing changed for the account not selected as seller
        self.assertEqual(tttzhang2000_axf_wallets.balance, tttzhang2000_axf_wallets_prev.balance)
        self.assertEqual(tttzhang2000_axf_wallets.locked_balance, tttzhang2000_axf_wallets_prev.locked_balance)
        self.assertEqual(tttzhang2000_axf_wallets.available_balance, tttzhang2000_axf_wallets_prev.available_balance)


        tttzhang2000_axf_wallets_prev = tttzhang2000_axf_wallets
        yingzhou_axf_wallets_prev = yingzhou_axf_wallets
        testuser1_axf_wallets_prev = testuser1_axf_wallets
        testuser1_cny_wallets_prev = testuser1_cny_wallets
        master_cny_wallets_prev = master_cny_wallets

        buy_order.refresh_from_db()
        self.assertTrue('PAID', buy_order.status)
        self.assertTrue('OPEN', buy_order.reference_order)
        self.assertEqual(155, buy_order.reference_order.units_locked)
        self.assertEqual(1.0, buy_order.reference_order.units_available_to_trade)


    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_for_redeem_side_effect)
    @patch('tradeex.client.apiclient.APIClient.send_json_request', 
            side_effect=send_json_request_for_redeem_test)
    def test_redeem_order_succeed(self, send_json_request_function,
        send_buy_apply_request_function,):
        try:
            api_users = APIUserAccount.objects.get(pk=TEST_API_USER2_APPKEY)
        except:
            self.fail('test_purchase_order_succeed() did not find api user {0}'.format(
                TEST_API_USER2_APPKEY
            ))

        print('test_redeem_order_succeed(): ready to create purchase orders first')
        show_user_wallet_overview(['tttzhang2000@yahoo.com', 'yingzhou61@yahoo.ca'])
        # create test sell orders
        self.create_fitting_order(62)

        print('test_redeem_order_succeed(): check userwallet and orders after creating sell orders')
        show_user_wallet_overview()
        show_order_overview()

        # these are the app_id and secret from fixture apiuseraccount        
        # TODO: validate this is tradeex_api_user1
        app_id = TEST_API_USER2_APPKEY
        secret_key = TEST_API_USER2_SECRET
        test_out_trade_no = TEST_OUT_TRADE_NO_REDEEM
        test_purchase_amount = TEST_REDEEM_AMOUNT
        test_user_heepay_to_account = '12738456'
        test_attach = 'userid:1'
        test_subject = '人民币提现成功测试'
        test_notify_url = 'http://testurl'
        test_return_url = 'http://testurl'
        request = TradeAPIRequest(
                API_METHOD_REDEEM,
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
        print('test_redeem_order_succeed(): send request {0}'.format(request_str))
        response = c.post('/api/v1/applyredeem/', request_str,
                          content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'SUCCESS')

        self.validate_purchase_first_state(request, resp_json)
        print('test_redeem_order_succeed(): check userwallet and orders after sending redeem request')
        show_user_wallet_overview()
        show_order_overview()

        purchase_request = {}
        api_trans = APIUserTransaction.objects.get(api_out_trade_no=test_out_trade_no)

        try:
            sell_order = Order.objects.get(pk=api_trans.reference_order.order_id)
            self.assertEqual('SELL', sell_order.order_type)
        except Order.DoesNotExist:
            self.fail('could not find the sell order for sell transaction {0}'.format(
                api_trans.transactionId
            ))
        except Order.MultipleObjectsReturned:
            self.fail('More than one sell order for sell transaction {0}'.format(
                api_trans.transactionId
            ))

        request_obj = TradeAPIRequest.parseFromJson(json.loads(api_trans.original_request))
        self.assertEqual(API_METHOD_REDEEM, request_obj.method)

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
        purchase_request['order_currency'] = 'CNY'
        #TODO: why purchase donot set unit_price currency

        c2 = Client()
        c.login(username='tttzhang2000@yahoo.com', password='user@123')
        purchase_response = c.post('/trading/purchase/createorder2/', purchase_request, follow=True)

        print('-------------------------------------------------------------------------------')
        print('test_redeem_order_succeed(): check userwallet and orders after tttzhang2000@yahoo.com bought on the redeem order')
        show_user_wallet_overview()
        show_order_overview()
        show_user_wallet_trans('tttzhang2000@yahoo.com', api_users.user.username)


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

        print('---------------------------------------------------------------------------------')
        print('test_redeem_order_succeed(): show overview after heepay confirm buyer\'s purchase')
        show_user_wallet_overview()
        show_order_overview()
        show_user_wallet_trans('tttzhang2000@yahoo.com', api_users.user.username)

        c = Client()
        c.login(username='yingzhou', password='user@123')
        response = c.get('/trading/account/cron/order_batch_process/')

        print('-------------------------------------------------------------------------------')
        print('test_redeem_order_succeed(): show overview after order process routine executed')
        show_user_wallet_overview()
        show_order_overview()
        show_user_wallet_trans('tttzhang2000@yahoo.com', api_users.user.username)


    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_for_redeem_side_effect)
    @patch('tradeex.client.apiclient.APIClient.send_json_request', 
            side_effect=send_json_request_for_redeem_test)
    @patch.object(CryptoUtility, 'send_fund')
    def test_redeem_order_async_succeed(self, mock_send_fund,
        send_json_request_function, send_buy_apply_request_function):
        cyn_trans = {}
        cyn_trans['txid'] = 'SIMULATED_TRANS'
        mock_send_fund.return_value = cyn_trans

        try:
            api_users = APIUserAccount.objects.get(pk=TEST_API_USER1_APPKEY)
        except:
            self.fail('test_redeem_order_async_succeed() did not find api user {0}'.format(
                TEST_API_USER1_APPKEY
            ))

        print('test_redeem_order_async_succeed(): ready to create purchase orders first')
        show_user_wallet_overview(['tttzhang2000@yahoo.com', 'yingzhou61@yahoo.ca'])
        # create test sell orders
        self.create_fitting_order(62)

        print('test_redeem_order_async_succeed(): check userwallet and orders after creating sell orders')
        show_user_wallet_overview()
        show_order_overview()

        # these are the app_id and secret from fixture apiuseraccount        
        # TODO: validate this is tradeex_api_user1
        app_id = TEST_API_USER1_APPKEY
        secret_key = TEST_API_USER1_SECRET
        test_out_trade_no = TEST_OUT_TRADE_NO_REDEEM
        test_purchase_amount = TEST_REDEEM_AMOUNT
        test_user_heepay_to_account = '12738456'
        test_attach = 'userid:1'
        test_subject = '人民币提现成功测试'
        test_notify_url = 'http://testurl'
        test_return_url = 'http://testurl'
        request = TradeAPIRequest(
                API_METHOD_REDEEM,
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
        print('test_redeem_order_async_succeed(): send request {0}'.format(request_str))
        response = c.post('/api/v1/applyredeem/', request_str,
                          content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'SUCCESS')

        print('test_redeem_order_async_succeed(): check userwallet and orders after sending redeem request')
        show_user_wallet_overview()
        show_order_overview()

        # since test user's cny wallet starts with 0, there should be no sell order
        api_trans = APIUserTransaction.objects.get(api_out_trade_no=test_out_trade_no)
        self.assertTrue(api_trans.reference_order is None)

        # now update user's cny wallet
        # TODO: use fake wallet transaction to update it
        seller_cny_wallet = UserWallet.objects.get(wallet__cryptocurrency__currency_code = 'CNY', user__id = api_trans.api_user.user.id)
        seller_cny_wallet.balance = seller_cny_wallet.available_balance = 50
        seller_cny_wallet.save()
        seller_axf_wallet = UserWallet.objects.get(wallet__cryptocurrency__currency_code = 'AXFund', user__id = api_trans.api_user.user.id)
        seller_axf_wallet.balance = seller_axf_wallet.available_balance = 160
        seller_axf_wallet.save()

        c_order = Client()
        c_order.login(username='yingzhou', password='user@123')
        response = c_order.get('/trading/account/cron/order_batch_process/')
        
        self.validate_purchase_first_state(request, resp_json)
        print('test_redeem_order_async_succeed(): check userwallet and orders after order backend run (after seller cyn wallet updated')
        show_user_wallet_overview()
        show_order_overview()

        api_trans = APIUserTransaction.objects.get(api_out_trade_no=test_out_trade_no)

        try:
            sell_order = Order.objects.get(pk=api_trans.reference_order.order_id)
            self.assertEqual('SELL', sell_order.order_type)
        except Order.DoesNotExist:
            self.fail('could not find the sell order for sell transaction {0}'.format(
                api_trans.transactionId
            ))
        except Order.MultipleObjectsReturned:
            self.fail('More than one sell order for sell transaction {0}'.format(
                api_trans.transactionId
            ))

        request_obj = TradeAPIRequest.parseFromJson(json.loads(api_trans.original_request))
        self.assertEqual(API_METHOD_REDEEM, request_obj.method)

        purchase_request = {}
        purchase_request['reference_order_id'] = api_trans.reference_order.order_id
        purchase_request['owner_user_id'] = api_trans.reference_order.user.id
        purchase_request['quantity']=api_trans.reference_order.units
        purchase_request['unit_price'] = api_trans.reference_order.unit_price
        logger.debug('test_redeem_order_async_succeed(): seller payment provider {0}'.format(
            api_trans.payment_provider
        ))
        purchase_request['seller_payment_provider']=api_trans.payment_provider.code
        purchase_request['crypto'] = 'AXFund'
        purchase_request['total_amount'] = api_trans.reference_order.total_amount
        purchase_request['order_currency'] = 'CNY'
        #TODO: why purchase donot set unit_price currency

        c2 = Client()
        c.login(username='tttzhang2000@yahoo.com', password='user@123')
        purchase_response = c.post('/trading/purchase/createorder2/', purchase_request, follow=True)

        print('-------------------------------------------------------------------------------')
        print('test_redeem_order_async_succeed(): check userwallet and orders after tttzhang2000@yahoo.com bought on the redeem order')
        show_user_wallet_overview()
        show_order_overview()
        show_user_wallet_trans('tttzhang2000@yahoo.com', api_users.user.username)

        api_trans = self.get_api_trans(test_out_trade_no)
        self.validate_api_trans_before_confirm(api_trans, app_id, 
            secret_key, test_out_trade_no, expected_total_fee=test_purchase_amount,
            expected_subject = test_subject, expected_attach = test_attach,
            expected_return_url = test_return_url, 
            expected_notify_url = test_notify_url)
        show_api_trans(api_trans)
        

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

        print('---------------------------------------------------------------------------------')
        print('test_redeem_order_async_succeed(): show overview after heepay confirm buyer\'s purchase')
        show_user_wallet_overview()
        show_order_overview()
        show_user_wallet_trans('tttzhang2000@yahoo.com', api_users.user.username)
        api_trans.refresh_from_db()
        show_api_trans(api_trans)

        c = Client()
        c.login(username='yingzhou', password='user@123')
        response = c.get('/trading/account/cron/order_batch_process/')

        print('-------------------------------------------------------------------------------')
        print('test_redeem_order_async_succeed(): show overview after order process routine executed')
        show_user_wallet_overview()
        show_order_overview()
        show_user_wallet_trans('tttzhang2000@yahoo.com', api_users.user.username)
        api_trans.refresh_from_db()
        show_api_trans(api_trans)
        
        # get all master CNY wallet trans
        master_trans = UserWalletTransaction.objects.filter(user_wallet__user__username='admin', 
            user_wallet__wallet__cryptocurrency__currency_code='CNY')
        self.assertEqual(1, len(master_trans))
        dump_userwallet_trans(master_trans[0])


    @patch('tradeex.controllers.crypto_utils.CryptoUtility.unlock_wallet', side_effect=unlock_wallet_for_purchase_test)
    @patch('tradeex.controllers.crypto_utils.CryptoUtility.send_fund', side_effect=send_fund_for_purchase_test)
    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_request_side_effect)
    @patch('tradeex.client.apiclient.APIClient.send_json_request', side_effect=send_json_request_for_purchase_test)
    def test_status_query(self,send_json_request_function,
            send_buy_apply_request_function, send_fund_function, unlock_wallet):

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
        response = c.post('/api/v1/applypurchase/', request_str,
                          content_type='application/json')

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        self.assertEqual(test_out_trade_no, resp_json["out_trade_no"])

        api_trans = self.get_api_trans(test_out_trade_no) 
        logger.info('finish issue purchase request, about to query the status')
        query_request = TradeAPIRequest(
            "wallet.trade.query",
            app_id, secret_key,
            test_out_trade_no, # out_trade_no    
            trx_bill_no=resp_json["trx_bill_no"],
            timestamp = timegm(dt.datetime.utcnow().utctimetuple())
        )

        c_query = Client()
        request_str = query_request.getPayload()
        print('test_status_query(): send request right after purchase command {0}'.format(request_str))
        response = c_query.post('/api/v1/checkstatus/', request_str,
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
        response = c_query.post('/api/v1/checkstatus/', request_str,
                          content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        print('Status right after purchase command is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))
        self.assertEqual('SUCCESS', resp_json['return_code'], 'The query should return SUCCCESS')
        self.assertEqual('Success', resp_json['trade_status'], 'The transaction should be in progress')
        
        # now run order_backend_proc
        c1 = Client()
        response = c1.get('/trading/account/cron/order_batch_process/')

        print('test_status_query(): send request after order_backend_proc run')
        response = c_query.post('/api/v1/checkstatus/', request_str,
                          content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        print('Status right after purchase command is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))
        self.assertEqual('SUCCESS', resp_json['return_code'], 'The query should return SUCCCESS')
        self.assertEqual('Success', resp_json['trade_status'], 'The transaction should be in progress')


    @patch('tradeex.controllers.crypto_utils.CryptoUtility.unlock_wallet', side_effect=unlock_wallet_for_purchase_test)
    @patch('tradeex.controllers.crypto_utils.CryptoUtility.send_fund', side_effect=send_fund_for_purchase_test)
    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', 
           side_effect=send_buy_apply_request_side_effect)
    @patch('tradeex.client.apiclient.APIClient.send_json_request', side_effect=send_json_request_for_purchase_test)
    def test_send_notification_after_confirm(self, send_json_request_function,
            send_buy_apply_request_function,  send_fund_function, unlock_wallet):

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
        response = c.post('/api/v1/applypurchase/', request_str,
                          content_type='application/json')

        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(resp_json['return_code'], 'SUCCESS')
        self.assertEqual(test_out_trade_no, resp_json["out_trade_no"])

        api_trans = self.get_api_trans(test_out_trade_no)
        logger.info('finish issue purchase request, about to query the status')
        query_request = TradeAPIRequest(
            "wallet.trade.query",
            app_id, secret_key,
            test_out_trade_no, # out_trade_no    
            trx_bill_no=resp_json["trx_bill_no"],
            timestamp = timegm(dt.datetime.utcnow().utctimetuple())
        )
    
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
        
        # should not send any notification or transfer any coins
        unlock_wallet.assert_called_once()
        send_json_request_function.assert_called_once()
        self.assertEqual('OK', response.content.decode('utf-8'), "The response to the payment confirmation should be OK")

        c_query = Client()
        request_str = query_request.getPayload()
        print('test_status_query(): send request right after purchase command {0}'.format(request_str))
        response = c_query.post('/api/v1/checkstatus/', request_str,
                          content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        print('Status right after purchase command is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))
        self.assertEqual('SUCCESS', resp_json['return_code'], 'The query should return SUCCCESS')
        self.assertEqual('Success', resp_json['trade_status'], 'The transaction should be in progress')
        

        # now directly confirm the order
        api_trans = self.get_api_trans(test_out_trade_no)
        ordermanager.confirm_purchase_order(api_trans.reference_order.order_id, 'admin')
        unlock_wallet.assert_called_once()
        send_json_request_function.assert_called_once()

        # now run order_backend_proc
        c1 = Client()
        response = c1.get('/trading/account/cron/order_batch_process/')

        print('test_status_query(): send request after order_backend_proc run')
        response = c_query.post('/api/v1/checkstatus/', request_str,
                          content_type='application/json')
        self.assertEqual(200, response.status_code)
        resp_json = json.loads(response.content.decode('utf-8'))
        print('Status right after purchase command is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))
        self.assertEqual('SUCCESS', resp_json['return_code'], 'The query should return SUCCCESS')
        self.assertEqual('Success', resp_json['trade_status'], 'The transaction should be in progress')

        # no more call to transfer coin or send notification
        unlock_wallet.assert_called_once()
        send_json_request_function.assert_called_once()

