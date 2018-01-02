#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import sys, os
import httplib
import time
import pytz
import datetime as dt
import hashlib
import shutil
import qrtools
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
       biz_content = biz_content + ('\"subject\":\"购买%fCNY\",' %(amount))
       biz_content = biz_content + ('\"total_fee\":\"1\",')
       biz_content = biz_content + ('\"api_account_mode\":\"Account\",')
       #biz_content = biz_content + ('\"from_account\":\"{0}\",'.format(buyer_account))
       biz_content = biz_content + ('\"to_account\":\"{0}\",'.format(seller_account))
       biz_content = biz_content + ('\"client_ip\":\"%s\"' % (client_ip))
       if notify_url is not None and len(notify_url) > 0:
          biz_content = biz_content + ',\"notify_url\":\"%s\"' % notify_url
       if return_url is not None and len(return_url) > 0:
          biz_content = biz_content + ',\"return_url\":\"%s\"' % return_url
       biz_content = biz_content  + '}'
       jsonobj['biz_content'] = biz_content

       m = hashlib.md5()
       content_to_signed = 'app_id=%s&biz_content=%s&charset=utf-8&method=%s&sign_type=MD5&timestamp=%s&version=1.0&key=%s' % (
                      app_id,
                      biz_content,
                      wallet_action, frmt_date,
                      app_key)
       logger.info('content to be signed: {0}'.format(content_to_signed))
       m.update(content_to_signed)
       signed_str = m.hexdigest()
       jsonobj['sign'] =  signed_str.upper()

       return json.dumps(jsonobj,ensure_ascii=False)

   def send_buy_apply_request(self, payload):
       conn = httplib.HTTPSConnection('wallet.heepay.com')
       pay_url = '/Api/v1/PayApply'
       logger.info('the payload is {0}'.format(payload))
       headers = {"Content-Type": "application/json",
               "charset": "UTF-8"}
       conn.request('POST', pay_url, payload, headers)
       response = conn.getresponse()
       return response.status, response.reason, response.read()


   def generate_heepay_qrcode(self, heepay_response_json, media_root):
       qrcode_filename = '{0}_{1}.png'.format(
          heepay_response_json['out_trade_no'],
          heepay_response_json['hy_bill_no']
       )
       dst = os.path.join(media_root, 'qrcode', qrcode_filename)
       content = heepay_response_json['hy_url'].encode('utf8')
       logger.info('generate qrcode for {0} refers to hy_bill_no {1}'.format(
           content, heepay_response_json['hy_bill_no']))
       myQR = qrtools.QR(data=content, pixel_size=6)
       myQR.encode()
       shutil.move(myQR.filename, dst)
       img_path = os.path.join('qrcode', qrcode_filename)
       return img_path

"""
{"sign":"19D4E6B0418D4F47CDE76BF3AA1B50AD"}
"""
