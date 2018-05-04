#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
sys.path.append('../stakingsvc/')

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponseServerError
from django.utils import timezone

from trading.config import context_processor
#from django.contrib.auth.decorators import login_required

# this is for test UI. A fake one
from tradeex.client.apiclient import APIClient
from tradeex.controllers.apiusermanager import APIUserManager
from tradeex.controllers.tradex import TradeExchangeManager
from tradeex.controllers.crypto_utils import CryptoUtility
from tradeex.requests.heepayapirequestfactory import HeepayAPIRequestFactory
from tradeex.responses.heepayresponse import HeepayResponse
from tradeex.utils import *

from trading.views import errorpageview
from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller import ordermanager
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
    if request_obj.method != expected_method:
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
        logger.debug('after parse the input, the request object is {0}'.format(
            request_obj.getPayload()
        ))
        api_user = APIUserManager.get_api_user_by_apikey(request_obj.apikey)
        logger.info('prepurchase(): [out_trade_no:{0}] find out api user id is {1}, key {2}'.format(
            request_obj.out_trade_no, api_user.user.id, api_user.secretKey
        ))
        validate_request(request_obj, api_user, 'wallet.trade.buy')
        logger.info('prepurchase(): [out_trade_no:{0}] request is valid'.format(
            request_obj.out_trade_no
        ))
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
            if response_json['return_code'] == 'SUCCESS':
                ordermanager.post_open_payment_order(
                            buyorder_id, 'heepay',
                            response_json['hy_bill_no'],
                            response_json['hy_url'],
                            api_user.user.username)
                
            heepay_response = HeepayResponse.parseFromJson(response_json, heepay_api_secret)

            return JsonResponse(create_prepurchase_response_from_heepay(
                heepay_response, api_user,api_trans_id, request_obj.out_trade_no))
        else:
            raise ValueError("payment provider {0} is not supported".format(request_obj.payment_provider))
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except ValueError as ve:
        logger.error("prepurchase(): [out_trade_no:{0}] hit value error {1}".format(
            request_obj.out_trade_no, ve.args[0]))
        resp = create_error_trade_response(
            request_obj, api_user,
            create_return_msg_from_valueError(ve.args[0]),
            create_result_msg_from_valueError(ve.args[0]),
            '')

        return JsonResponse(resp.to_json())

    except:
        error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_trade_response(
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
    except :
        error_msg = 'selltoken()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_trade_response(
            request_obj, api_user,
            '系统错误', '系统错误',''
        )
        return JsonResponse(resp.to_json())

def query_order_status(request) :
    try:
        logger.debug('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        request_json= json.loads(request.body)
        request_obj = TradeAPIRequest.parseFromJson(request_json)
        api_user = APIUserManager.get_api_user_by_apikey(request_obj['api_key'])
        validate_request(request_obj, api_user, 'wallet.trade.query')
        tradeex = TradeExchangeManager()
        api_trans = tradeex.find_transaction(request_obj.trx_bill_no)
        sitesettings = context_processor.settings(request)['settings']
        appId = sitesettings.heepay_app_id
        appKey = sitesettings.heepay_app_key

        # if trade status is alreadu in failed state, just return the status
        if api_trans.trade_status in ['ExpiredInvalid', 'DevClose','UserAbandon']:
            return JsonResponse(create_query_status_response(api_trans, api_user).to_json())
            
        if api_trans.payment_status in ['Unknow','NotStart','PaySuccess']:
            if api_trans.payment_provider != 'heepay':
                logger.error('query_order_status(): found unsupported payment provider {0}'.format(
                    api_trans.payment_provider))
                raise ValueError('PAYMENT_PROVIDER_NOT_SUPPORTED')
            logger.info('api trans id {0}, reference_order {1}: payment_status: {2}. Query heepay for status...'.format(
                api_trans.transactionId, api_trans.reference_order.order_id,
                api_trans.payment_status))
            heepay = HeePayManager()
            json_response = heepay.get_payment_status(api_trans.reference_order.order_id,
                                   api_trans.reference_bill_no, appId, appKey)
            ordermanager.update_order_with_heepay_notification(json_response, 'admin', api_trans)
            api_trans.refresh_from_db()

        return JsonResponse(create_query_status_response(api_trans, api_user).to_json())
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except:
        error_msg = 'query_order_status()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_trade_response(
            request_obj, api_user,
            '系统错误', '系统错误',''
        )
        return JsonResponse(resp.to_json())

