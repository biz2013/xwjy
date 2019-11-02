#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, time, pytz, datetime as dt
import hashlib


class UnifiedOrderResponse(object):

    def __init__(self, code, msg, inner_trade_no, out_trade_no, apiKey, product_origin_fee, product_real_fee, code_url, expireTime, status):
        self.code = code
        self.msg = msg
        self.inner_trade_no = inner_trade_no
        self.out_trade_no = out_trade_no
        self.apiKey = apiKey
        self.product_origin_fee = product_origin_fee
        self.product_real_fee = product_real_fee
        self.code_url = code_url
        self.expireTime = expireTime
        self.status = status

    @classmethod
    def parseFromJson(cls, json_input):
        code = json_input['code']
        msg = json_input['msg']
        inner_trade_no = json_input['data']['inner_trade_no']
        out_trade_no = json_input['data']['out_trade_no']
        apiKey = json_input['data']['apiKey']
        product_origin_fee = json_input['data']['product_origin_fee']
        product_real_fee = json_input['data']['product_real_fee']
        code_url = json_input['data']['code_url']
        expireTime = json_input['data']['expireTime']
        status = json_input['data']['status']
        return UnifiedOrderResponse(code, msg, inner_trade_no, out_trade_no, apiKey, product_origin_fee, product_real_fee, code_url, expireTime, status)
