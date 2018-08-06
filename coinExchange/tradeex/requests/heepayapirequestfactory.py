#!/usr/bin/python
# -*- coding: utf-8 -*-
import time, hashlib
from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller.global_utils import *
from trading.controller import ordermanager
from trading.controller import useraccountinfomanager
from trading.controller.heepaymanager import HeePayManager

class HeepayAPIRequestFactory(object):
    def __init__(self, version, api_key, api_secret, 
                 sign_type = 'MD5', charset_type='utf-8'):
        self.version = version
        self.api_key = api_key
        self.api_secret = api_secret
        self.sign_type = sign_type
        self.charset_type = charset_type

    def __sign(self, json):
        sorted_keys = sorted(json.keys())
        count = 0
        str_to_be_signed = ""
        for key in sorted_keys:
            if count > 0:
                str_to_be_signed = str_to_be_signed + '&'
            str_to_be_signed = '{0}{1}={2}'.format(str_to_be_signed, key, json[key])
            count = count + 1
        str_to_be_signed = str_to_be_signed + '&key=' + self.api_secret
        m = hashlib.md5()
        print("str to be signed {0}".format(str_to_be_signed))
        m.update(str_to_be_signed.encode('utf-8'))
        return m.hexdigest().upper()
    
    def __get_biz_content_json(self, order_id, amount, buyer_account,
             seller_account, async_notify_url, sync_notify_url,
             **kwargs):

        biz_content_json = {}
        biz_content_json['out_trade_no'] = order_id
        biz_content_json['subject'] = '购买{0}'.format(amount)
        biz_content_json['total_fee'] = amount
        biz_content_json['api_account_mode']= 'Account'
        biz_content_json['client_ip'] = '127.0.0.1'

        # TODO: for now,we don't put buyer account
        biz_content_json['to_account'] = seller_account
        if async_notify_url:
            biz_content_json['notify_url'] = async_notify_url
        if sync_notify_url:
            biz_content_json['return_url'] = sync_notify_url

        if kwargs:
            for key, value in kwargs.items():
                if key == 'subject':
                    biz_content_json['subject'] = value
                elif key == 'client_ip':
                    biz_content_json['client_ip'] = value
                elif key == 'api_account_mode':
                    biz_content_json['api_account_mode'] = value
            
        return biz_content_json


    def create_payload(self, order_id, amount,  
            buyer_account, seller_account, async_notify_url, sync_notify_url,
             **kwargs):
        if not order_id:
            raise ValueError('INVALID_PARAM_ORDER_ID_REQUIRED')
            
        heepayAmount = int(round(amount, 2) * 100)
        if heepayAmount < 1:
            raise ValueError('INVALID_PARAM_AMOUNT_TOO_SMALL_FOR_HEEPAY')

        if not seller_account:
            raise ValueError('INVALID_PARAM_SELLER_ACCOUNT_REQUIRED')

        jsonobj = {}
        jsonobj['method'] = 'wallet.pay.apply'
        jsonobj['version'] = self.version
        jsonobj['app_id']= self.api_key
        jsonobj['charset'] = self.charset_type
        jsonobj['sign_type'] = self.sign_type

        epoch_now = time.time()
        frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S")
        #frmt_date = '20171218094803'
        jsonobj['timestamp'] = frmt_date

        biz_content_json = self.__get_biz_content_json(order_id, amount,  
                buyer_account, seller_account, async_notify_url, sync_notify_url,
                kwargs = kwargs)
        jsonobj['biz_content'] = json.dumps(biz_content_json, ensure_ascii=False)
        jsonobj['sign'] =  self.__sign(jsonobj)

        return json.dumps(jsonobj,ensure_ascii=False)

 
