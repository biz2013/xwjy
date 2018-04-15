#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib

class HeepayResponse(object):

    def __init__(self, api_secret):
        self.api_secret = api_secret

    def __sign(self, json):
        sorted_keys = sorted(json.keys())
        count = 0
        str_to_be_signed = ""
        for key in sorted_keys:
            if key.startswith('return'):
                continue
            if count > 0:
                str_to_be_signed = str_to_be_signed + '&'
            str_to_be_signed = '{0}{1}={2}'.format(str_to_be_signed, key, json[key])
            count = count + 1
        str_to_be_signed = str_to_be_signed + '&key=' + self.api_secret
        m = hashlib.md5()
        m.update(str_to_be_signed.encode('utf-8'))
        return m.hexdigest().upper()

    @classmethod    
    def parseFromJson(cls, json_data, api_secret):
        resp = HeepayResponse(api_secret)
        if 'return_code' not in json_data:
            raise ValueError('Invalid heepay response: missing return_code')
        if 'return_msg' not in json_data:
            raise ValueError('Invalid heepay response: missing return_msg')
        if 'sign' not in json_data:
            raise ValueError('Invalid heepay response: missing sign data')
        if json_data['return_code'] == 'SUCCESS':
            if 'result_code' not in json_data:
                raise ValueError('Invalid heepay response: missing result_code')
            if 'result_msg' not in json_data:
                raise ValueError('Invalid heepay response: missing result_msg')
        else:
            if 'result_code' in json_data:
                raise ValueError('Invalid heepay response: result_code field should not exist if return_code=FAIL')
            if 'result_msg' in json_data:
                raise ValueError('Invalid heepay response: result_msg field should not exist if return_code=FAIL')

        calculated_sign = resp.__sign(json_data)
        resp.sign = calculated_sign
        #if calculated_sign != json_data['sign']:
        #    raise ValueError('Invalid heepay response: signature does not match.  Expected {0} but got {1}'.format(
        #        json_data['sign'], calculated_sign
        #    ))

        if json_data['return_code'] =='SUCCESS' and 'result_code' in json_data:
            resp.api_key = json_data['app_id']
            resp.subject = json_data['subject']
            resp.attach = json_data.get('attach', None)
            resp.total_fee = json_data['total_fee']
            resp.out_trade_no = json_data['out_trade_no']
            resp.hy_url = json_data['hy_url']
            resp.hy_pay_id = json_data['hy_pay_id']


        
            
            