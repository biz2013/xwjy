#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json, datetime

from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone

# this is for test UI. A fake one
from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller.global_utils import *
from trading.controller.heepaymanager import *
from trading.controller import ordermanager
from trading.controller import useraccountinfomanager
from trading.controller import backend_order_processor

from trading.views.models.orderitem import OrderItem
from trading.views.models.returnstatus import ReturnStatus
from trading.views import errorpageview
from django.contrib.auth.decorators import login_required


logger = logging.getLogger("site.order_batch_process")

def handle_paying_order(order, order_timeout, appId, appkey):
    try:
        logger.info("handle_paying_order {0}".format(order.order_id))
        trans = ordermanager.get_order_transactions(order.order_id)
        if not trans.payment_bill_no:
            logger.error('purchase order {0}: transaction id{1} : no payment bill no yet its status is PAYING'.format(order.order_id, trans.id))
            return;

        payment_status = 'UNKNOWN'
        heepay = HeePayManager()
        if trans.payment_status != 'SUCCESS':
            logger.info('purchase order {0}: transaction id{1} : expired, payment_status: {2}. Query heepay for status...'.format(order.order_id, trans.id, trans.payment_status))
            json_response = heepay.get_payment_status(order.order_id,
                                   trans.payment_bill_no, appId, appkey)
            payment_status = json_response['trade_status'].upper()
            logger.info('purchase order {0}: transaction id{1} : expired, queried payment_status: {2}. Query heepay '.format(order.order_id, trans.id, payment_status))
            if payment_status in ['PAYSUCCESS','SUCCESS']:
                ordermanager.update_order_with_heepay_notification(json_response, 'admin')
                return
        timediff = timezone.now() - order.lastupdated_at
        if int(timediff.total_seconds()) > order_timeout:
            if payment_status in ['EXPIREDINVALID','DEVCLOSE','USERABANDON','UNKNOWN']:
                ordermanager.cancel_purchase_order(order,
                      'FAILED', payment_status, 'admin')
            else:
                heepay.cancel_payment(order.order_id, trans.payment_bill_no, appId,
                                           appkey)
                ordermanager.cancel_purchase_order(order,
                      'FAILED', payment_status, 'admin')
        else:
            logger.info("The order {0} is not expired, skip for now".format(order.order_id)) 
    except Exception as e:
        error_msg = 'handle_paying_order hit eception {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)

def handle_paid_order(order, confirmation_timeout):
    try:
        logger.info("handle_paid_order {0}".format(order.order_id))
        timediff = timezone.now() - order.lastupdated_at
        if int(timediff.total_seconds()) > confirmation_timeout:
            ordermanager.confirm_purchase_order(order.order_id, 'admin')
    except Exception as e:
        error_msg = 'handle_paid_order hit eception {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)

def handle_open_order(order, sell_order_timeout):
    try:
        logger.info("handle_open_order {0}".format(order.order_id))
        timediff = timezone.now() - order.lastupdated_at
        if int(timediff.total_seconds()) > sell_order_timeout:
            ordermanager.cancel_purchase_order(order,
              'CANCELLED', 'UNKNOWN', 'admin')
    except Exception as e:
        error_msg = 'handle_open_order hit eception {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)

def order_batch_process(request):
    try:
        sitesettings = context_processor.settings(request)['settings']
        sell_order_timeout = sitesettings.order_timeout_insec
        confirmation_timeout = sitesettings.confirmation_timeout_insec
        appId = sitesettings.heepay_app_id
        appKey = sitesettings.heepay_app_key
        orders = backend_order_processor.get_unfilled_purchase_orders()
        for order in orders:
            if order.status == 'PAYING':
                handle_paying_order(order, sell_order_timeout, appId, appKey)
            elif order.status == 'PAID':
                handle_paid_order(order, confirmation_timeout)
            elif order.status == 'OPEN':
                handle_open_order(order, sell_order_timeout)
        return HttpResponse(content='OK')
    except Exception as e:
        error_msg = 'order_batch_process hit eception {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return HttpResponse(content=error_msg)
