#!/usr/bin/python
# -*- coding: utf-8 -*-

from tradeapi.utils import *
from tradeapi.data.traderesponse import APIResponseBase

import json

Version	必填	版本号（1.0）
api_key	必填	用户注册时得到的密锁字符串
out_trade_no	必填	开发者订单号
trx_bill_no	必填	系统 提供的账单号，以便查询
payment_provider	必填	支付服务商（heepay）
Subject	必填	用户下单时填的购买的商品或服务的名称
Attach	选填	开发者扩展参数 
total_amount	必填	总金额(分)
trade_status	必填	交易状态，InProgress =处理中，PaidSuccess =付款成功，Success =交易成功（付款成功，到账成功）
real_fee	必填	实际总金额(分)
received_time	必填	支付完成时间(yyyyMMddHHmmss). 这是UTC
from_account	选填	支付用的账户
to_account	选填	收款人在同一个支付服务商的账户
Sign	必填	签名值


class PurchaseAPINotify(object):
    def __init__(self, version, api_key, out_trade_no, trx_bill_no, 
        payment_provider, subject, total_amount, trade_status, 
        real_fee, received_time, from_account=None, to_account=None, attach = None):
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
        self.sign = sign_api_content(self.__get_content_to_be_signed(), secret_key)
    
    def __get_content_to_be_signed(self):
        content_json = {}
        content_json['version'] = self.return_code
        content_json['return_msg'] = self.return_msg
        return content_json
    
    def to_json(self):
        resp_json = {}
        resp_json['return_code'] = self.return_code
        resp_json['return_msg'] = self.return_msg
        resp_json['result_code'] = self.result_code
        resp_json['result_msg'] = self.result_msg
        resp_json['api_key'] = self.apikey
        resp_json['total_received'] = self.total_received
        resp_json['out_trade_no'] = self.out_trade_no
        resp_json['trx_bill_no'] = self.trx_bill_no
        resp_json['total_received'] = self.total_received
        resp_json['payment_url'] = self.payment_url
        if self.subject:
            resp_json['subject'] = self.subject
        if self.attach:
            resp_json['attach'] = self.attach
        
        resp_json['sign'] = self.sign
        return resp_json