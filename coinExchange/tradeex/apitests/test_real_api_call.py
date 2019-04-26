#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, json, hashlib
import datetime as dt

from django.conf import settings
from django.test import TestCase

from tradeex.data.api_const import *
from tradeex.data.tradeapirequest import TradeAPIRequest
from tradeex.client.apiclient import APIClient

TEST_API_USER1_APPKEY = 'api_test_user_appId1'
TEST_API_USER1_SECRET ='api_test_user_secrets1'
TEST_PURCHASE_AMOUNT = 2


# Create your tests here.
class TestAPICall(TestCase):

    def test_purchase_api_call(self):
        if not settings.TEST_REAL_CALL:
            print('Donot run real call test')
            return

        app_id = TEST_API_USER1_APPKEY
        secret_key = TEST_API_USER1_SECRET
        test_out_trade_no = 'order_to_purchase'
        test_purchase_amount = TEST_PURCHASE_AMOUNT
        test_user_heepay_from_account = '13910978598'
        test_timestamp = int(dt.datetime.utcnow().strftime("%Y%m%d%H%M%s"))
        test_out_trade_no = 'order_to_purchase_{0}'.format(test_timestamp)
        test_attach = 'userid:1'
        test_subject = '人民币充值成功测试'
        test_notify_url = 'http://52.43.117.129/api/v1/api_notify_test/'
        test_return_url = 'http://52.43.117.129/api/v1/api_notify_test/'
        request = TradeAPIRequest(
                API_METHOD_PURCHASE,
                app_id, secret_key,
                test_out_trade_no, # out_trade_no
                total_fee=test_purchase_amount, # total fee
                expire_minute=10, # expire_minute
                payment_provider='heepay', 
                payment_account=test_user_heepay_from_account,
                client_ip='127.0.0.1', #client ip
                timestamp = test_timestamp,
                attach=test_attach,
                subject=test_subject,
                notify_url=test_notify_url,
                return_url=test_return_url)

        c = APIClient('http://52.43.117.129/api/v1/applypurchase/')
        request_str = request.getPayload()
        resp_json = c.send_json_request(json.loads(request_str))
        print('reply is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))


    def test_redeem_api_call(self):
        if not settings.TEST_REAL_CALL:
            print('Donot run real call test')
            return
        app_id = TEST_API_USER1_APPKEY
        secret_key = TEST_API_USER1_SECRET
        test_out_trade_no = 'order_test_redeem'
        test_purchase_amount = TEST_PURCHASE_AMOUNT
        test_user_heepay_from_account = '13910978598'
        test_attach = 'userid:1'
        test_subject = '人民币提现成功测试'
        test_notify_url = 'http://52.43.117.129/api/v1/api_notify_test/'
        test_return_url = 'http://52.43.117.129/api/v1/api_notify_test/'
        request = TradeAPIRequest(
                API_METHOD_REDEEM,
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

        c = APIClient('http://52.43.117.129/api/v1/applyredeem/')
        request_str = request.getPayload()
        resp_json = c.send_json_request(json.loads(request_str))
        print('reply is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))

    def test_user_api_call(self):
        pass
        request = TradeAPIRequest(
                API_METHOD_PURCHASE,
                'L2CLMSBYJAPF0HX0PY4VIW0XFPCNT6Y8', '6521126bd7b0907aa2671c547db671f0',
                '201806251012458960', # out_trade_no
                total_fee=1, # total fee
                payment_provider='heepay', 
                payment_account='13910978598',
                client_ip='42.96.158.70', #client ip
                timestamp = 20180625101245,
                attach='1235',
                subject='测试',
                notify_url='http://game.p2pinfo.cn/api_notify.php',
                return_url='http://game.p2pinfo.cn/api_notify.php')

        c = APIClient('http://52.43.117.129/api/v1/applypurchase/')
        request_str = request.getPayload()
        resp_json = c.send_json_request(json.loads(request_str))
        print('reply is {0}'.format(json.dumps(resp_json, ensure_ascii=False)))

    def test_validate_request(self):
        request_json = {"method":"wallet.trade.buy","version":"1.0","api_key":"L2CLMSBYJAPF0HX0PY4VIW0XFPCNT6Y8","charset":"utf-8","sign_type":"MD5","timestamp":"20180630064937","biz_content":"{\"api_account_type\":\"Account\",\"attach\":\"1235\",\"client_ip\":\"42.96.158.70\",\"expire_minute\":\"0\",\"meta_option\":\"123\",\"notify_url\":\"http://game.p2pinfo.cn/api_notify.php\",\"out_trade_no\":\"2018063006493725900\",\"payment_account\":\"13910978598\",\"payment_provider\":\"heepay\",\"return_url\":\"http://game.p2pinfo.cn/api_notify.php\",\"subject\":\"test\",\"total_fee\":\"1\"}","sign":"E5AFC1466C676A2277DA3DC218480256"}
        request_obj = TradeAPIRequest.parseFromJson(request_json)

        str1 = 'api_key=L2CLMSBYJAPF0HX0PY4VIW0XFPCNT6Y8&biz_content={"api_account_type":"Account","attach":"1235","client_ip":"42.96.158.70","expire_minute":"0","meta_option":"123","notify_url":"http://game.p2pinfo.cn/api_notify.php","out_trade_no":"2018063006493725900","payment_account":"13910978598","payment_provider":"heepay","return_url":"http://game.p2pinfo.cn/api_notify.php","subject":"测试","total_fee":"1"}&charset=utf-8&method=wallet.trade.buy&sign_type=MD5&timestamp=20180630064937&version=1.0&key=6521126bd7b0907aa2671c547db671f0'
        str2 = 'api_key=L2CLMSBYJAPF0HX0PY4VIW0XFPCNT6Y8&biz_content={"api_account_type":"Account","attach":"1235","client_ip":"42.96.158.70","expire_minute":"0","meta_option":"123","notify_url":"http://game.p2pinfo.cn/api_notify.php","out_trade_no":"2018063006493725900","payment_account":"13910978598","payment_provider":"heepay","return_url":"http://game.p2pinfo.cn/api_notify.php","subject":"测试","total_fee":"1"}&charset=utf-8&method=wallet.trade.buy&sign_type=MD5&timestamp=20180630064937&version=1.0&key=6521126bd7b0907aa2671c547db671f0'
        self.maxDiff = None
        self.assertEqual(str1, str2)
        m = hashlib.md5()
        m.update(str1.encode('utf-8'))
        print("signature str 1 is {0}".format(m.hexdigest()))
        m = hashlib.md5()
        m.update(str2.encode('utf-8'))
        print("signature str 2 is {0}".format(m.hexdigest()))
        self.assertTrue(request_obj.is_valid('6521126bd7b0907aa2671c547db671f0'))

        """
        testString = [ 'api_key=L2CLMSBYJAPF0HX0PY4VIW0XFPCNT6Y8', '测试',
           'api_key=L2CLMSBYJAPF0HX0PY4VIW0XFPCNT6Y8&biz_content={\"api_account_type\":\"Account\",\"attach\":\"1235\",\"client_ip\":\"42.96.158.70\",\"expire_minute\":\"0\",\"meta_option\":\"123\",\"notify_url\":\"http://game.p2pinfo.cn/api_notify.php\",\"out_trade_no\":\"2018063006493725900\",\"payment_account\":\"13910978598\",\"payment_provider\":\"heepay\",\"return_url\":\"http://game.p2pinfo.cn/api_notify.php\",\"subject\":\"test\",\"total_fee\":\"1\"}&charset=utf-8&method=wallet.trade.buy&sign_type=MD5&timestamp=20180630064937&version=1.0&key=6521126bd7b0907aa2671c547db671f0'

        ]

        for teststr in testString:
            print('字符串 {0}'.format(teststr))
            m = hashlib.md5()
            m.update(teststr.encode('utf-8'))
            print('签名 %s' % m.hexdigest())
        """
