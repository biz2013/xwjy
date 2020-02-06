#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

from django.conf import settings
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseServerError
from django.utils import timezone

from trading.config import context_processor
#from django.contrib.auth.decorators import login_required

# this is for test UI. A fake one
from tradeex.client.apiclient import APIClient
from tradeex.controllers.apiusermanager import APIUserManager
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
from tradeex.controllers.tradex import TradeExchangeManager
from tradeex.requests.heepayapirequestfactory import HeepayAPIRequestFactory
from tradeex.responses.heepayresponse import HeepayResponse
from tradeex.data.api_const import *
from tradeex.data.tradeapirequest import TradeAPIRequest
from tradeex.data.tradeapiresponse import TradeAPIResponse
from tradeex.utils import *

from trading.views import errorpageview
from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller import ordermanager
from trading.controller.heepaymanager import *
import logging, json, re

logger = logging.getLogger("tradeex.api")


def create_selltoken_response(request_obj, api_trans, sell_order_id):
    return_msg = '挂卖单成功' if sell_order_id else '挂卖进行中'
    response = TradeAPIResponse(
        api_trans.api_user.apiKey, api_trans.api_user.secretKey,
        'SUCCESS',  return_msg,
        'SUCCESS',  return_msg,
        api_trans.api_out_trade_no,
        api_trans.transactionId,
        subject = api_trans.subject if api_trans.subject else None,
        attach = api_trans.attach if api_trans.attach else None,
        total_fee = api_trans.total_fee,
        payment_url = None,
        reference_id = api_trans.transactionId
    )

    return response.to_json()
    
def parseUserInput(request_json):
    logger.debug('parseUserInput {0}'.format(request_json))
    logger.debug('parseUserInput to string {0}'.format(json.dumps(request_json, ensure_ascii=False)))
    request_obj = TradeAPIRequest.parseFromJson(request_json)
    api_user = APIUserManager.get_api_user_by_apikey(request_obj.apikey)
    return request_obj, api_user

def validateUserInput(expected_method, request_obj, api_user):
    if request_obj.method != expected_method:
        raise ValueError('{0}: expected:{1}, actual:{2}'.format(
            ERR_UNEXPECTED_METHOD,
            expected_method, request_obj.method))

    if request_obj.method in [API_METHOD_PURCHASE, API_METHOD_REDEEM]:
        if not (request_obj.payment_provider and request_obj.payment_provider in settings.SUPPORTED_API_PAYMENT_PROVIDERS):
            logger.error('parseUserInput(): {0}'.format(
                'unsupported payment provider' if request_obj.payment_provider else 'missing payment provider'
            ))
            raise ValueError(ERR_INVALID_OR_MISSING_PAYMENT_PROVIDER)

        if request_obj.method == API_METHOD_REDEEM and not request_obj.payment_account:
            logger.error('parseUserInput(): missing payment account')
            raise ValueError(ERR_REDEEM_REQUEST_NO_PAYMENT_ACCOUNT)

        # making sure all purchase traffic not from investment site (www.9lp.com) has external_cny_rec_address defined.
        if request_obj.method == API_METHOD_PURCHASE and not re.search(settings.INVESTMENT_SITE, api_user.source, re.IGNORECASE)  \
             and not re.search(settings.LIUSIJIU_SITE, api_user.source, re.IGNORECASE) \
             and ( not hasattr(request_obj, 'external_cny_rec_address') or not request_obj.external_cny_rec_address ):
            logger.error('parseUserInput(): missing external_cny_rec_address info')
            # return same error as missing payment account to hide we need cny_address.
            raise ValueError(ERR_REQUEST_MISS_EXTERNAL_CNYF_ADDRESS_FOR_REDEEM)

        if request_obj.method == API_METHOD_PURCHASE and request_obj.payment_provider == PAYMENTMETHOD_PAYPAL:
            if request_obj.cad_cny_exchange_rate and request_obj.cad_cny_exchange_rate < 4:
                logger.error("Purchase request {0} payment provider is paypal, but exchange rate (cad -> cny) seems incorrect, its value is {1}, suppose to be something like 5.36".format(
                    request_obj, request_obj.cad_cny_exchange_rate
                ))
                raise ValueError(ERR_INVALID_CAD_CHANGERATE_INPUT)

        # making sure we have external_cny_rec_address attribute in purchase request object.
        if request_obj.method == API_METHOD_PURCHASE and not hasattr(request_obj, 'external_cny_rec_address'):
            setattr(request_obj, "external_cny_rec_address", None)

        amount = int(request_obj.total_fee) if type(request_obj.total_fee) is str else request_obj.total_fee
        logger.debug("The request's amount is {0}".format(amount))

        if amount > settings.API_TRANS_LIMIT_IN_CENT:
            logger.error('parseUserInput(): {0}: amount:{1}, limit:{2}'.format(
                ERR_OVER_TRANS_LIMIT, request_obj.total_fee, settings.API_TRANS_LIMIT))
            raise ValueError(ERR_OVER_TRANS_LIMIT)

    if not request_obj.is_valid(api_user.secretKey):
        raise ValueError(ERR_INVALID_SIGNATURE)

