#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib

class HeepayNotification(object):

    def __init__(self, api_secret):
        self.api_secret = api_secret
        self.version = None
        self.appkey = None
        self.out_trade_no  = None
        self.hy_bill_no = None
        self.payment_type = None
        self.total_fee = None
        self.trade_status = None
        self.real_fee = None
        self.payment_time = None
        self.attach = None
        self.to_account = None
        self.from_account = None
        self.original_json = None
        self.sign = None

    def __sign(self, json):
        sorted_keys = sorted(json.keys())
        str_to_be_signed = ""
        for key in sorted_keys:
           if key != 'sign':
               str_to_be_signed = '{0}{1}={2}&'.format(str_to_be_signed, key, json[key])
        str_to_be_signed = "{0}key={1}".format(str_to_be_signed, self.api_secret)
        m = hashlib.md5()
        m.update(str_to_be_signed.encode('utf-8'))
        return m.hexdigest().upper()

    @classmethod    
    def parseFromJson(cls, json_data, api_secret, validate_sign = False):
        notify = HeepayNotification(api_secret)
        notify.version = json_data['version']
        notify.appkey = json_data['app_id']
        notify.out_trade_no  = json_data['out_trade_no']
        notify.hy_bill_no = json_data['hy_bill_no']
        notify.payment_type = json_data['payment_type']
        notify.total_fee = json_data['total_fee']
        notify.trade_status = json_data['trade_status']
        notify.real_fee = json_data['real_fee']
        notify.payment_time = json_data['payment_time']
        if 'attach' in json_data:
            notify.attach = json_data['attach']
        if 'to_account' in json_data:
            notify.to_account = json_data['to_account']
        if 'from_account' in json_data:
            notify.from_account = json_data['from_account']
        notify.original_json = json_data

        calculated_sign = notify.__sign(json_data)
        notify.sign = calculated_sign
        if validate_sign and calculated_sign != json_data['sign']:
            raise ValueError('Invalid heepay response: signature does not match.  Expected {0} but got {1}'.format(
                json_data['sign'], calculated_sign
            ))

        return notify