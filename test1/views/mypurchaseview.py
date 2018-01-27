#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# this is for test UI. A fake one
from config import context_processor
from controller.global_constants import *
from controller.global_utils import *
from controller import ordermanager
from controller import useraccountinfomanager
from controller.heepaymanager import HeePayManager
import controller
from django.contrib.auth.decorators import login_required

from users.models import *
from views.models.orderitem import OrderItem
from views.models.userpaymentmethodview import *
from views.models.returnstatus import ReturnStatus
from views import errorpage
from test1 import settings

logger = logging.getLogger("site.purchaseview")

@login_required
def show_active_sell_orders(request):
    try:
       logger.debug("get show show_active_sell_orders request")

       if not request.user.is_authenticated():
           return render(request, 'login.html', { 'next' : '/purchase/'})
       username = request.user.username
       status = None
       sellorders = ordermanager.get_all_open_seller_order_exclude_user(request.user.id)
       accountinfo = useraccountinfomanager.get_user_accountInfo(request.user, 'AXFund', True)
       return render(request, 'html/purchase.html', {'sellorders': sellorders,
                REQ_KEY_USERNAME: username,
                'useraccountInfo': accountinfo,
                'previous_call_status' : status})

    except Exception as e:
       error_msg = '显示现有卖单出现错误: {0}'.format(sys.exc_info()[0])
       logger.exception(e)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def show_purchase_input(request):
    try:
        if not request.user.is_authenticated():
           return render(request, 'login.html', { 'next' : '/purchase/'})
        username = request.user.username
        userid = request.user.id
        useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
        if len(useraccountInfo.paymentmethods) == 0:
            messages.error(request, '请先注册支付账号再购买')
            return redirect('accountinfo')
        if len(useraccountInfo.paymentmethods[0].account_at_provider) == 0:
            messages.error(request, '请先注册支付账号再购买')
            return redirect('accountinfo')
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
           '','','BUY')
        return render(request, 'html/input_purchase.html',
               {'username': username,
                'buyorder': buyorder,
                'owner_user_id': owner_user_id,
                'reference_order_id': reference_order_id,
                'available_units_for_purchase': available_units,
                'owner_payment_methods': owner_payment_methods,
                'buyer_payment_methods': useraccountInfo.paymentmethods }
               )
    except Exception as e:
       error_msg = '显示买单出现错误: {0}'.format(sys.exc_info()[0])
       logger.exception(e)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

def send_payment_request_to_heepay(sitesettings, buyorder_id, amount):
    notify_url = 'http://{0}:{1}/heepay/confirm_payment/'.format(
           sitesettings.heepay_notify_url_host,
           sitesettings.heepay_notify_url_port)
    return_url = 'http://{0}:{1}/heepay/confirm_payment/'.format(
           sitesettings.heepay_return_url_host,
           sitesettings.heepay_return_url_port)
    heepay = HeePayManager()
    seller_account, buyer_account = ordermanager.get_seller_buyer_payment_accounts(
                buyorder_id, 'heepay')
    logger.info('find seller account {0} and buyer account {1} with provider heepay'.format(
              seller_account, buyer_account))
    json_payload = heepay.create_heepay_payload('wallet.pay.apply',
         buyorder_id,
         sitesettings.heepay_app_id.encode('ascii'),
         sitesettings.heepay_app_key.encode('ascii'),
         '127.0.0.1', amount,
         seller_account,
         buyer_account,
         notify_url,
         return_url)
    status, reason, message = heepay.send_buy_apply_request(json_payload)
    if status == 200:
        logger.info("heepay replied: {0}".format(message))
        return json.loads(message)
    else:
        logger.error('Request to heepay failed with {0}:{1}-{2}'.format(
           status, reason, message
        ))
        return None

def send_payment_request(sitesettings, payment_provider, buyorder_id, amount):
    if payment_provider == 'heepay':
        return send_payment_request_to_heepay(sitesettings, buyorder_id, amount)
    else:
        raise ValueError('Payment method {0} is not supported'.format(payment_method))

def generate_payment_qrcode(payment_provider,payment_provider_response_json,
         qrcode_image_basedir):
    if payment_provider == 'heepay':
        heepay = HeePayManager()
        return heepay.generate_heepay_qrcode(payment_provider_response_json,
                qrcode_image_basedir)
    else:
        raise ValueError('Payment provider {0} is not supported'.format(payment_provider))

@login_required
def create_purchase_order(request):
    try:
        logger.debug('create_purchase_order()...')
        if not request.user.is_authenticated():
            logger.error("user session is not valid.  Go to logout")
            return render(request, 'login.html', { 'next': '/purchase/'})
        username = request.user.username
        userid = request.user.id
        logger.info("Begin process user input for creating purchase order")
        if request.method == 'POST':
            reference_order_id = request.POST['reference_order_id']
            owner_user_id = int(request.POST["owner_user_id"])
            quantity = float(request.POST['quantity'])
            available_units = float(request.POST['available_units'])
            unit_price = float(request.POST['unit_price'])
            seller_payment_provider = request.POST['seller_payment_provider']
            crypto= request.POST['crypto']
            total_amount = float(request.POST['total_amount'])
            buyorder = OrderItem('', userid, username, unit_price, 'CNY', quantity,
                0, total_amount, crypto, '', '','BUY')
            buyorderid = None
            try:
                buyorderid = ordermanager.create_purchase_order(buyorder,
                     reference_order_id,
                     seller_payment_provider, username)
            except ValueError as ve:
                if ve.args[0] == 'SELLORDER_NOT_OPEN':
                    messages.error(request, '卖单暂时被锁定，请稍后再试')
                elif ve.args[0] == 'BUY_EXCEED_AVAILABLE_UNITS':
                    messages.error(request,'购买数量超过卖单余额，请按撤销键然后再试')
                else:
                    raise
                owner_payment_methods = ordermanager.get_user_payment_methods(owner_user_id)
                useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
                redirect('purchase')
            if buyorderid is None:
               raise ValueError('Failed to get purchase order id')

            returnstatus = None

            # read the sitsettings
            sitesettings = context_processor.settings(request)['settings']
            json_response = send_payment_request(sitesettings, seller_payment_provider,
                buyorder.order_id, total_amount)
            if json_response is not None and json_response['return_code'] == 'SUCCESS':
                if ordermanager.post_open_payment_order(
                                buyorderid, 'heepay',
                                json_response['hy_bill_no'],
                                json_response['hy_url'],
                                username):

                    qrcode_file = generate_payment_qrcode('heepay', json_response, settings.MEDIA_ROOT)
                    return render(request, 'html/purchase_heepay_qrcode.html',
                         { 'total_units' : quantity, 'unit_price': unit_price,
                           'total_amount': total_amount,
                           'heepay_qrcode_file' : qrcode_file })
            owner_payment_methods = ordermanager.get_user_payment_methods(owner_user_id)
            useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
            # sample reply error : {"return_code":"FAIL","return_msg":"无效的total_fee"}
            messages.error(request, '向汇钱包下单申请失败:{0}'.format(json_response['return_msg'].encode("utf-8")))
            redirect('purchase')

    except Exception as e:
        error_msg = '创建买单遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