def handleValueError(ve_msg, secretKey):
    request_errors = {
        ERR_REQUEST_MISS_METHOD : '请求缺少method字段',
        ERR_REQUEST_MISS_BIZCONTENT: '请求缺少biz_content字段',
        ERR_REQUEST_MISS_VERSION : '请求缺少version字段',
        ERR_REQUEST_MISS_CHARSET : '请求缺少charset字段',
        ERR_REQUEST_MISS_SIGN_TYPE : '请求缺少sign_type字段',
        ERR_REQUEST_MISS_TIMESTAMP : '请求缺少timestamp字段',
        ERR_REQUEST_MISS_SIGNATURE : '请求缺少sign(签名）字段',
        ERR_REQUEST_MISS_PAYMENT_PROVIDER : '请求缺少payment_provider字段',
        ERR_REQUEST_MISS_PAYMENT_ACCOUNT_FOR_REDEEM : '提现请求缺少payment_account字段',
        ERR_REQUEST_MISS_TXID_FOR_REDEEM: '提现请求缺少txid字段',
        ERR_REQUEST_MISS_EXTERNAL_CNYF_ADDRESS_FOR_REDEEM: '提现请求缺少external_cny_rec_address字段'
    }

    resp_json = {}
    resp_json['return_code'] = 'FAIL'
    if ve_msg == ERR_INVALID_JSON_INPUT:
        resp_json['return_msg'] = '用户请求不是正确的JSON格式'
    elif ve_msg == ERR_INVALID_SIGNATURE:
        resp_json['return_msg'] = '签名不符'
    elif ve_msg == ERR_USER_NOT_FOUND_BASED_ON_APPID:
        resp_json['return_msg'] = '用户不存在'
    elif ve_msg == ERR_MORE_THAN_ONE_USER_BASED_ON_APPID:
        resp_json['return_msg'] = '用户有多于一个账户'
    elif ve_msg == ERR_UNEXPECTED_METHOD:
        resp_json['return_msg'] = '错误指令'
        resp_json['result_code'] = 'FAIL'
        pos = ve_msg.find('expected:')
        parts = ve_msg[pos:].split(',')
        key_value_parts1 = parts[0].split[':']
        expected = key_value_parts1[1]
        key_value_parts2 = parts[1].split[':']
        actual = key_value_parts2[1]
        resp_json['result_msg'] = '期望指令: {0}, 实际指令: {1}'.format(expected, actual)
    elif ve_msg == ERR_OVER_TRANS_LIMIT:
        resp_json['return_msg'] = '交易超额'
        resp_json['result_code'] = 'FAIL'
        resp_json['result_msg'] = '每笔交易上限为{0}分'.format(settings.API_TRANS_LIMIT)
    elif ve_msg == ERR_NO_RIGHT_SELL_ORDER_FOUND:
        resp_json['return_msg'] = '无卖单提供充值'
    elif ve_msg == ERR_MORE_THAN_ONE_OPEN_BUYORDER:
        resp_json['return_msg'] = '请您等您正在处理的充值购买请求被确认后再发新的请求'
    elif ve_msg == ERR_INVALID_OR_MISSING_PAYMENT_PROVIDER:
        resp_json['return_msg'] = '缺失支付方式或提供的支付方式系统不支持'
    elif ve_msg == ERR_REDEEM_REQUEST_NO_PAYMENT_ACCOUNT:
        resp_json['return_msg'] = '请提供相应的支付账号'
    elif ve_msg == ERR_CANNOT_FIND_BUYER_PAYMENT_PROVIDER:
        resp_json['return_msg'] = '找不到买家付款方式'                
    elif ve_msg == ERR_CANNOT_FIND_SELLER_PAYMENT_PROVIDER:
        resp_json['return_msg'] = '找不到卖家付款方式'        
    elif ve_msg == ERR_CANNOT_FIND_SELLER_PAYMENT_ACCOUNT:
        resp_json['return_msg'] = '找不到卖家账号'
    elif ve_msg == ERR_NO_SELL_ORDER_TO_SUPPORT_PRICE:
        resp_json['return_msg'] = '无卖单提供定价'
    elif ve_msg == ERR_HEEPAY_REQUEST_EXCEPTION:
        resp_json['return_msg'] = '无法连接支付系统，请询问供应商'
    elif ve_msg == ERR_HEEPAY_REQUEST_ERROR:
        resp_json['return_msg'] = '支付系统回复错误码，请询问供应商'
    elif ve_msg in request_errors:
        resp_json['return_msg'] = request_errors[ve_msg]
    else:
        resp_json['return_msg'] = '数据错误'

    logger.info('handleValueError({0}): return error response {1}'.format(
        ve_msg, json.dumps(resp_json, ensure_ascii=False)
    ))

    if secretKey:
        resp_json['sign'] = sign_api_content(resp_json, secretKey)

    return JsonResponse(resp_json)

