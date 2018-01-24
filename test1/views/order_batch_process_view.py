#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json, datetime

from django.contrib import messages
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.global_constants import *
from controller.global_utils import *
from controller.heepaymanager import *
from controller import ordermanager
from controller import useraccountinfomanager
from controller import backend_order_processor

from views.models.orderitem import OrderItem
from views.models.returnstatus import ReturnStatus
from views import errorpage
from django.contrib.auth.decorators import login_required


logger = logging.getLogger("site.order_batch_process")

def handle_paying_order(order, order_timeout, appId, appkey):
    try:
        trans = order.get_order_transactions(order.order_id)
        if not trans.payment_bill_no:
            logger.error('purchase order {0}: transaction id{1} : no payment bill no yet its status is PAYING'.format(order.order_id, trans.id))
            return;

        heepay = HeePayManager()
        if trans.payment_status != 'SUCCESS':
            logger.info('purchase order {0}: transaction id{1} : expired, payment_status: {2}. Query heepay for status...'.format(order.order_id, trans.id, trans.payment_status))
            payment_status = heepay.get_payment_status(order.order_id,
                               trans.payment_bill_no, appId, appkey)
            logger.info('purchase order {0}: transaction id{1} : expired, queried payment_status: {2}. Query heepay '.format(order.order_id, trans.id, payment_status))

        if payment_status in ['PAYSUCCESS','SUCCESS']:
            ordermanager.confirm_purchase_order(order.order_id, 'admin')

        timediff = datetime.datetime().utcnow() - order.lastupdated_at
        if int(timediff.total_seconds()) > order_timeout:
            if payment_status in ['EXPIREDINVALID','DEVCLOSE','USERABANDON','UNKNOWN']:
                backend_order_process.cancel_purchase_order(order.order_id,
                  'FAILED', payment_status, 'admin')
            else:
                heepay.cancel_payment(order.order_id, trans.payment_bill_no, appId,
                                       appkey)
                backend_order_process.cancel_purchase_order(order.order_id,
                  'CANCELLED', payment_status, 'admin')
    except Exception as e:
        error_msg = 'handle_paying_order hit eception {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)





def order_batch_process(request):
    try:
        sitesettings = context_processor.settings(request)['settings']
        sell_order_timeout = sitesettings['order_timeout_insec']
        confirmation_timeout = sitesettings['confirmation_timeout_insec']
        orders = backend_order_processor.get_unfilled_purchase_orders(request)
        for order in orders:
            if order.status == 'PAYING':
                handle_paying_order(order, 'admin')
            elif order.status == 'PAID':
                pass
            elif order.status == 'OPEN':
                pass


    except Exception as e:
        error_msg = 'order_batch_process hit eception {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
