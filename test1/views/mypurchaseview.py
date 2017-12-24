#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from config import context_processor
from controller.test_model_manager import ModelManager
from controller.global_constants import *
from controller.global_utils import *
from controller import ordermanager
from controller import useraccountinfomanager
from controller.heepaymanager import HeePayManager


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
    username = request.session[REQ_KEY_USERNAME]
    userid = int(request.session[REQ_KEY_USERID])
    useraccountInfo = useraccountinfomanager.get_user_accountInfo(userid,'AXFund')
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
    return render(request, 'html/input_purchase.html',
           {'username': username,
            'sellorder': sellorder,
            'owner_payment_methods':owner_payment_methods,
            'buyer_payment_methods': useraccountInfo.paymentmethods }
           )

def create_purchase_order(request):
    #try:
        logger.debug('create_purchase_order()...')
        if not user_session_is_valid(request):
           return render(request, 'html/login.html', { 'next_action' : '/purchase/'})
        username = request.POST[REQ_KEY_USERNAME]
        userid = int(request.session[REQ_KEY_USERID])
        reference_order_id = request.POST['reference_order_id']
        owner_user_id = request.POST['owner_user_id']
        quantity = request.POST['quantity']
        available_units = request.POST['available_units']
        unit_price = request.POST['unit_price']
        seller_payment_provider = request.POST['seller_payment_provider']
        total_amount = float(request.POST['total_amount'])
        manager = ModelManager()
        order = manager.create_purchase_order(username, reference_order_id,
               quantity, unit_price, 'CNY', total_amount, 'AXFund')

        returnstatus = None
        seller_accounts = ordermanager.get_user_payment_account(owner_user_id, seller_payment_provider)
        buyer_accounts = ordermanager.get_user_payment_account(userid, seller_payment_provider)
        if len(seller_accounts) == 0:
            raise ValueError('Could not find seller %d\'s account with payment provider %s', owner_user_id, seller_payment_provider)
        if len(seller_accounts) > 1:
            raise ValueError('Find more than one accounts for seller %d\'s account with payment provider %s', owner_user_id, seller_payment_provider)

        seller_account = seller_accounts[0].account_at_provider.encode('ascii')
        buyer_account = ''
        if len(buyer_accounts) > 0:
            if len(buyer_accounts) > 1:
               raise ValueError('Find more than one accounts for buyer %d\'s account with payment provider %s', owner_user_id, seller_payment_provider)
            buyer_account = buyer_accounts[0].account_at_provider.encode('ascii')

        print 'find seller account %s and buyer account %s with provider %s' % (seller_account, buyer_account, seller_payment_provider)

        # read the sitsettings
        sitesettings = context_processor.settings(request)['settings']
        notify_url = 'http://{0}:{1}/mysellorder/heepay/confirm_payment/'.format(sitesettings.heepay_notify_url_host, sitesettings.heepay_notify_url_port)
        return_url = 'http://{0}:{1}/purchase/createorder2/heepay/confirmed/'.format(sitesettings.heepay_return_url_host, sitesettings.heepay_return_url_port)
        if (seller_payment_provider == 'heepay'):
            heepay = HeePayManager()
            json_payload = heepay.create_heepay_payload('wallet.pay.apply',
                 order.order_id,
                 sitesettings.heepay_app_id.encode('ascii'),
                 sitesettings.heepay_app_key.encode('ascii'),
                 '127.0.0.1', order.total_amount,
                 seller_account,
                 buyer_account,
                 notify_url,
                 return_url)
            status, reason, message = heepay.send_buy_apply_request(json_payload)
            print "call heepay response: status %s reason %s message %s" % (status, reason, message)
            go_to_pay = False
            if status == 200:
               json_response = json.loads(message)
               if json_response['return_code'] == 'SUCCESS':
                  return render(request, 'html/jumptopayment.html',
                         { 'payment_redirect_url' : json_response['hy_url'] })
            if go_to_pay:
               returnstatus = ReturnStatus('SUCCEED','','下单成功')
            else:
               returnstatus = ReturnStatus('FAILED', 'FAILED', '下单申请失败')
        sellorder = OrderItem(
             reference_order_id,
             owner_user_id,
             '', #owner_login
             float(unit_price),
             'CNY',
             quantity,
             available_units,
             dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S'),
             'ACTIVE')
        owner_payment_methods = manager.get_user_payment_methods(owner_user_id)

        return render(request, 'html/input_purchase.html',
               {'username': username,
                'sellorder': sellorder,
                'buyorder' : order,
                'owner_payment_methods':owner_payment_methods,
                'returnstatus': returnstatus }
               )
    #except:
        error_msg = 'create_purchase order hit exception: {0}'.format(sys.exc_info()[0])
        logger.error(error_msg)
        return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
