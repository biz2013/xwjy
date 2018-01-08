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
from test1 import settings

logger = logging.getLogger("site.purchaseview")

def show_active_sell_orders(request):
    try:
       logger.debug("get show show_active_sell_orders request")

       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/purchase/'})
       username = request.session[REQ_KEY_USERNAME]
       userId = int(request.session[REQ_KEY_USERID])
       status = None
       sellorders = ordermanager.get_all_open_seller_order_exclude_user(userId)
       accountinfo = useraccountinfomanager.get_user_accountInfo(userId, 'AXFund', True)
       return render(request, 'html/purchase.html', {'sellorders': sellorders,
                REQ_KEY_USERNAME: username,
                'useraccountInfo': accountinfo,
                'previous_call_status' : status})

    except Exception as e:
       error_msg = '显示现有卖单出现错误: {0}'.format(sys.exc_info()[0])
       logger.exception(e)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

def show_purchase_input(request):
    if not user_session_is_valid(request):
       return render(request, 'html/login.html', { 'next_action' : '/purchase/'})
    username = request.session[REQ_KEY_USERNAME]
    userid = int(request.session[REQ_KEY_USERID])
    useraccountInfo = useraccountinfomanager.get_user_accountInfo(userid,'AXFund')
    owner_user_id = request.POST["owner_user_id"]
    reference_order_id = request.POST["reference_order_id"]
    owner_login = request.POST["owner_login"]
    unit_price = float(request.POST["locked_in_unit_price"])
    total_units = 0
    if 'quantity' in request.POST:
       total_units = float(request.POST['quantity'])
    available_units = float(request.POST["available_units_for_purchase"])
    owner_payment_methods = ordermanager.get_user_payment_methods(owner_user_id)
    #for method in owner_payment_methods:
    #    print ("provider %s has image %s" % (method.provider.name, method.provider_qrcode_image))
    buyorder = OrderItem(
       '',
       userid,
       username,
       unit_price,'CYN',
       total_units, 0,
       0.0, 'AXFund',
       '','')
    return render(request, 'html/input_purchase.html',
           {'username': username,
            'buyorder': buyorder,
            'owner_user_id': owner_user_id,
            'reference_order_id': reference_order_id,
            'available_units_for_purchase': available_units,
            'owner_payment_methods': owner_payment_methods,
            'buyer_payment_methods': useraccountInfo.paymentmethods }
           )

def create_purchase_order(request):
    try:
        logger.debug('create_purchase_order()...')
        if not user_session_is_valid(request):
           return render(request, 'html/login.html', { 'next_action' : '/purchase/'})
        username = request.POST[REQ_KEY_USERNAME]
        userid = int(request.session[REQ_KEY_USERID])
        reference_order_id = request.POST['reference_order_id']
        owner_user_id = int(request.POST["owner_user_id"])
        quantity = float(request.POST['quantity'])
        available_units = float(request.POST['available_units'])
        unit_price = float(request.POST['unit_price'])
        seller_payment_provider = request.POST['seller_payment_provider']
        crypto= request.POST['crypto']
        total_amount = float(request.POST['total_amount'])
        buyorder = OrderItem('', userid, username, unit_price, 'CNY', quantity,
            0, total_amount, crypto, '', '')
        buyorderid, rs= ordermanager.create_purchase_order(buyorder, reference_order_id, username)
        if buyorderid is None:
           logger.error('Failed to create purchase order %s' % rs)
           owner_payment_methods = ordermanager.get_user_payment_methods(owner_user_id)
           useraccountInfo = useraccountinfomanager.get_user_accountInfo(userid,'AXFund')
           return render(request, 'html/input_purchase.html',
              {'username': username,
               'buyorder': buyorder,
               'owner_user_id': owner_user_id,
               'reference_order_id': reference_order_id,
               'available_units_for_purchase': available_units,
               'owner_payment_methods': owner_payment_methods,
               'buyer_payment_methods': useraccountInfo.paymentmethods,
               'returnstatus' : ReturnStatus(-1, 'Failed', '') }
           )

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

        logger.info('find seller account %s and buyer account %s with provider %s' % (seller_account, buyer_account, seller_payment_provider))

        # read the sitsettings
        sitesettings = context_processor.settings(request)['settings']
        notify_url = 'http://{0}:{1}/heepay/confirm_payment/'.format(sitesettings.heepay_notify_url_host, sitesettings.heepay_notify_url_port)
        return_url = 'http://{0}:{1}/heepay/confirm_payment/'.format(sitesettings.heepay_return_url_host, sitesettings.heepay_return_url_port)
        if (seller_payment_provider == 'heepay'):
            heepay = HeePayManager()
            json_payload = heepay.create_heepay_payload('wallet.pay.apply',
                 buyorder.order_id,
                 sitesettings.heepay_app_id.encode('ascii'),
                 sitesettings.heepay_app_key.encode('ascii'),
                 '127.0.0.1', total_amount,
                 seller_account,
                 buyer_account,
                 notify_url,
                 return_url)
            status, reason, message = heepay.send_buy_apply_request(json_payload)
            logger.info("call heepay response: status %s reason %s message %s" % (status, reason, message))
            go_to_pay = False
            if status == 200:
               json_response = json.loads(message)
               if json_response['return_code'] == 'SUCCESS':
                  qrcode_file = heepay.generate_heepay_qrcode(json_response, settings.MEDIA_ROOT)
                  return render(request, 'html/purchase_heepay_qrcode.html',
                         { 'total_units' : quantity, 'unit_price': unit_price,
                           'total_amount': total_amount,
                           'heepay_qrcode_file' : qrcode_file })
            else:
               returnstatus = ReturnStatus('FAILED', 'FAILED', '下单申请失败')
        owner_payment_methods = ordermanager.get_user_payment_methods(owner_user_id)
        useraccountInfo = useraccountinfomanager.get_user_accountInfo(userid,'AXFund')
        return render(request, 'html/input_purchase.html',
          {'username': username,
           'buyorder': buyorder,
           'owner_user_id': owner_user_id,
           'reference_order_id': reference_order_id,
           'available_units_for_purchase': available_units,
           'owner_payment_methods': owner_payment_methods,
           'buyer_payment_methods': useraccountInfo.paymentmethods,
           'returnstatus' : ReturnStatus(-1, rs, '') }
        )
    except Exception as e:
        error_msg = '创建买单遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
