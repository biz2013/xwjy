#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, time, pytz, datetime as dt
import hashlib
import logging

from tradeapi.utils import *

logger = logging.getLogger("tradeapi.purchaserequest")

class PurchaseAPIRequest(object):

   def __init__(self, apikey, secret_key, out_trade_no, total_fee, 
           payment_provider, payment_account, client_ip,
           subject='人民币充值', attach=None, notify_url=None, return_url=None,
           version='1.0', charset='utf-8', sign_type='MD5', timestamp=0,
           sign = ''):
        self.version = version
        self.charset = charset
        self.sign_type = sign_type
        self.method = 'wallet.trade.buy'
        self.apikey = apikey.upper()
        self.secret_key = secret_key.upper()
        self.out_trade_no = out_trade_no
        self.total_fee = total_fee
        self.client_ip = client_ip
        self.payment_provider = payment_provider
        self.payment_account = payment_account
        self.subject = subject
        self.attach = attach
        self.return_url = return_url
        self.notify_url= notify_url
        self.timestamp = timestamp
        self.sign = sign
        self.meta_option = None

   @classmethod
   def parseFromJson(cls, json_input):
        method = json_input['method']
        if method != 'wallet.trade.buy':
            raise ValueError('Unexpected PrepurchaseRequest method. Expected: wallet.trade.buy actual:{0}'.format(method))

        biz_content_json = json.loads(json_input['biz_content'])
        return PurchaseAPIRequest(json_input['api_key'], '', biz_content_json['out_trade_no'],
            float(biz_content_json['total_fee']),
            biz_content_json['payment_provider'],
            biz_content_json['payment_account'],
            biz_content_json['client_ip'],
            biz_content_json['subject'],
            attach = biz_content_json.get('attach', None),
            notify_url= biz_content_json.get('notify_url', None),
            return_url= biz_content_json.get('return_url', None),
            version = json_input['version'],
            charset = json_input['charset'],
            sign_type = json_input['sign_type'],
            timestamp = biz_content_json.get('timestamp', 0),
            sign = json_input['sign'])

   def __get_biz_content_json(self):
       biz_content_json = {}
       biz_content_json['out_trade_no'] = self.out_trade_no
       biz_content_json['subject'] = self.subject
       amount_str = str(round(self.total_fee,2))
       biz_content_json['total_fee'] = amount_str
       biz_content_json['api_account_mode']= 'Account'
       biz_content_json['client_ip'] = self.client_ip
       biz_content_json['payment_provider'] = self.payment_provider
       biz_content_json['payment_account'] = self.payment_account
       if self.meta_option:
           biz_content_json['meta_option'] = self.meta_option
       if self.notify_url:
          biz_content_json['notify_url'] = self.notify_url
       if self.return_url:
          biz_content_json['return_url'] = self.return_url
       return biz_content_json

   def is_valid(self, secret_key):
       self.secret_key = secret_key
       signed = sign_api_content(self.__get_biz_content_json(), secret_key)
       return signed == self.sign

   def getPayload(self):
       jsonobj = {}
       jsonobj['method'] = self.method
       jsonobj['version'] = '1.0'
       jsonobj['api_key']= self.apikey
       jsonobj['charset'] = 'utf-8'
       jsonobj['sign_type'] = 'MD5'
       epoch_now = time.time()
       frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S")
       #frmt_date = '20171218094803'
       jsonobj['timestamp'] = frmt_date
       biz_content_json = self.__get_biz_content_json()

       jsonobj['biz_content'] = json.dumps(biz_content_json, ensure_ascii=False)
       jsonobj['sign'] =  sign_api_content(biz_content_json, self.secret_key)

       return json.dumps(jsonobj, ensure_ascii=False)
