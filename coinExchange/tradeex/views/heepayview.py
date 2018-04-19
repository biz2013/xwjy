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
from tradeex.controllers.walletmanager import WalletManager
from trading.controller.heepaymanager import *
from tradeapi.data.purchase_notify import PurchaseAPINotify

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
    api_trans = None
    try:
        crypto_util = WalletManager.create_fund_util('CNY')
        api_trans = APIUserTransactionManager.get_trans_by_reference_order(heepay_notify.out_trade_no)
        api_user = api_trans.api_user
        external_crypto_addr = APIUserManager.get_api_user_external_crypto_addr(api_user.user.id, 'CNY')
        updated_api_trans = tradeex.handle_payment_notificiation('heepay', heepay_notify, api_trans)
        if api_trans.trade_status=='INPROGRESS':
            # do nothing if payment provider is in progress
            return HttpResponse(content='ok')
        elif api_trans.trade_status=='PAIDSUCCESS':
            amount = float(api_trans.total_fee) / 100.0
            comment = 'amount:{0},trxId:{1},out_trade_no:{2}'.format(amount, api_trans.transactionId, api_trans.out_trade_no)
            crypto_util.send(external_crypto_addr, amount, comment)
            # send success response
            resp_content = 'OK'
            if api_trans.notify_url:
                notify = create_api_notification(api_trans)
                api_client = APIClient(api_trans.notify_url)
                notify_resp = api_client.send_json_request(notify.to_json, response_format='text')
                # update notify situation
                comment = 'NOTIFYSUCCESS' if notify_resp.upper() == 'OK' else 'NOTIFYFAILED: {0}'.format(notify_resp)
                if api_trans:
                    APIUserTransactionManager.update_notification_status(
                        api_trans.transactionId, 
                        json_dumps(notify.to_json(), ensure_ascii = False), 
                        notify_resp, comment)
                if notify_resp.upper() != 'OK':
                    resp_content='error'
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
    except Exception as e:
        error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        if api_trans:
            APIUserTransactionManager.update_status_info(api_trans.transactionId, error_msg)
        return HttpResponse(content='error')      

def create_api_notification(api_trans):
        return PurchaseAPIResponse(
            '1.0',
            api_trans.api_user.apiKey,
            api_trans.api_user.secretKey,
            api_trans.api_out_trade_no,
            api_trans.transactionId,
            api_trans.payment_provider.name,
            api_trans.subject,
            api_trans.total_fee,
            api_trans.trade_status,
            api_trans.real_fee,
            api_trans.payment_provider_last_notified_at.strftime('yyyyMMddHHmmss') if api_trans.payment_provider_last_notified_at else None,
            from_account=api_trans.from_account,
            to_account = api_trans.to_account,
            attach = api_trans.attach
        )


    