#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, redirect

from config import context_processor
from controller.heepaymanager import *
from controller import ordermanager
from django.contrib.auth.decorators import login_required

logger = logging.getLogger("site.heepay_confirm")

@login_required
def get_payment_confirmation_json(request, app_key):
   logger.info('get_payment_confirmation_json()')
   json_data = {}
   logger.info('notification method is %s, full url is %s' % (request.method, request.get_full_path()))
   if request.method == 'POST':
       json_data = json.loads(request.body)
   elif request.method == 'GET':
       json_data['version'] = request.GET['version']
       json_data['app_id'] = request.GET['app_id']
       json_data['subject'] = request.GET['subject']
       json_data['out_trade_no'] = request.GET['out_trade_no']
       json_data['hy_bill_no'] = request.GET['hy_bill_no']
       json_data['payment_type'] = request.GET['payment_type']
       json_data['total_fee'] = request.GET['total_fee']
       json_data['trade_status'] = request.GET['trade_status']
       json_data['real_fee'] = request.GET['real_fee']
       json_data['payment_time'] = request.GET['payment_time']
       if 'attach' in request.GET:
           json_data['attach']
       if 'api_account_mode' in request.GET:
           json_data['api_account_mode'] = request.GET['api_account_mode']
       if 'to_open_id' in request.GET:
           json_data['to_open_id'] = request.GET['to_open_id']
       if 'from_open_id' in request.GET:
           json_data['from_open_id'] = request.GET['from_open_id']
       if 'to_account' in request.GET:
           json_data['to_account'] = request.GET['to_account']
       if 'from_account' in request.GET:
           json_data['from_account'] = request.GET['from_account']
       json_data['sign'] = request.GET['sign']
   else:
       raise ValueError('Unsupported request method %s' % request.method)
   logger.info('Receive payment confirmation {0}'.format(request.body))
   manager = HeePayManager()
   if not manager.confirmation_is_valid(json_data, app_key):
       return None
   return json_data

# This is the handler of notification from heepay
# If it is POST, it can only return 'ok' or 'error'
#
@csrf_exempt
def heepay_confirm_payment(request):
    try:
        if request.method == 'POST':
            logger.info("Receive async payment notification ")
        elif request.method == 'GET':
            logger.info("Receive sync payment notification")
        else:
            return HttpResponse(content='error')
        sitesettings = context_processor.settings(request)['settings']
        json_data = get_payment_confirmation_json(request,
                          sitesettings.heepay_app_key)
        validated = False
        if json_data is None:
            error_msg = 'Receive invalid notification from confirmation request, nothing to do'
            logger.error(error_msg)
            return HttpResponse(content='error')
        trade_status = json_data.get('trade_status', 'Unknown')
        if trade_status not in ['Success', 'Starting', 'PaySuccess']:
            error_msg = 'Receive notification with unsupported trade_status %s' % trade_status
            logger.error(error_msg)
            return HttpResponse(content='error')
        ordermanager.update_order_with_heepay_notification(json_data, 'sysop')
        if request.method == 'GET':
            request.session[REQ_KEY_USERID] = userid
            request.session[REQ_KEY_USERNAME] = operator
            return redirect('accountinfo')
        else:
            return HttpResponse(content='OK')
    except Exception as e:
        error_msg = 'Confirmation processing hit exception: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        if request.method == 'GET':
            return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
               '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
        else:
            return HttpResponse(content='error')
