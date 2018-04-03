#!/usr/bin/python
# -*- coding: utf-8 -*-

class APIResponseBase(object):
    def __init__(self, apikey, secret_key, return_code, return_msg,
         result_code, result_msg, out_trade_no, trx_bill_no, **kwargs):
        self.return_code = return_code
        self.return_msg = return_msg
        self.result_code = result_code
        self.result_msg = result_msg
        self.apikey = apikey
        self.secret_key = secret_key
        self.out_trade_no = out_trade_no
        self.trx_bill_no = trx_bill_no
        self.content_to_sign = ""
        self.sign = ""

    def is_valid(self, secret_key):
        return False

    def parse_from_json(self, json):
        raise NotImplementedError("APIResponse:parse_from_json() has not been implemented")
