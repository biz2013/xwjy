import json
import httplib
import time
import datetime as dt
import hashlib

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
       jsonobj['sign_type'] = 'MD5',
       epoch_now = time.time()
       frmt_date = dt.datetime.utcfromtimestamp(epoch_now).strftime("%Y/%m/%d%H:%M%s")
       jsonobj['timestamp'] = frmt_date,
       biz_content = '{\"out_trade_no\":\"%s\",' % (order_id_str)
       biz_content = biz_content + ('\"subject\":\"购买付款%f\",' % (amount))
       biz_content = biz_content + ('\"total_fee\":\"1\",')
       biz_content = biz_content + ('\"api_account_mode\":\"Account\",')
       biz_content = biz_content + ('\"to_account\":\"%s\",' % (seller_account))
       biz_content = biz_content + ('\"client_ip\":\"%s\",' % (client_ip))
       biz_content = biz_content + '\"notify_url\":\"https://demowallet.heepay.com/Test/Api/RecNotifyUrl.aspx\",'
       biz_content = biz_content + '\"return_url\":\"https://demowallet.heepay.com/Test/Api/RecReturnUrl.aspx\"}",'
       jsonobj['biz_content'] = biz_content
       if notify_url is not None and len(notify_url) > 0:
          jsonobj['notify_url'] = notify_url
       else:
          jsonobj['return_url'] = return_url

       m = hashlib.md5()
       sign_content = 'app_id=%s&biz_content=%s&charset=UTF-8&method=%s&sign_type=MD5&timestamp=%s&version=1.0&key=%s' % (app_id, biz_content, wallet_action, frmt_dat, app_key)
       m.update(signed_content)
       signed_str = m.hexidigest()
       jsonobj['sign'] =  signed_str
           return json.dump(jsonobj)

   def send_buy_apply_request(self, payload):
       try:
         """
         https://local.heepay.com/Wallet/Api/v1/PayApply
         """
         conn = httplib.HTTPSConnection('local.heepay.com'])
         pay_url = '/Wallet/Api/v1/PayApply'

         headers = {"Content-Type": "application/json",
                   "charset": "UTF-8"}
         conn.request('POST', payurl, payload, headers)
         response = conn.getresponse()
         return response.code, response.reason, response.read()

    except httplib.HTTPException as ex:
        logger.error('Error {0}'.format(ex))
        raise ValueError('Exception found during sending alert.[{0}]'.format(ex))
    except:
        logger.error("create_purchase_order:Unexpected error:", sys.exc_info()[0])
        raise

"""
{"sign":"19D4E6B0418D4F47CDE76BF3AA1B50AD"}
"""
