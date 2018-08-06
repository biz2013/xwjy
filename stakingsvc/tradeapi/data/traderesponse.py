#!/usr/bin/python
# -*- coding: utf-8 -*-
from tradeapi.utils import *

class APIResponseBase(object):
    def __init__(self, apikey, return_code, return_msg,
         result_code, result_msg, out_trade_no, trx_bill_no, **kwargs):
        self.return_code = return_code
        self.return_msg = return_msg
        self.result_code = result_code
        self.result_msg = result_msg
        self.apikey = apikey
        self.out_trade_no = out_trade_no
        self.trx_bill_no = trx_bill_no
        self.content_to_sign = ""
        self.sign = ""
