#!/usr/bin/python
# -*- coding: utf-8 -*-

from tradeex.utils import *
from tradeex.data.traderesponse import APIResponseBase

import json

class TradeAPIResponse(APIResponseBase):
    def __init__(self, apikey, secret_key, return_code, return_msg, result_code, 
            result_msg, out_trade_no, trx_bill_no, **kwargs):
        super(TradeAPIResponse, self).__init__(apikey, return_code, 
            return_msg, result_code, result_msg,
            out_trade_no, trx_bill_no, **kwargs)
        self.subject = None
        self.attach = None
        self.total_fee = 0
        self.payment_url = None
        self.trade_status = 'UNKNOWN'
        if kwargs:
            for key,value in kwargs.items():
                if key == 'subject':
                    self.subject = value
                elif key == 'attach':
                    self.attach = value
                elif key == 'total_fee':
                    self.total_fee = value
                elif key == 'payment_url':
                    self.payment_url = value
                elif key == 'trade_status':
                    self.trade_status = value
        
        #if 'SUCCESS' == self.return_code:
        #    if not self.payment_url:
        #        raise ValueError('PurchaseAPIResponse: miss payment_url')
        #    if 0 == self.total_fee
        #        raise ValueError('PurchaseAPIResponse: miss total_fee')

        self.sign = sign_api_content(self.__get_content_to_be_signed(), secret_key)
    
    def __get_content_to_be_signed(self):
        content_json = {}
        content_json['return_code'] = self.return_code
        content_json['return_msg'] = self.return_msg
        return content_json
    
    def to_json(self):
        resp_json = {}
        resp_json['return_code'] = self.return_code
        resp_json['return_msg'] = self.return_msg
        resp_json['result_code'] = self.result_code
        resp_json['result_msg'] = self.result_msg
        resp_json['api_key'] = self.apikey
        resp_json['total_fee'] = self.total_fee
        resp_json['out_trade_no'] = self.out_trade_no
        resp_json['trx_bill_no'] = self.trx_bill_no
        if self.payment_url:
            resp_json['payment_url'] = self.payment_url
        if self.subject:
            resp_json['subject'] = self.subject
        if self.attach:
            resp_json['attach'] = self.attach
        if self.trade_status:
            resp_json['trade_status'] = self.trade_status
            
        resp_json['sign'] = self.sign
        return resp_json
