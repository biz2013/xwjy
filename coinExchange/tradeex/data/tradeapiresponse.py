#!/usr/bin/python
# -*- coding: utf-8 -*-
import json

from tradeex.utils import *

class TradeAPIResponse(object):
    def __init__(self, apikey, secret_key, return_code, return_msg, result_code, 
            result_msg, out_trade_no, trx_bill_no, **kwargs):

        self.return_code = return_code
        self.return_msg = return_msg
        self.result_code = result_code
        self.result_msg = result_msg
        self.apikey = apikey
        self.out_trade_no = out_trade_no
        self.trx_bill_no = trx_bill_no
        self.content_to_sign = ""
        self.sign = ""
        self.subject = None
        self.attach = None
        self.total_fee = 0
        self.payment_url = None
        self.trade_status = 'UNKNOWN'
        self.paypal_payment_id = None
        if kwargs:
            for key,value in kwargs.items():
                if key == 'subject':
                    self.subject = value
                elif key == 'attach':
                    self.attach = value
                elif key == 'total_fee':
                    self.total_fee = int(value) if type(value) is str else value
                elif key == 'payment_url':
                    self.payment_url = value
                elif key == 'trade_status':
                    self.trade_status = value
                elif key == 'paypal_payment_id':
                    self.paypal_payment_id = value
        
        #if 'SUCCESS' == self.return_code:
        #    if not self.payment_url:
        #        raise ValueError('PurchaseAPIResponse: miss payment_url')
        #    if 0 == self.total_fee
        #        raise ValueError('PurchaseAPIResponse: miss total_fee')
        self.sign = sign_api_content(self.__get_content_to_be_signed(), secret_key) if secret_key else ''
    
    def __get_content_to_be_signed(self):
        content_json = {}
        content_json['return_code'] = self.return_code
        content_json['return_msg'] = self.return_msg
        if self.subject:
            content_json['subject'] = self.subject
        if self.attach:
            content_json['attach'] = self.attach
        if self.total_fee > 0:
            content_json['total_fee'] = self.total_fee
        if self.payment_url:
            content_json['payment_url'] = self.payment_url
        if self.paypal_payment_id:
            content_json['paypal_payment_id'] = self.paypal_payment_id
        content_json['trade_status'] =self.trade_status
        return content_json
    
    def to_json(self):
        resp_json = {}
        resp_json['return_code'] = self.return_code
        resp_json['return_msg'] = self.return_msg
        if self.sign:
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
            if self.paypal_payment_id:
                resp_json['paypal_payment_id'] = self.paypal_payment_id
                
            resp_json['sign'] = self.sign
        return resp_json
