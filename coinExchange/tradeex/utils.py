#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import hashlib
import logging, json
import hmac
import string
import random

from tradeex.controllers.apiusermanager import APIUserManager

logger = logging.getLogger("tradeex.utils")

def sign_api_content(json_input, secret_key):
    logger.debug("sign_api_content({0})".format(json.dumps(json_input, ensure_ascii=False)))
    sorted_keys = sorted(json_input.keys())
    str_to_be_signed = ""
    for key in sorted_keys:
        str_to_be_signed = '{0}{1}={2}&'.format(str_to_be_signed, key, json_input[key])
    str_to_be_signed = '{0}key={1}'.format(str_to_be_signed, secret_key)
    m = hashlib.md5()
    logger.debug("sign_api_content(): str to be signed {0}".format(str_to_be_signed))
    m.update(str_to_be_signed.encode('utf-8'))
    return m.hexdigest().upper()


def create_return_msg_from_valueError(valueError):
    msg_map= {
        'PAYMENT_ACCOUNT_NOT_FOUND':'数据错误:通知系统服务',
        'TOO_MANY_ACCOUNTS_AT_PROVIDER': '数据错误:通知系统服务',
        'NOT_SELL_ORDER_FOUND':'数据错误:通知系统服务',
        'NOT_SELL_ORDER_CAN_BE_LOCKED':'数据错误:通知系统服务',
        'USER_NOT_FOUND_WITH_API_KEY':'未找到您的账户:通知系统服务'
    }
    return msg_map[valueError] if valueError in msg_map else '系统错误:通知系统服务'

def create_result_msg_from_valueError(valueError):
    msg_map= {
        'PAYMENT_ACCOUNT_NOT_FOUND':'数据错误:通知系统服务',
        'TOO_MANY_ACCOUNTS_AT_PROVIDER': '数据错误:通知系统服务',
        'NOT_SELL_ORDER_FOUND':'数据错误:通知系统服务',
        'NOT_SELL_ORDER_CAN_BE_LOCKED':'数据错误:通知系统服务'
    }
    return msg_map[valueError] if valueError in msg_map else '系统错误:通知系统服务'

def heepay_status_to_trade_status(status):
    states_map ={ 'NotStart'.upper(): 'NotStarted',
           'PaySuccess'.upper(): 'PaidSuccess',
           'Success'.upper(): 'PaidSuccess',
           'ExpiredInvalid'.upper(): 'ExpiredInvalid',
           'DevClose'.upper(): 'DevClose',
           'UserAbandon'.upper(): 'UserAbandon',
           'UnKnow'.upper(): 'UnKnown',
           'Failure'.upper(): 'Failure',
           'Starting'.upper(): 'InProgress'}

    return states_map[status.upper()] if status.upper() in states_map else 'UnKown'


# id_generator creates random user id, by default is 16 characters combined with upper case letter and digits.
def id_generator(size=16, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# create_access_keys creates pair of user id and user access key, access key is md5 hash of user id + random string.
# return {user_access_key_id, user_access_key}
def create_access_keys(api_id):
    digest_maker = hmac.new(api_id.encode('utf-8'))
    random_factor = id_generator(3)
    digest_maker.update(random_factor.encode('utf-8'))

    access_key = digest_maker.hexdigest()
    return access_key

# used by API transaction to get the external cnyf address to transfer CNYF to.
# this is used by both purchase and redeem.  In purchase, when the purchase is
# succeeeded, CNYF will be transfered to the external cnyf address.  In redeem,
# if redeem fails, CNYF will be returned to the external cnyf address
def get_api_trans_external_cnyf_address(api_tran):
    external_crypto_addr = api_trans.external_cny_receive_addr

    # if there is no external cny address from user request (save as api transaction), read from APIUserExternalWalletAddress
    if not external_crypto_addr:
        logger.info("get_api_trans_external_cnyf_address({0}): could not find external cny receive addr in the request.  Try to read from the external wallet address table")
        external_crypto_addr = APIUserManager.get_api_user_external_crypto_addr(api_trans.api_user.user.id, 'CNY')

    return external_crypto_addr