def cancel_order(requet):
    try:
        logger.debug('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        request_json= json.loads(request.body)
        request_obj = TradeAPIRequest.parseFromJson(request_json)
        api_user = APIUserManager.get_api_user_by_apikey(request_obj['api_key'])
        validate_request(request_obj, api_user, 'wallet.trade.cancel')
        tradeex = TradeExchangeManager()
        api_trans = tradeex.find_transaction(request_obj.trx_bill_no)
        sitesettings = context_processor.settings(request)['settings']
        appId = sitesettings.heepay_app_id
        appKey = sitesettings.heepay_app_key

        # if trade status is alreadu in failed state, just return the status
        if api_trans.trade_status in ['ExpiredInvalid', 'DevClose','UserAbandon','PaidSuccess','PaidSuccess']:
            return JsonResponse(create_cancel_response(api_trans, api_user).to_json())
            
        if api_trans.payment_status in ['Unknow','NotStart','PaySuccess']:
            if api_trans.payment_provider != 'heepay':
                logger.error('query_order_status(): found unsupported payment provider {0}'.format(
                    api_trans.payment_provider))
                raise ValueError('PAYMENT_PROVIDER_NOT_SUPPORTED')
            logger.info('api trans id {0}, reference_order {1}: payment_status: {2}. Query heepay for status...'.format(
                api_trans.transactionId, api_trans.reference_order.order_id,
                api_trans.payment_status))
            heepay = HeePayManager()
            json_response = heepay.get_payment_status(api_trans.reference_order.order_id,
                                   api_trans.reference_bill_no, appId, appKey)
            ordermanager.update_order_with_heepay_notification(json_response, 'admin', api_trans)
            api_trans.refresh_from_db()
            if api_trans.payment_status in ['Unknow','NotStart']:
                APIUserTransactionManager.abandon_trans(api_trans)
                api_trans.refresh_from_db()
        return JsonResponse(create_query_status_response(api_trans, api_user).to_json())
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except:
        error_msg = 'query_order_status()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_trade_response(
            request_obj, api_user,
            '系统错误', '系统错误',''
        )
        return JsonResponse(resp.to_json())
    
def create_error_trade_response(request_obj, api_user, return_msg, result_msg, trx_bill_no):
    kwargs = {}
    if request_obj.subject:
        kwargs['subject'] = request_obj.subject
    if request_obj.attach:
        kwargs['attach'] = request_obj.attach
    kwargs['total_fee'] = request_obj.total_fee
    return TradeAPIResponse(
        request_obj.apikey if request_obj else '',
        api_user.secretKey if api_user else '',
        'FAIL', return_msg, 'FAIL', result_msg,
        request_obj.out_trade_no,
        trx_bill_no, **kwargs)


def create_query_status_response(api_trans, api_user):
    return TradeAPIResponse(
        api_user.apiKey,
        api_user.secretKey,
        'SUCCESS', '查询成功',
        'SUCCESS', '查询成功',
        api_trans.out_trade_no,
        api_trans.reference_bill_no,
        subject = api_trans.subject,
        attach = api_trans.attach,
        total_fee = api_trans.total_fee,
        trade_status = api_trans.trade_status
    )

def create_cancel_response(api_trans, api_user):
    return_code = 'SUCCESS'
    return_msg = '撤单成功'
    result_code = 'SUCCESS'
    result_msg = '撤单成功'
    if api_trans.trade_status in ['PaidSuccess', 'Success']:
        return_code = result_code = 'FAIL'
        return_msg = result_msg = '订单已支付'
    elif api_trans.trade_status != 'UserAbandon':
        result_msg = return_msg = '订单已经失败'

    return TradeAPIResponse(
        api_user.apiKey,
        api_user.secretKey,
        return_code, return_msg,
        result_code, result_msg,
        api_trans.out_trade_no,
        api_trans.reference_bill_no,
        trade_status = api_trans.trade_status
    )
    