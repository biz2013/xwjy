import json
import httplib
import time
import datetime as dt
import hashlib

class HeePayManager(object):
   def __init__(self):
       self.dst = ''

   def create_purchase_order(self, buyer_api_key, buyer_account,
          seller_account, amount, buyerorder_id):
       try:
         """
         https://local.heepay.com/Wallet/Api/v1/PayApply
         """
         conn = httplib.HTTPSConnection('local.heepay.com'])
         pay_url = '/Wallet/Api/v1/PayApply'

        headers = {"Content-Type": "application/json",
                   "charset": "UTF-8"}
        conn.request('POST', payurl, goc_alert_json, headers)
        response = conn.getresponse()
        return response.reason, response.read()

    except httplib.HTTPException as ex:
        logger.error('Error {0}'.format(ex))
        raise ValueError('Exception found during sending alert.[{0}]'.format(ex))
    except:
        logger.error("create_purchase_order:Unexpected error:", sys.exc_info()[0])
        raise

"""
{"sign":"19D4E6B0418D4F47CDE76BF3AA1B50AD"}
"""
