#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import sys, os
import http.client
import time
import pytz
import datetime as dt
import hashlib
import shutil
import qrcode
import logging

logger = logging.getLogger("site.heepaymanager")

class HeePayManager(object):
   def __init__(self):
       self.dst = ''

   def create_heepay_payload(self, wallet_action, order_id_str, app_id, app_key,
         client_ip, amount, seller_account, buyer_account, notify_url,
         return_url):
       jsonobj = {}
       jsonobj['method'] = wallet_action
       jsonobj['version'] = '1.0'
       jsonobj['app_id']= app_id
       jsonobj['charset'] = 'utf-8'
       jsonobj['sign_type'] = 'MD5'
       epoch_now = time.time()
       frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S")
       #frmt_date = '20171218094803'
       jsonobj['timestamp'] = frmt_date
       biz_content = '{\"out_trade_no\":\"%s\",' % (order_id_str)
       amount_in_dollar = round(amount, 2)
       amount_str = str(int(amount_in_dollar)*100)
       biz_content = biz_content + ('\"subject\":\"购买{0}元\",'.format(amount_str))
       biz_content = biz_content + ('\"total_fee\":\"{0}\",'.format(amount_str))
       biz_content = biz_content + ('\"api_account_mode\":\"Account\",')
       #biz_content = biz_content + ('\"from_account\":\"{0}\",'.format(buyer_account))
       biz_content = biz_content + ('\"to_account\":\"{0}\",'.format(seller_account))
       biz_content = biz_content + ('\"client_ip\":\"%s\"' % (client_ip))
       if notify_url is not None and len(notify_url) > 0:
          biz_content = biz_content + ',\"notify_url\":\"%s\"' % notify_url
       if return_url is not None and len(return_url) > 0:
          full_return_url = '{0}?order_id={1}'.format(return_url, order_id_str) if return_url.endswith('/') else '{0}/?order_id={1}'.format(return_url, order_id_str)
          biz_content = biz_content + ',\"return_url\":\"%s\"' % full_return_url
       biz_content = biz_content  + '}'
       jsonobj['biz_content'] = biz_content

       m = hashlib.md5()
       content_to_signed = 'app_id=%s&biz_content=%s&charset=utf-8&method=%s&sign_type=MD5&timestamp=%s&version=1.0&key=%s' % (
                      app_id,
                      biz_content,
                      wallet_action, frmt_date,
                      app_key)
       logger.info('content to be signed: {0}'.format(content_to_signed))
       m.update(content_to_signed.encode('utf-8'))
       signed_str = m.hexdigest()
       jsonobj['sign'] =  signed_str.upper()

       return json.dumps(jsonobj,ensure_ascii=False)

   def send_inquiry_request(self, payload):
       conn = http.client.HTTPSConnection('wallet.heepay.com')
       pay_url = '/Api/v1/PayQuery'
       logger.info('the payload is {0}'.format(payload))
       headers = {"Content-Type": "application/json",
               "charset": "UTF-8"}
       conn.request('POST', pay_url, payload.encode('utf-8'), headers)
       response = conn.getresponse()
       return response.status, response.reason, response.read().decode('utf-8')

   def send_buy_apply_request(self, payload):
       conn = http.client.HTTPSConnection('wallet.heepay.com')
       pay_url = '/Api/v1/PayApply'
       logger.info('the payload is {0}'.format(payload))
       headers = {"Content-Type": "application/json",
               "charset": "UTF-8"}
       conn.request('POST', pay_url, payload.encode('utf-8'), headers)
       response = conn.getresponse()
       return response.status, response.reason, response.read().decode('utf-8')


   def generate_heepay_qrcode(self, heepay_response_json, media_root):
       qrcode_filename = '{0}_{1}.png'.format(
          heepay_response_json['out_trade_no'],
          heepay_response_json['hy_bill_no']
       )
       dst = os.path.join(media_root, 'qrcode', qrcode_filename)
       content = heepay_response_json['hy_url'].encode('utf8')
       logger.info('generate qrcode for {0} refers to hy_bill_no {1} into path {2}'.format(
           content, heepay_response_json['hy_bill_no'], dst))
       myQR = qrcode.QRCode(
               version = 1,
               error_correction = qrcode.constants.ERROR_CORRECT_H,
               box_size = 6,
               border = 2,
              )
       myQR.add_data(content)
       img = myQR.make_image()
       img.save(dst)
       img_path = os.path.join('qrcode', qrcode_filename)
       return img_path

   def create_confirmation_sign(self, json_data, app_key):
       keylist = sorted(json_data.keys())
       content = ''
       for key in keylist:
           if key != 'sign':
              content = "{0}{1}={2}&".format(content, key, json_data[key])
       content = "{0}key={1}".format(content, app_key)
       m = hashlib.md5()
       logger.info('the content to be verified with signature: {0}'.format(content))
       m.update(content.encode('utf-8'))
       signed_str = m.hexdigest().upper()
       return signed_str

   def confirmation_is_valid(self, json_data, app_key):
       signed_str = self.create_confirmation_sign(json_data, app_key)
       logger.info('the signed of content is {0} and the original sign is {1}'.format(
             signed_str, json_data['sign']
       ))
       return signed_str == json_data['sign']


   def get_payment_status(self, orderId, hy_bill_no, appId, app_key):
       logger.info('get_payment_status({0},{1})'.format(orderId, hy_bill_no))
       jsonobj = {}
       jsonobj['method'] = 'wallet.pay.query'
       jsonobj['version'] = '1.0'
       jsonobj['app_id']= appId
       jsonobj['charset'] = 'UTF-8'
       jsonobj['sign_type'] = 'MD5'
       epoch_now = time.time()
       frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S")
       #frmt_date = '20171218094803'
       jsonobj['timestamp'] = frmt_date
       biz_content = '{\"hy_bill_no\":\"%s\",' % (hy_bill_no)
       biz_content = biz_content + '\"out_trade_no\":\"%s\"}' % (orderId)
       jsonobj['biz_content'] = biz_content

       m = hashlib.md5()
       content_to_signed = 'app_id=%s&biz_content=%s&charset=%s&method=%s&sign_type=MD5&timestamp=%s&version=1.0&key=%s' % (
                      appId,
                      biz_content,
                      jsonobj['charset'],
                      'wallet.pay.query', frmt_date,
                      app_key)
       logger.info('get_payment_status(): content to be signed: {0}'.format(content_to_signed))
       m.update(content_to_signed.encode('utf-8'))
       signed_str = m.hexdigest()
       jsonobj['sign'] =  signed_str.upper()

       payload = json.dumps(jsonobj,ensure_ascii=False)
       status, reason, message = self.send_inquiry_request(payload)
       logger.info("query payment status {0} {1} return status {2} message {3}".format(orderId, hy_bill_no, status, message))

       if status != 200:
           logger.error("Calling heepay failed with {0}:{1} {2}".format(status, reason, message))
           return 'UNKNOWN'
       json_response = json.loads(message)

       if json_response['return_code'] != 'SUCCESS':
           logger.error('Heepay report failure: %s' % (json_response['return_msg']))
       if 'result_code' in json_response:
           if json_response['result_code'] != 'SUCCESS' and 'result_msg' in json_response:
               logger.error('Heepay return result message: {0}'.format(json_response['result_msg']))
       if 'hy_bill_no' in json_response and json_response['hy_bill_no'] != hy_bill_no:
           logger.error("Mismatch Bill No: response bill no is {0}, expected {1}".format(json_response['hy_bill_no'], hy_bill_no))
       return json_response


   def cancel_payment(self, orderId, hy_bill_no, appId, app_key):
       pass

"""
{"sign":"19D4E6B0418D4F47CDE76BF3AA1B50AD"}
"""
