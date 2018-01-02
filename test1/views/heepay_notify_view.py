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
        operator = 'sysop'
        userid, username = ordermanager.get_order_owner_info(json_data['out_trade_no'])
        ordermanager.update_order_with_heepay_notification(json_data,
                 userid,
                 operator if request.method=='POST' else username)
        if request.method == 'GET':
            request.session[REQ_KEY_USERID] = userid
            request.session[REQ_KEY_USERNAME] = operator
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
