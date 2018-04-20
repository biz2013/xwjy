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
from tradeex.controllers.apiusermanager import APIUserManager
from tradeex.controllers.tradex import TradeExchangeManager
from tradeex.requests.heepayapirequestfactory import HeepayAPIRequestFactory
from tradeex.responses.heepayresponse import HeepayResponse
from tradeex.utils import *

from trading.views import errorpageview
from trading.controller.global_constants import *
from trading.controller.ordermanager import *
from trading.controller.heepaymanager import *
from tradeapi.utils import *
from tradeapi.data.tradeapirequest import TradeAPIRequest
from tradeapi.data.tradeapiresponse import TradeAPIResponse
import logging,json

logger = logging.getLogger("tradeex.api")

# in case in the future we need to reconstruct the
# response from trade exchange.  For now, it is
# just straight return
def create_prepurchase_response_from_heepay(heepay_response, api_user, api_trans_id, api_out_trade_no):
    
    response = TradeAPIResponse(
        api_user.apiKey, api_user.secretKey,
        heepay_response.return_code, 
        heepay_response.return_msg, 
        heepay_response.result_code,
        heepay_response.result_msg,
        api_out_trade_no,
        heepay_response.hy_bill_no,
        subject = heepay_response.subject,
        attach = heepay_response.attach,
        total_received = heepay_response.total_fee,
        payment_url = heepay_response.hy_url,
        reference_id = api_trans_id
    )

    return response.to_json()       

def create_selltoken_response(request_obj, api_trans):
    response = TradeAPIResponse(
        api_trans.api_user.apiKey, api_trans.api_user.secretKey,
        'SUCCESS',  '挂卖单成功',
        'SUCCESS',  '挂卖单成功',
        api_trans.out_trade_no,
        api_trans.transactionId,
        subject = api_trans.subject if api_trans.subject else None,
        attach = api_trans.attach if api_trans.attach else None,
        total_received = api_trans.total_fee,
        payment_url = None,
        reference_id = api_trans.transactionId
    )
    
# This will find user's account, use its secret key to check
# the sign of the request, then, based on request type, validate
# whether request has meaningful data
def validate_request(request_obj, api_user_info, expected_method):
    logger.info("validate_request: request parsed is {0}".format(request_obj.getPayload()))
    if not request_obj.is_valid(api_user_info.secretKey):
        raise ValueError('Request has invalid signature')
    if request_obj.method == expected_method:
        raise ValueError('Request has invalid method: expected {0}, actual {1}'.format(
            expected_method, request_obj.method))

def prepurchase(request):
    request_obj = None
    api_user = None
    try:
        logger.info('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        request_json= json.loads(request.body)
        request_obj = TradeAPIRequest.parseFromJson(request_json)
        api_user = APIUserManager.get_api_user_by_apikey(request_obj.apikey)
        logger.info('prepurchase(): [out_trade_no:{0}] find out api user id is {1}, key {2}'.format(
            request_obj.out_trade_no, api_user.user.id, api_user.secretKey
        ))
        validate_request(request_obj, api_user, 'wallet.trade.buy')
        tradex = TradeExchangeManager()
        api_trans_id, buyorder_id, seller_payment_account = tradex.purchase_by_cash_amount(api_user,
           request_obj, 'AXFund',  True)
        
        sitesettings = context_processor.settings(request)['settings']
        notify_url = settings.HEEPAY_NOTIFY_URL_FORMAT.format(
           sitesettings.heepay_notify_url_host,
           sitesettings.heepay_notify_url_port)
        return_url = settings.HEEPAY_RETURN_URL_FORMAT.format(
           sitesettings.heepay_return_url_host,
           sitesettings.heepay_return_url_port)
        
        heepay_api_key = sitesettings.heepay_app_id
        heepay_api_secret = sitesettings.heepay_app_key

        request_factory = HeepayAPIRequestFactory(
            "1.0", request_obj.apikey, api_user.secretKey)

        #heepay_request = request_factory.create_payload(
        #    orderId, request_obj.total_fee,  
        #    request_obj.payment_account, seller_payment_account, notify_url, return_url,
        #    nothing='nothing')
        
        heepay = HeePayManager()
        json_payload = heepay.create_heepay_payload('wallet.pay.apply', buyorder_id, heepay_api_key, 
            heepay_api_secret, "127.0.0.1", float(request_obj.total_fee)/100.0,
            seller_payment_account, request_obj.payment_account, 
            notify_url, return_url)
        status, reason, message = heepay.send_buy_apply_request(json_payload)
        response_json = json.loads(message) if status == 200 else None
        if not response_json:
            raise ValueError('Request to heepay failed with {0}:{1}-{2}'.format(
                status, reason, message
            ))

        # TODO: hard coded right now
        #api_client = APIClient('https://wallet.heepay.com/api/v1/payapply')
        #response_json = api_client.send_json_request(heepay_request)
        logger.info("prepurchase(): [out_trade_no:{0}] heepay reply: {1}".format(
            request_obj.out_trade_no, json.dumps(response_json, ensure_ascii=False)
        ))

        if request_obj.payment_provider == 'heepay':
            heepay_response = HeepayResponse.parseFromJson(response_json, heepay_api_secret)

            return JsonResponse(create_prepurchase_response_from_heepay(heepay_response, api_user,api_trans_id))
        else:
            raise ValueError("payment provider {0} is not supported".format(request_obj.payment_provider))
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except ValueError as ve:
        logger.error("prepurchase(): [out_trade_no:{0}] hit value error {1}".format(
            request_obj.out_trade_no, ve.args[0]))
        resp = create_error_purchase_response(
            request_obj, api_user,
            create_return_msg_from_valueError(ve.args[0]),
            create_result_msg_from_valueError(ve.args[0]),
            '')

        return JsonResponse(resp.to_json())

    except:
        error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_purchase_response(
            request_obj, api_user,
            '系统错误', '系统错误',''
        )
        return JsonResponse(resp.to_json())

def selltoken(request):
    try:
        logger.info('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        request_json= json.loads(request.body)
        request_obj = TradeAPIRequest.parseFromJson(request_json)
        api_user = APIUserManager.get_api_user_by_apikey(request_obj.apikey)
        logger.info('selltoken(): [out_trade_no:{0}] find out api user id is {1}, key {2}'.format(
            request_obj.out_trade_no, api_user.user.id, api_user.secretKey
        ))
        validate_request(request_obj, api_user, 'wallet.trade.sell')
        tradex = TradeExchangeManager()
        api_trans, sell_orderId = tradex.post_sell_order(request_obj, api_user)

        return JsonResponse(create_selltoken_response(request_obj, api_trans))
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except Exception as e:
       error_msg = 'selltoken()遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       #TODO: we should always return json with error message.
       return HttpResponseServerError('系统处理提现请求时出现系统错误')

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


def create_error_purchase_response(request_obj, api_user, return_msg, result_msg, trx_bill_no):
    kwargs = {}
    if request_obj.subject:
        kwargs['subject'] = request_obj.subject
    if request_obj.attach:
        kwargs['attach'] = request_obj.attach
    kwargs['total_fee'] = request_obj.total_fee
    return PurchaseAPIResponse(
        request_obj.apikey if request_obj else '',
        api_user.secretKey if api_user else '',
        'FAIL', return_msg, 'FAIL', result_msg,
        request_obj.out_trade_no,
        trx_bill_no, **kwargs)
