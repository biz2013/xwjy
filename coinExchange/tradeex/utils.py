#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
sys.path.append('../stakingsvc/')

from tradeapi.data.tradeapiresponse import TradeAPIResponse

def create_return_msg_from_valueError(valueError):
    msg_map= {
        'PAYMENT_ACCOUNT_NOT_FOUND':'数据错误:通知系统服务',
        'TOO_MANY_ACCOUNTS_AT_PROVIDER': '数据错误:通知系统服务',
        'NOT_SELL_ORDER_FOUND':'数据错误:通知系统服务',
        'NOT_SELL_ORDER_CAN_BE_LOCKED':'数据错误:通知系统服务'
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
    states_map ={ 'NotStart'.upper(), 'NotStarted',
           'PaySuccess'.upper(), 'PaidSuccess',
           'Success'.upper(), 'PaidSuccess',
           'ExpiredInvalid'.upper(), 'ExpiredInvalid',
           'DevClose'.upper(), 'DevClose',
           'UserAbandon'.upper(), 'UserAbandon',
           'UnKnow'.upper, 'UnKnown',
           'Failure'.upper(), 'Failure',
           'Starting'.upper(), 'InProgress'}

    return states_map[status.upper()] if status.upper() in states_map else 'UnKown' 
