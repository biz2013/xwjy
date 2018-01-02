#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect

from controller.heepaymanager import *
from controller import ordermanager

logger = logging.getLogger("site.heepay_confirm")

@csrf_exempt
def heepay_confirm_payment(request):
    """
    {
	"version": "1.0",
	"app_id": "hyq17121610000800000911220E16AB0",
	"subject": "购买1.020000CNY",
	"out_trade_no": "20180102122319_293146",
	"hy_bill_no": "180102122300364021000081666",
	"payment_type": "Alipay",
	"total_fee": "1",
	"trade_status": "Success",
	"real_fee": "1",
	"payment_time": "20180102122507",
	"api_account_mode": "Account",
	"to_account": "15811302702",
	"from_account": "18600701961",
	"sign": "EEB980CD2663C9E27C7A38094410CB60"
}
    """
    try:
        if request.method == 'POST':
            logger.info("Receive async payment notification ")
        elif request.method == 'GET':
            logger.info("Receive sync payment notification")
        else:
            #TODO error
            pass
        manager = HeePayManager()
        json_data = manager.get_payment_confirmation_json(request)
        if json_data is None:
            error_msg = 'Receive invalid notification from confirmation request, nothing to do'
            logger.error(error_msg)
            return HttpResponseBadRequest(content = error_msg)
        logger.info("notification: {0}".format(json_data))
        trade_status = json_data.get('trade_status', 'Unknown')
        if trade_status not in ['Success', 'Starting', 'PaySuccess']:
            error_msg = 'Receive notification with unsupported trade_status %s' % trade_status
            logger.error(error_msg)
            return HttpResponseBadRequest(content = error_msg)
        ordermanager.update_order_with_heepay_notification(json_data)
        if request.method == 'GET':
            userid, username = ordermanager.get_order_owner_info(json_data['out_trade_no'])
            request.session[REQ_KEY_USERID] = userid
            request.session[REQ_KEY_USERNAME] = username
            return redirect('accountinfo')
        else:
            return HttpResponse(content='OK')
    except Exception as e:
        error_msg = ''
        if request.method =='GET':
           error_msg = '付款确认遇到错误: {0}'.format(sys.exc_info()[0])
        else:
           error_msg = 'Confirmation processing hit exception: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        #TODO return 503 for post method
        if request.method == 'GET':
            return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
               '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
        else:
            return HttpResponseServerError(error_msg)
