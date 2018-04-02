#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse

from trading.config import context_processor
#from django.contrib.auth.decorators import login_required

# this is for test UI. A fake one
from trading.views import errorpageview
from trading.controller.global_constants import *
from trading.controller.ordermanager import *
from trading.data.traderequest import *
from tradeapi.utils import *

import logging,json

logger = logging.getLogger("tradeapi.prepurchase")

# in case in the future we need to reconstruct the
# response from trade exchange.  For now, it is
# just straight return
def create_prepurchase_response(respons_json, purchase_order):
    return response_json


# This will find user's account, use its secret key to check
# the sign of the request, then, based on request type, validate
# whether request has meaningful data
def validate_request(request_obj, api_user_info):
    # find the secret key based on the user apiKey

    # validate sign

    # validate request data
    return True

def prepurchase(request):
    try:
        logger.debug('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        request_json= json.loads(request.body)
        request_obj = PrepurchaseRequest.parseFromJson(request_json)
        api_user = APIUserManager.getUserByAPIKey(request_obj['api_key'])
        validate_request(request_obj, api_user)
        tradex = TradeExchange()
        order, userpaymentmethods = tradex.find_order_to_buy(request_obj)
        heepay_request = HeepayRequest.create(request_obj, api_user,
              order.order_id,
              settings.PAYMENT_CALLBACK_HOST,
              settings.PAYMENT_CALLBACK_PORT,
              payment_provider_manager.get_callback_url(
                         request_obj.payment_provider)
            )
        api_client = PaymentAPICallClient(
                      payment_provider_manager.get_purchase_url(
                            request_obj.payment_provider)
                     )

        response_json = api_client.sendRequest(heepay_request)
        heepay_response = HeepayResponse.parseFromJson(response_json)

        return JsonResponse(create_prepurchase_response(heepay_response, order))
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except Exception as e:
       error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       #TODO: we should always return json with error message.
       return HttpResponseServerError('系统处理充值请求时出现系统错误')


def selltoken(request):
    try:
        logger.debug('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        request_json= json.loads(request.body)
        request_obj = PrepurchaseRequest.parseFromJson(request_json)
        api_user = APIUserManager.getUserByAPIKey(request_obj['api_key'])
        validate_request(request_obj, api_user)
        tradex = TradeExchange()
        order = tradex.find_order_to_buy()
        heepay_request = HeepayRequest.create(request_obj, api_user,
              order.order_id,
              settings.PAYMENT_CALLBACK_HOST,
              settings.PAYMENT_CALLBACK_PORT,
              payment_provider_manager.get_callback_url(
                         request_obj.payment_provider)
            )
        api_client = PaymentAPICallClient(
                      payment_provider_manager.get_purchase_url(
                            request_obj.payment_provider)
                     )

        response_json = api_client.sendRequest(heepay_request)
        heepay_response = HeepayResponse.parseFromJson(response_json)

        return JsonResponse(create_prepurchase_response(heepay_response, order))
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except Exception as e:
       error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       #TODO: we should always return json with error message.
       return HttpResponseServerError('系统处理充值请求时出现系统错误')



def query_order_status(request) :
    try:
        logger.debug('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        request_json= json.loads(request.body)
        request_obj = PrepurchaseRequest.parseFromJson(request_json)
        api_user = APIUserManager.getUserByAPIKey(request_obj['api_key'])
        validate_request(request_obj, api_user)
        tradex = TradeExchange()
        order = tradex.find_order_to_buy()
        heepay_request = HeepayRequest.create(request_obj, api_user,
              order.order_id,
              settings.PAYMENT_CALLBACK_HOST,
              settings.PAYMENT_CALLBACK_PORT,
              payment_provider_manager.get_callback_url(
                         request_obj.payment_provider)
            )
        api_client = PaymentAPICallClient(
                      payment_provider_manager.get_purchase_url(
                            request_obj.payment_provider)
                     )

        response_json = api_client.sendRequest(heepay_request)
        heepay_response = HeepayResponse.parseFromJson(response_json)

        return JsonResponse(create_prepurchase_response(heepay_response, order))
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except Exception as e:
       error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       #TODO: we should always return json with error message.
       return HttpResponseServerError('系统处理查询请求时出现系统错误')
    