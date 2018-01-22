#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from config import context_processor
from controller.heepaymanager import *
from controller import ordermanager
from views import errorpage

logger = logging.getLogger("site.heepay_confirm")

def get_payment_confirmation_json(request, app_key):
   logger.info('get_payment_confirmation_json()')
   json_data = {}
   logger.info('notification method is %s, full url is %s' % (request.method, request.get_full_path()))
   if request.method == 'POST':
       json_data = json.loads(request.body)
   elif request.method == 'GET':
       if len(request.GET.items()) == 0:
           logger.error("There is no input in GET confirmation request")
           return None
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
            json_data = get_payment_confirmation_json(request,
                              sitesettings.heepay_app_key)
            if json_data is None:
                error_msg = 'Receive invalid notification from confirmation request, nothing to do'
                logger.error(error_msg)
                return HttpResponse(content='error')
            trade_status = json_data.get('trade_status', 'Unknown')
            if trade_status not in ['Success', 'Starting', 'PaySuccess']:
                error_msg = 'Receive notification with unsupported trade_status %s' % trade_status
                logger.error(error_msg)
                return HttpResponse(content='error')
            ordermanager.update_order_with_heepay_notification(json_data, 'admin')
            return HttpResponse(content='OK')
        elif request.method == 'GET':
            logger.info("Receive sync payment notification")
            if 'order_id' not in request.GET:
                logger.error('heepay didn\'t return with order_id with sync notification')
                messages.error('汇钱包回复没有买单号码，请刷新交易记录等待交易完成')
            else：
                order_id = request.GET['order_id']
                buyorder = ordermanager.get_order_info(order_id)
                if order.status == 'PAYING':
                    logger.warn('purchse order {0} is still in PAYING mode'.format(order_id))
                    messages.warn('支付系统还未最终确认买单{0}支付成功，请刷新交易记录等待交易完成'.format(order_id,order.units))
                elif order.status == 'PAID':
                    logger.info('purchse order {0} is already PAID'.format(order_id))
                    messages.success('支付系统确认买单{0}支付成功，请刷新交易记录等待交易完成'.format(order_id))
                elif
                    logger.info('purchase order {0} has been filled'.format(order_id))
                    messages.success('您的买单{0}交易已完成，请看交易记录'.format(order_id))
                    return redirect('mytransactions')
        else:
            logger.error('heepay_confirm_payment() receive invalid method {0}'.format(request.method))
        return redirect('purchase')
    except Exception as e:
        error_msg = 'Confirmation processing hit exception: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        if request.method == 'GET':
            return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
               '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
        else:
            return HttpResponse(content='error')
