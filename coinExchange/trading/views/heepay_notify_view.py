#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller.heepaymanager import *
from trading.controller import ordermanager
from trading.views import errorpageview

logger = logging.getLogger("site.heepay_confirm")

def get_payment_confirmation_json(request, app_key):
   logger.info('get_payment_confirmation_json()')
   json_data = {}
   logger.info('notification method is %s, full url is %s' % (request.method, request.get_full_path()))
   json_data = json.loads(request.body)
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
        sitesettings = context_processor.settings(request)['settings']
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
        else:
            logger.info("Receive sync payment notification")
            order_id = request.GET.get('order_id')
            if order_id is None:
                logger.error('heepay did not return with order_id with sync notification')
                messages.error(request, '请稍后再查看您的买单')
            else:
                order = ordermanager.get_order_info(order_id)
                if order.status == 'PAYING':
                    logger.warn('purchse order {0} is still in PAYING mode'.format(order_id))
                    messages.warning(request, '请等会确认付款完成'.format(order_id,order.units))
                elif order.status == 'PAID':
                    logger.info('purchse order {0} is already PAID'.format(order_id))
                    messages.success(request, '买单已发送，请等待卖方确认'.format(order_id))
                else:
                    logger.info('purchase order {0} has been filled'.format(order_id))
                    messages.success(request, '您的购买交易已完成，请看交易记录'.format(order_id))
                    return redirect('mytransactions')
        return redirect('purchase')
    except Exception as e:
        error_msg = 'Confirmation processing hit exception: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        if request.method == 'GET':
            return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
               '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
        else:
            return HttpResponse(content='error')
