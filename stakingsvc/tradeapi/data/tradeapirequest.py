#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, time, datetime as dt
import hashlib
import logging

from tradeex.utils import *
from tradeex.data.api_const import *

logger = logging.getLogger("tradeex.tradeapirequest")

class TradeAPIRequest(object):

    def __init__(self, method, apikey, secret_key, out_trade_no,
            trx_bill_no=None,
            total_fee=0,
            expire_minute=10, 
            payment_provider='heepay',
            payment_account=None, 
            client_ip='127.0.0.1', 
            subject=None, attach=None, notify_url=None, return_url=None,
            version='1.0', charset='utf-8', sign_type='MD5', timestamp=0,
            sign=None, original_json_request=None):
        self.version = version
        self.charset = charset
        self.sign_type = sign_type
        self.method = method
        self.apikey = apikey
        self.secret_key = secret_key
        self.out_trade_no = out_trade_no
        self.trx_bill_no = trx_bill_no
        self.total_fee = total_fee
        if total_fee < 1 and method in ['wallet.trade.buy', 'wallet.trade.sell']:
            raise ValueError("The total fee is too small")
        self.expire_minute = expire_minute
        self.payment_provider = payment_provider
        self.payment_account = payment_account
        self.client_ip = client_ip
        self.subject = subject
        self.attach = attach
        self.return_url = return_url
        self.notify_url= notify_url
        self.timestamp = timestamp
        self.sign = sign
        self.meta_option = None
        self.original_json_request = original_json_request
        if not self.sign:
            if not self.secret_key:
                raise ValueError('Not secrete key to sign the request')
            self.sign = sign_api_content(self.__create_json_to_sign(), self.secret_key)

    @classmethod
    def parseFromJson(cls, json_input):
        method = json_input['method']
        if not method in [API_METHOD_PURCHASE, API_METHOD_REDEEM, API_METHOD_QUERY, API_METHOD_CANCEL]:
            raise ValueError('Unexpected method {0}'.format(method))

        biz_content_json = json.loads(json_input['biz_content'])
        return TradeAPIRequest(method, json_input['api_key'], '', biz_content_json['out_trade_no'],
            total_fee=int(biz_content_json.get('total_fee', 0)),
            expire_minute=biz_content_json.get('expire_minute',0),
            payment_provider=biz_content_json.get('payment_provider', None),
            payment_account=biz_content_json.get('payment_account', None),
            client_ip=biz_content_json.get('client_ip', None),
            trx_bill_no =biz_content_json.get('trx_bill_no', None),
            subject=biz_content_json.get('subject', None),            
            attach = biz_content_json.get('attach', None),
            notify_url= biz_content_json.get('notify_url', None),
            return_url= biz_content_json.get('return_url', None),
            version = json_input['version'],
            charset = json_input['charset'],
            sign_type = json_input['sign_type'],
            timestamp = json_input['timestamp'],
            sign = json_input['sign'],
            original_json_request = json_input)

    def __get_biz_content_json(self):
        biz_content_json = {}
        biz_content_json['out_trade_no'] = self.out_trade_no
        if self.method in ['wallet.trade.buy', 'wallet.trade.sell']:
            biz_content_json['subject'] = self.subject
            biz_content_json['total_fee'] = self.total_fee
            biz_content_json['expire_minute'] = self.expire_minute
            biz_content_json['api_account_mode']= 'Account'
            biz_content_json['client_ip'] = self.client_ip
            biz_content_json['payment_provider'] = self.payment_provider
            biz_content_json['payment_account'] = self.payment_account
            if self.attach:
                biz_content_json['attach'] = self.attach
            if self.meta_option:
                biz_content_json['meta_option'] = self.meta_option
            if self.notify_url:
                biz_content_json['notify_url'] = self.notify_url
            if self.return_url:
                biz_content_json['return_url'] = self.return_url
        elif self.method == 'wallet.trade.query':
            biz_content_json['trx_bill_no'] = self.trx_bill_no
        return biz_content_json

    def __create_json_to_sign(self):
        jsonobj = {}
        jsonobj['method'] = self.method
        jsonobj['version'] = self.version
        jsonobj['api_key']= self.apikey
        jsonobj['charset'] = self.charset
        jsonobj['sign_type'] = self.sign_type
        jsonobj['timestamp'] = self.timestamp
        biz_content_json = self.__get_biz_content_json()

        jsonobj['biz_content'] = json.dumps(biz_content_json, ensure_ascii=False, sort_keys=True)
        return jsonobj

    def is_valid(self, secret_key):
        self.secret_key = secret_key
        signed = sign_api_content(self.__create_json_to_sign(), secret_key)
        logger.info('signed is {0} original sign is {1}'.format(signed, self.sign))
        return signed == self.sign

    def getPayload(self):
        if not self.sign:
            raise ValueError('getPayload(): There is no signature of the request')
        jsonobj = self.__create_json_to_sign()
        jsonobj['sign'] = self.sign
        return json.dumps(jsonobj, ensure_ascii=False)
