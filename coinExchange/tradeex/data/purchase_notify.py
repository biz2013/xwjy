#!/usr/bin/python
# -*- coding: utf-8 -*-

from tradeex.utils import *

import json

class PurchaseAPINotify(object):
    def __init__(self, version, api_key, secret_key, out_trade_no, trx_bill_no, 
        payment_provider, subject, total_amount, trade_status, 
        real_fee, received_time, from_account=None, to_account=None, attach = None,
        txid = None):
        self.version = version
        self.api_key = api_key
        self.out_trade_no = out_trade_no
        self.trx_bill_no = trx_bill_no
        self.payment_provider = payment_provider
        self.subject = subject
        self.attach = attach
        self.total_amount = total_amount
        self.real_fee = real_fee
        self.received_time = received_time
        self.trade_status = trade_status
        self.from_account = from_account
        self.to_account = to_account
        self.txid = txid
        self.sign = sign_api_content(self.__get_content_to_be_signed(), secret_key)
    
    def __get_content_to_be_signed(self):
        content_json = {}
        content_json['version'] = self.version
        content_json['api_key'] = self.api_key
        content_json['out_trade_no'] = self.out_trade_no
        content_json['trx_bill_no'] = self.trx_bill_no 
        content_json['payment_provider'] = self.payment_provider
        content_json['subject'] = self.subject
        if self.attach:
            content_json['attach'] = self.attach
        content_json['total_amount'] = self.total_amount
        content_json['real_fee'] = self.real_fee
        content_json['received_time'] = self.received_time
        content_json['trade_status'] = self.trade_status
        if self.from_account:
            content_json['from_account'] = self.from_account
        if self.to_account:
            content_json['to_account'] = self.to_account
        if self.txid:
            content_json['txid'] = self.txid

        return content_json
    
    def to_json(self):
        resp_json = self.__get_content_to_be_signed()
        resp_json['sign'] = self.sign
        return resp_json
