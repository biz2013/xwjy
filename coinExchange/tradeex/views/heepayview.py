#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, json, logging
sys.path.append('../stakingsvc/')

from django.http import JsonResponse, HttpResponse

from trading.config import context_processor
from tradeex.utils import *
from tradeex.responses.heepaynotify import *
from tradeex.client.apiclient import APIClient
from tradeex.controllers.tradex import TradeExchangeManager
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
from trading.controller.heepaymanager import *
from tradeapi.data.purchase_notify import PurchaseAPINotify

logger = logging.getLogger("tradeex.heepayview")

def get_payment_confirmation_json(request, app_key):
   logger.info('get_payment_confirmation_json()')
   json_data = {}
   logger.info('notification method is %s, full url is %s' % (request.method, request.get_full_path()))
   response = request.body.decode('utf-8')
   json_data = json.loads(response, encoding='utf-8')
   logger.info('Receive payment confirmation {0}'.format(response))
   manager = HeePayManager()
   # TODO: fix the valiation
   #if not manager.confirmation_is_valid(json_data, app_key):
   #    logger.info('get_payment_confirmation_json() the request is not valid')
   #    return None
   return json_data

def heepay_notification(request):
    sitesettings = context_processor.settings(request)['settings']
    notify_json = get_payment_confirmation_json(request, sitesettings.heepay_app_key)
    heepay_notify = HeepayNotification.parseFromJson(notify_json, sitesettings.heepay_app_key)
    tradeex = TradeExchangeManager()
    api_trans = None
    try:
        api_trans = APIUserTransactionManager.get_trans_by_reference_order(heepay_notify.out_trade_no)
        updated_api_trans = tradeex.handle_payment_notificiation('heepay', heepay_notify, api_trans)
        if updated_api_trans.trade_status=='INPROGRESS':
            # do nothing if payment provider is in progress
            return HttpResponse(content='ok')
        elif updated_api_trans.trade_status=='PAIDSUCCESS':
            resp_content = 'OK'
            if not APIUserTransactionManager.on_trans_paid_success(updated_api_trans):
                resp_content = 'error'
            return HttpResponse(content=resp_content)
        else: 
            # return failed response
            return HttpResponse(content='error')

    except ValueError as ve:
        error_msg = "heepay_notification(): [out_trade_no:{0}] hit value error {1}".format(
            heepay_notify.out_trade_no, ve.args[0])
        logger.error(error_msg)
        if api_trans:
            APIUserTransactionManager.update_status_info(api_trans.transactionId, error_msg)
        return HttpResponse(content='error')
    except:
        error_msg = 'heepay_notification()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        if api_trans:
            APIUserTransactionManager.update_status_info(api_trans.transactionId, error_msg)
        return HttpResponse(content='error')      


    