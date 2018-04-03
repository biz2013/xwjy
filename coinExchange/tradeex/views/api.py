#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
sys.path.append('../stakingsvc/')

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse

from trading.config import context_processor
#from django.contrib.auth.decorators import login_required

# this is for test UI. A fake one
from tradeex.client.apiclient import APIClient
from trading.views import errorpageview
from trading.controller.global_constants import *
from trading.controller.ordermanager import *
from tradeapi.utils import *
from tradeapi.data.traderequest import PurchaseAPIRequest

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
        request_obj = PurchaseAPIRequest.parseFromJson(request_json)
        api_user = APIUserManager.get_user_by_apikey(request_obj['api_key'])
        validate_request(request_obj, api_user)
        tradex = TradeExchange()
        order, userpaymentmethods = tradex.purchase_by_cash_amount(api_user,
           'AXFund', request_obj.total_fee, 'CNY',
           request_obj.payment_provider, 
           request_obj.payment_account,
           True, request_obj.out_trade_no)
        
        notify_url = settings.HEEPAY_NOTIFY_URL_FORMAT.format(
           sitesettings.heepay_notify_url_host,
           sitesettings.heepay_notify_url_port)
        return_url = settings.HEEPAY_RETURN_URL_FORMAT.format(
           sitesettings.heepay_return_url_host,
           sitesettings.heepay_return_url_port)
 
        request_factory = HeepayAPIRequestFactory(
            "1.0", request_obj.apiKey, request_obj.secret_key)

        heepay_request = request_factory.create_payload(
            order.order_id, request_obj.total_fee,  
            request_obj.buyer_account, seller_account, async_notify_url, sync_notify_url,
            None)
        
        # TODO: hard coded right now
        api_client = APIClient('https://wallet.heepay.com/Api/v1/PayApply')
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
    