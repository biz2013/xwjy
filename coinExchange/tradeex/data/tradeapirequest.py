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
            sign=None, original_json_request=None, external_cny_rec_address = None,
            txid=None, **kwargs):
        self.version = version
        self.charset = charset
        self.sign_type = sign_type
        self.method = method
        self.apikey = apikey
        self.secret_key = secret_key
        self.out_trade_no = out_trade_no
        self.trx_bill_no = trx_bill_no
        self.total_fee = total_fee
        if int(total_fee) < 1 and method in ['wallet.trade.buy', 'wallet.trade.sell']:
            raise ValueError("The total fee is too small")
        self.expire_minute = expire_minute
        self.payment_provider = payment_provider
        if not self.payment_provider and self.method in [API_METHOD_PURCHASE, API_METHOD_REDEEM]:
            raise ValueError(ERR_REQUEST_MISS_PAYMENT_PROVIDER)

        self.payment_account = payment_account
        if not self.payment_account and self.method == API_METHOD_REDEEM:
            raise ValueError(ERR_REQUEST_MISS_PAYMENT_ACCOUNT_FOR_REDEEM) 

        self.client_ip = client_ip
        self.subject = subject
        self.attach = attach
        self.return_url = return_url
        self.notify_url= notify_url
        self.timestamp = timestamp
        self.sign = sign
        self.meta_option = None
        self.pay_option = None
        self.external_cny_rec_address = external_cny_rec_address
        self.txid = txid
        self.original_json_request = original_json_request
        if kwargs:
            for key,value in kwargs.items():
                if key == 'meta_option':
                    self.meta_option = value
                elif key == 'pay_option':
                    self.pay_option = value
                elif key == 'external_cny_rec_address':
                    self.external_cny_rec_address = value
        if not self.sign:
            if not self.secret_key:
                raise ValueError('Not secrete key to sign the request')
            self.sign = sign_api_content(self.__create_json_to_sign(), self.secret_key)

    @classmethod
    def parseFromJson(cls, json_input):
        if 'method' not in json_input:
            raise ValueError(ERR_REQUEST_MISS_METHOD)
        if 'biz_content' not in json_input:
            raise ValueError(ERR_REQUEST_MISS_BIZCONTENT)
        if 'version' not in json_input:
            raise ValueError(ERR_REQUEST_MISS_VERSION)
        if 'charset' not in json_input:
            raise ValueError(ERR_REQUEST_MISS_CHARSET)
        if 'sign_type' not in json_input:
            raise ValueError(ERR_REQUEST_MISS_SIGN_TYPE)
        if 'timestamp' not in json_input:
            raise ValueError(ERR_REQUEST_MISS_TIMESTAMP)
        if 'sign' not in json_input:
            raise ValueError(ERR_REQUEST_MISS_SIGNATURE)
            
        method = json_input['method']
        if not method in [API_METHOD_PURCHASE, API_METHOD_REDEEM, API_METHOD_QUERY, API_METHOD_CANCEL]:
            raise ValueError('Unexpected method {0}'.format(method))

        if method == API_METHOD_REDEEM and 'txid' not in json_input:
            raise ValueError(ERR_REQUEST_MISS_TXID_FOR_REDEEM)

        biz_content_json = json.loads(json_input['biz_content'])
        if 'payment_account' not in biz_content_json and json_input['method'] == API_METHOD_REDEEM:
            raise ValueError(ERR_REQUEST_MISS_PAYMENT_ACCOUNT_FOR_REDEEM)
        if 'payment_provider' not in biz_content_json and json_input['method'] in [API_METHOD_PURCHASE, API_METHOD_REDEEM]:
            raise ValueError(ERR_REQUEST_MISS_PAYMENT_PROVIDER)

        return TradeAPIRequest(method, json_input['api_key'], '', biz_content_json['out_trade_no'],
            total_fee=biz_content_json.get('total_fee', 0),
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
            original_json_request = json_input, 
            meta_option = biz_content_json.get('meta_option', None),
            pay_option = biz_content_json.get('pay_option', None),
            external_cny_rec_address = json_input.get('external_cny_rec_address', None),
            txid = json_input.get('txid', None))

    def __get_biz_content_json(self):
        biz_content_json = {}
        biz_content_json['out_trade_no'] = self.out_trade_no
        if self.method in ['wallet.trade.buy', 'wallet.trade.sell']:
            biz_content_json['subject'] = self.subject
            biz_content_json['total_fee'] = self.total_fee
            biz_content_json['expire_minute'] = self.expire_minute
            biz_content_json['api_account_type']= 'Account'
            biz_content_json['client_ip'] = self.client_ip
            biz_content_json['payment_provider'] = self.payment_provider
            if self.payment_account:
                biz_content_json['payment_account'] = self.payment_account
            if self.attach:
                biz_content_json['attach'] = self.attach
            if self.meta_option:
                biz_content_json['meta_option'] = self.meta_option
            if self.pay_option:
                biz_content_json['pay_option'] = self.pay_option
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
        if self.external_cny_rec_address is not None:
            jsonobj['external_cny_rec_address'] = self.external_cny_rec_address
        if self.txid is not None:
            jsonobj['txid'] = self.txid

        biz_content_json = self.__get_biz_content_json()

        jsonobj['biz_content'] = json.dumps(biz_content_json, separators=(',',':'), ensure_ascii=False, sort_keys=True)
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
