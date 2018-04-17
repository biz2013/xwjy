#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, json, logging

from django.http import JsonResponse

from trading.config import context_processor
from tradeex.utils import *
from tradeex.responses.heepaynotify import *
from tradeex.controllers.tradex import *
from trading.controller.heepaymanager import *

sys.path.append('../stakingsvc/')

logger = logging.getLogger("tradeex.heepayview")

def get_payment_confirmation_json(request, app_key):
   logger.info('get_payment_confirmation_json()')
   json_data = {}
   logger.info('notification method is %s, full url is %s' % (request.method, request.get_full_path()))
   response = request.body.decode('utf-8')
   json_data = json.loads(response)
   logger.info('Receive payment confirmation {0}'.format(response))
   manager = HeePayManager()
   if not manager.confirmation_is_valid(json_data, app_key):
       return None
   return json_data

def heepay_notification(request):
    sitesettings = context_processor.settings(request)['settings']
    notify_json = get_payment_confirmation_json(request, sitesettings.heepay_app_key)
    heepay_notify = HeepayNotification.parseFromJson(notify_json, sitesettings.heepay_app_key)
    tradeex = TradeExchangeManager()
    api_user = None
    try:
        resp, api_user = tradeex.handle_payment_notificiation('heepay', heepay_notify)
        return JsonResponse(resp.to_json())

    except ValueError as ve:
        logger.error("heepay_notification(): [out_trade_no:{0}] hit value error {1}".format(
            heepay_notify.out_trade_no, ve.args[0]))
        resp = create_error_notification_response(
            api_user,
            create_return_msg_from_valueError(ve.args[0]),
            create_result_msg_from_valueError(ve.args[0]),
            heepay_notify.out_trade_no if heepay_notify else '',
            heepay_notify.trx_bill_no if heepay_notify else ''
        )

        return JsonResponse(resp.to_json())
    except Exception as e:
        error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        resp = create_error_notification_response(
            api_user, 
            '系统错误', '系统错误',
            heepay_notify.out_trade_no if heepay_notify else '',
            heepay_notify.trx_bill_no if heepay_notify else ''
        )
        return JsonResponse(resp.to_json())        


def create_error_notification_response(api_user, return_msg, result_msg, out_trade_no, trx_bill_no):
    return PurchaseAPIResponse(
        api_user.apiKey if api_user else '',
        api_user.secretKey if api_user else '',
        'FAIL', return_msg, 'FAIL', result_msg,
        out_trade_no,
        trx_bill_no, {})

    