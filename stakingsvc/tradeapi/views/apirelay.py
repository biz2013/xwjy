#!/usr/bin/python
# -*- coding: utf-8 -*-

import json, logging, sys

from django.conf import settings
from django.http import JsonResponse

from tradeapi.data.api_const import *
from tradeapi.data.tradeapirequest import TradeAPIRequest
from tradeapi.apiclient import APIClient
from tradeapi.walletmanager import WalletManager

logger = logging.getLogger("tradingapi.apirelay")
def handleValueError(ve_msg):
    resp_json = {}
    resp_json['return_code'] = 'FAILED'
    if ve_msg == ERR_INVALID_SIGNATURE:
        resp_json['return_msg'] = '签名不符'
    elif ve_msg == ERR_USER_NOT_FOUND_BASED_ON_APPID:
        resp_json['return_msg'] = '用户不存在'
    elif ve_msg == ERR_MORE_THAN_ONE_USER_BASED_ON_APPID:
        resp_json['return_msg'] = '用户有多于一个账户'
    elif ve_msg == ERR_UNEXPECTED_METHOD:
        resp_json['return_msg'] = '错误指令'
        resp_json['result_code'] = 'FAILED'
        pos = ve_msg.find('expected:')
        parts = ve_msg[pos:].split(',')
        key_value_parts1 = parts[0].split[':']
        expected = key_value_parts1[1]
        key_value_parts2 = parts[1].split[':']
        actual = key_value_parts2[1]
        resp_json['result_msg'] = '期望指令: {0}, 实际指令: {1}'.format(expected, actual)
    elif ve_msg == ERR_OVER_TRANS_LIMIT:
        resp_json['return_msg'] = '交易超额'
        resp_json['result_code'] = 'FAILED'
        resp_json['result_msg'] = '每笔交易上限为{0}分'.format(settings.API_TRANS_LIMIT)
    elif ve_msg == ERR_NO_RIGHT_SELL_ORDER_FOUND:
        resp_json['return_msg'] = '无卖单提供充值'
    else:
        resp_json['return_msg'] = '数据错误'
    return JsonResponse(resp_json)

def purchase(request):
    try:
        request_json = json.loads(request.body.decode('utf-8'))
        request_obj = TradeAPIRequest.parseFromJson(request_json)
        if request_obj != API_METHOD_PURCHASE:
            raise ValueError('{0}: expected:{1}, actual:{2}'.format(
                ERR_UNEXPECTED_METHOD,
                API_METHOD_PURCHASE, request_obj.method))
        
        url = TRADE_API_PURCHASE_URL_TEMPLATE.format(settings.TRADE_API_HOST)
        api_client = APIClient(url)
        resp_json = api_client.send_json_request(request_obj.getPayload())
        return JsonResponse(resp_json)
    except ValueError as ve:
        handleValueError(ve.args[0])
    except:
        logger.error('purchase(): relay hit exception {0}'.format(sys.exc_info()[0]))
        return handleValueError(sys.exc_info()[0])

def redeem(request):
    request_json = json.loads(request.body.decode('utf-8'))
    try:
        request_obj = TradeAPIRequest.parseFromJson(request_json)
        if request_obj != API_METHOD_PURCHASE:
            raise ValueError('{0}: expected:{1}, actual:{2}'.format(
                ERR_UNEXPECTED_METHOD,
                API_METHOD_REDEEM, request_obj.method))
        
        #first submit 
        crypt = WalletManager.create_fund_util('CNY')
        balance = crypt.getbalance()
        if balance - float(request_obj.total_fee) /100.0 < 0:
            raise ValueError(ERR_NOT_ENOUGH_CNY)
        
        crypt.unlock_wallet(5)
        amount = float(request_obj.total_fee) /100
        comment ='api_user:{0}, redeem amount: {1}'.format(request_obj.apikey, amount)
        crypt.send_fund(settings.TRADE_API_WALLET_ADDR, amount, comment)

        url = TRADE_API_REDEEM_URL_TEMPLATE.format(settings.TRADE_API_HOST)
        api_client = APIClient(url)
        resp_json = api_client.send_json_request(request_obj.getPayload())
        return JsonResponse(resp_json)
    except ValueError as ve:
        handleValueError(ve.args[0])
    except:
        logger.error('redeem(): relay hit exception {0}'.format(sys.exc_info()[0]))
        return handleValueError(sys.exc_info()[0])

def checkstatus(request):
    try:
        request_json = json.loads(request.body.decode('utf-8'))
        request_obj = TradeAPIRequest.parseFromJson(request_json)
        if request_obj != API_METHOD_PURCHASE:
            raise ValueError('{0}: expected:{1}, actual:{2}'.format(
                ERR_UNEXPECTED_METHOD,
                API_METHOD_QUERY, request_obj.method))
        
        url = TRADE_API_QUERY_URL_TEMPLATE.format(settings.TRADE_API_HOST)
        api_client = APIClient(url)
        resp_json = api_client.send_json_request(request_obj.getPayload())
        return JsonResponse(resp_json)
    except ValueError as ve:
        handleValueError(ve.args[0])
    except:
        logger.error('checkstatus(): relay hit exception {0}'.format(sys.exc_info()[0]))
        return handleValueError(sys.exc_info()[0])

def closetransaction(request):
    pass
