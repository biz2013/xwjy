#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.test_model_manager import ModelManager
from controller.global_constants import *
from controller.global_utils import *
from controller import ordermanager

from users.models import *
from views.models.orderitem import OrderItem
from views.models.userpaymentmethodview import *
from views.models.returnstatus import ReturnStatus
from views import errorpage

logger = logging.getLogger(__name__)

def show_active_sell_orders(request):
    try:
       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/purchase/'})
       username = request.session[REQ_KEY_USERNAME]
       userId = int(request.session[REQ_KEY_USERID])
       status = None
       sellorders = ordermanager.get_all_open_seller_order_exclude_user(userId)
       return render(request, 'html/purchase.html', {'sellorders': sellorders,
                REQ_KEY_USERNAME: username,
                'previous_call_status' : status})

    except:
       error_msg = 'sell_axfund hit exception: {0}'.format(sys.exc_info()[0])
       logger.error(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

def show_purchase_input(request):
    if not user_session_is_valid(request):
       return render(request, 'html/login.html', { 'next_action' : '/purchase/'})

    owner_user_id = request.POST["owner_user_id"]
    order_id = request.POST["reference_order_id"]
    owner_login = request.POST["owner_login"]
    available_units = request.POST["available_units_for_purchase"]
    print "receive order id %s" % (order_id)
    print "receive owner_user_id is %s" % (owner_user_id)
    print "available units for purchase is %s" % (available_units)
    owner_payment_methods = ordermanager.get_user_payment_methods(int(owner_user_id))
    #for method in owner_payment_methods:
    #    print ("provider %s has image %s" % (method.provider.name, method.provider_qrcode_image))
    sellorder = OrderItem(
       request.POST["reference_order_id"],
       owner_user_id,
       owner_login,
       request.POST["locked_in_unit_price"],
       'CYN',
       0, available_units,
       '','')
    print 'sellorder id is here %s' % (sellorder.order_id)
    login = request.POST['username']
    return render(request, 'html/input_purchase.html',
           {'username':'taozhang',
            'sellorder': sellorder,
            'owner_payment_methods':owner_payment_methods }
           )