def handleException(ex_msg):
    resp_json = {}
    resp_json['return_code'] = 'FAILED'
    resp_json['return_msg'] = '系统错误'
    logger.info('handleValueError({0}): return error response {1}'.format(
        ve_msg, json.dumps(resp_json, ensure_ascii=False)
    ))
    return JsonResponse(resp_json)

# This will find user's account, use its secret key to check
# the sign of the request, then, based on request type, validate
# whether request has meaningful data
def validate_request(request_obj, api_user_info, expected_method):
    logger.info("validate_request: request parsed is {0}".format(request_obj.getPayload()))
    logger.info("validate request with key={0}".format(api_user_info.secretKey))
    if not request_obj.is_valid(api_user_info.secretKey):
        raise ValueError('Request has invalid signature')
    if request_obj.method != expected_method:
        raise ValueError('Request has invalid method: expected {0}, actual {1}'.format(
            expected_method, request_obj.method))

@csrf_exempt
def prepurchase(request):
    request_obj = None
    api_user = None
    try:
        logger.info('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request in binary {0}'.format(request.body))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))

        try:
            request_json= json.loads(request.body.decode('utf-8'))
        except:
            raise ValueError(ERR_INVALID_JSON_INPUT)

        request_obj, api_user = parseUserInput(request_json)
        validateUserInput(API_METHOD_PURCHASE, request_obj, api_user)

        #if request_obj.total_fee > settings.API_TRANS_LIMIT:
        #    raise ValueError('OVERLIMIT: amount:{0}, limit:{1}'.format(request_obj.total_fee, settings.API_TRANS_LIMIT))
        #api_user = APIUserManager.get_api_user_by_apikey(request_obj.apikey)
        #logger.info('prepurchase(): [out_trade_no:{0}] find out api user id is {1}, key {2}'.format(
        #    request_obj.out_trade_no, api_user.user.id, api_user.secretKey
        #))
        #validate_request(request_obj, api_user, 'wallet.trade.buy')
        #logger.info('prepurchase(): [out_trade_no:{0}] request is valid'.format(
        #    request_obj.out_trade_no
        #))
        
        tradex = TradeExchangeManager()
        sitesettings = context_processor.settings(request)['settings']
        final_resp_json = tradex.purchase_by_cash_amount(api_user,
           request_obj, 'AXFund', sitesettings, True)
        
        logger.info("prepurchase(): sending response to buyer...")
        return JsonResponse(final_resp_json)
        #else:
        #    raise ValueError("payment provider {0} is not supported".format(request_obj.payment_provider))
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except ValueError as ve:
        logger.error('prepurchase(): hit ValueError {0}'.format(ve.args[0]))
        return handleValueError(ve.args[0], api_user.secretKey if api_user else None)
    except:
        error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_trade_response(
            request_obj, api_user,
            '系统错误', '系统错误',''
        )
        return JsonResponse(resp.to_json())
    #except:
    #    logger.error('prepurchase() hit error: {0}'.format(sys.exc_info()[0]))
    #    return handleException(sys.exc_info()[0])

