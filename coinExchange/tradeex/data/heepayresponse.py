#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib

class HeepayResponse(object):

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
        m.update(str_to_be_signed.encode('utf-8'))
        return m.hexdigest().upper()
    
    def parseFromJson(self, json_data, api_secret):
        self.api_secret = api_secret
        if 'return_code' not in json_data:
            raise ValueError('Invalid heepay response: missing return_code')
        if 'return_msg' not in json_data:
            raise ValueError('Invalid heepay response: missing return_msg')
        if 'sign' not in json_data:
            raise ValueError('Invalid heepay response: missing sign data')
        if 'result_code' not in json_data:
            raise ValueError('Invalid heepay response: missing result_code')
        if 'result_msg' not in json_data:
            raise ValueError('Invalid heepay response: missing result_msg')

        calculated_sign = self.__sign(json_data)
        if calculated_sign != json_data['sign']:
            raise ValueError('Invalid heepay response: signature does not match.  Expected {0} but got {1}'.format(
                json_data['sign'], calculated_sign
            ))

        self.api_key = json_data['app_id']
        self.subject = json_data['subject']
        self.attach = json_data['attach']
        self.total_fee = json_data['total_fee']
        self.out_trade_no = json_data['out_trade_no']
        self.hy_url = json_data['hy_url']
        self.hy_pay_id = json_data['hy_pay_id']
        self.sign = calculated_sign


        
            
            