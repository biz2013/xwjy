#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, time, pytz, datetime as dt
import hashlib


class PrepurchaseRequest(object):

   def __init__(self, apiKey, secret_key, order_id, total_fee, client_ip,
           subject='人民币充值', attached='', notify_url='', return_url='',
           version='1.0', charset='utf-8', sign_type='MD5', timestamp=0,
           sign = ''):
       self.version = version
       self.charset = charset
       self.sign_type = sign_type
       self.method = 'wallet.trade.buy'
       self.apiKey = apiKey
       self.secret_key = secret_key
       self.order_id = order_id
       self.total_fee = total_fee
       self.client_ip = client_ip
       self.subject = subject
       self.attached = attached
       self.return_url = return_url
       self.notify_url= notify_url
       self.timestamp = timestamp
       self.sign = sign

   @classmethod
   def parseFromJson(cls, json_input):
       method = json_input['method']
       if method != 'wallet.trade.buy':
           raise ValueError('Unexpected PrepurchaseRequest method. Expected: wallet.trade.buy actual:{0}'.format(method))

       biz_content_json = json.loads(json_input['biz_content'])
       return cls(json_input['api_key'], '', biz_content_json['out_trade_no'],
           biz_content_json['total_fee'],
           biz_content_json['clientip'],
           biz_content_json['subject'],
           attached = biz_content_json.get('attached', None),
           notify_url= biz_content_json.get('notify_url', None),
           return_url= biz_content_json.get('return_url', None),
           version = json_input['version'],
           charset = json_input['charset'],
           sign_type = json_input['sign_type'],
           timestamp = biz_content_json.get('timestamp', 0),
           sign = json_input['sign'])
   def __sign(self, json):
       sorted_keys = sorted(json.keys())
       count = 0
       str_to_be_signed = ""
       for key in sorted_keys:
           if count > 0:
               str_to_be_signed = '&' + str_to_be_signed
           str_to_be_signed = '{0}{1}={2}'.format(str_to_be_signed, key, json[key])
           count = count + 1
       m = hashlib.md5()
       m.update(str_to_be_signed.encode('utf-8'))
       return m.hexdigest().upper()

   def __get_biz_content_json(self):
       biz_content_json = {}
       biz_content_json['out_trade_no'] = self.order_id
       biz_content_json['subject'] = self.subject
       amount_str = str(int(round(self.total_fee, 2)*100))
       biz_content_json['total_fee'] = amount_str
       biz_content_json['api_account_mode']= 'Account'

       biz_content_json['client_ip'] = self.client_ip
       if self.notify_url is not None and len(self.notify_url) > 0:
          biz_content_json['notify_url'] = self.notify_url
       if self.return_url is not None and len(self.return_url) > 0:
          biz_content_json['return_url'] = self.return_url
       return biz_content_json

   def validate(self, secret_key):
       signed = self.__sign(self.__get_biz_content_json())
       return signed == self.sign
       
   def getPayload(self):
       jsonobj = {}
       jsonobj['method'] = self.method
       jsonobj['version'] = '1.0'
       jsonobj['api_key']= self.apiKey
       jsonobj['charset'] = 'utf-8'
       jsonobj['sign_type'] = 'MD5'
       epoch_now = time.time()
       frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S")
       #frmt_date = '20171218094803'
       jsonobj['timestamp'] = frmt_date
       biz_content_json = self.__get_biz_content_json()

       jsonobj['biz_content'] = json.dumps(biz_content_json, ensure_ascii=False)
       jsonobj['sign'] =  self.__sign(biz_content_json)

       return json.dumps(jsonobj,ensure_ascii=False)