@csrf_exempt
def selltoken(request):
    request_obj = None
    api_user = None    
    try:
        logger.info('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        try:
            request_json= json.loads(request.body.decode('utf-8'))
        except:
            raise ValueError(ERR_INVALID_JSON_INPUT)

        request_obj, api_user = parseUserInput(request_json)
        validateUserInput(API_METHOD_REDEEM, request_obj, api_user)
        logger.info('selltoken(): [out_trade_no:{0}] find out api user id is {1}, key {2}'.format(
            request_obj.out_trade_no, api_user.user.id, api_user.secretKey
        ))
        validate_request(request_obj, api_user, API_METHOD_REDEEM)
        tradex = TradeExchangeManager()
        api_trans, sell_orderId = tradex.post_sell_order(request_obj, api_user)
        return JsonResponse(create_selltoken_response(request_obj, api_trans, sell_orderId))
    #TODO: should handle different error here.
    # what if network issue, what if the return is 30x, 40x, 50x
    except ValueError as ve:
        logger.error('selltoken(): hit ValueError {0}'.format(ve.args[0]))
        return handleValueError(ve.args[0], api_user.secretKey if api_user else None)
    except :
        error_msg = 'selltoken()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_trade_response(
            request_obj, api_user,
            '系统错误', '系统错误',''
        )
        return JsonResponse(resp.to_json())

@csrf_exempt
def query_order_status(request) :
    api_user = None
    request_obj = None
    try:
        logger.debug('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        try:
            request_json= json.loads(request.body.decode('utf-8'))
        except:
            raise ValueError(ERR_INVALID_JSON_INPUT)

        request_obj, api_user = parseUserInput(request_json)
        validateUserInput(API_METHOD_QUERY, request_obj, api_user)
        tradeex = TradeExchangeManager()
        api_trans = tradeex.find_transaction(request_obj.trx_bill_no)
        sitesettings = context_processor.settings(request)['settings']
        appId = sitesettings.heepay_app_id
        appKey = sitesettings.heepay_app_key

        # if trade status is alreadu in failed state, just return the status
        logger.info('query_order_status(): api trans[{0}] trade_status is {1}'.format(
            api_trans.transactionId, api_trans.trade_status
        ))
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
            ordermanager.update_order_with_heepay_notification(json_response, 'admin')
            api_trans.refresh_from_db()

        return JsonResponse(create_query_status_response(api_trans, api_user).to_json())
    except ValueError as ve:
        logger.error('query_order_status(): hit ValueError {0}'.format(ve.args[0]))
        return handleValueError(ve.args[0], api_user.secretKey if api_user else None)
    except:
        error_msg = 'query_order_status()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_trade_response(
            request_obj, api_user,
            '系统错误', '系统错误',''
        )
        return JsonResponse(resp.to_json())

@csrf_exempt
def cancel_order(request):
    try:
        logger.debug('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        try:
            request_json= json.loads(request.body.decode('utf-8'))
        except:
            raise ValueError(ERR_INVALID_JSON_INPUT)
            
        request_obj = TradeAPIRequest.parseFromJson(request_json)
        api_user = APIUserManager.get_api_user_by_apikey(request_obj.api_key)
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
            ordermanager.update_order_with_heepay_notification(json_response, 'admin')
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
    if request_obj:
        if request_obj.subject:
            kwargs['subject'] = request_obj.subject
        if request_obj.attach:
            kwargs['attach'] = request_obj.attach
        kwargs['total_fee'] = request_obj.total_fee
    return TradeAPIResponse(
        request_obj.apikey if request_obj else '',
        api_user.secretKey if api_user else '',
        'FAIL', return_msg, 'FAIL', result_msg,
        request_obj.out_trade_no if request_obj else '',
        trx_bill_no, **kwargs)


def create_query_status_response(api_trans, api_user):
    return TradeAPIResponse(
        api_user.apiKey,
        api_user.secretKey,
        'SUCCESS', '查询成功',
        'SUCCESS', '查询成功',
        api_trans.api_out_trade_no,
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
