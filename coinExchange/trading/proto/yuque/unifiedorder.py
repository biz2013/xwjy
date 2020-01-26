#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, time, pytz, datetime as dt
import hashlib


class UnifiedOrderRequest(object):

   def __init__(self, apiKey, out_trade_no, product_origin_fee, notify_url, strategy='any', order_ttl=90):
       self.apiKey = apiKey
       self.out_trade_no = out_trade_no
       self.product_origin_fee = product_origin_fee
       self.notify_url = notify_url
       self.strategy = strategy
       self.order_ttl = order_ttl

   def toJson(self):
       jsonobj = {}
       jsonobj['apiKey'] = self.apiKey
       jsonobj['out_trade_no'] = self.out_trade_no
       jsonobj['product_origin_fee']= self.product_origin_fee
       jsonobj['notify_url'] = self.notify_url
       jsonobj['strategy'] = self.strategy
       jsonobj['order_ttl'] = self.order_ttl
       return jsonobj




