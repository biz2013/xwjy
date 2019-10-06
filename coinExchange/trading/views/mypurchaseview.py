#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings

from tradeex.data.api_const import *
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager

from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller.global_utils import *
from trading.controller import ordermanager, userpaymentmethodmanager
from trading.controller import useraccountinfomanager
from trading.controller.heepaymanager import HeePayManager

from trading.views.paypalview import GetOrder
from trading.models import *
from trading.views.models.orderitem import OrderItem
from trading.views.models.userpaymentmethodview import *
from trading.views.models.returnstatus import ReturnStatus
from django.http import HttpResponse, HttpResponseServerError, HttpResponseForbidden, JsonResponse
from trading.views import errorpageview

logger = logging.getLogger("site.purchaseview")

def handleValueError(ve, request):
    if ve.args[0] == ERR_SELLER_WEIXIN_NOT_FULLY_SETUP:
        messages.error(request, '这个卖单的卖家没有正确设置微信支付收款，请选择其他卖单')
    elif ve.args[0] == ERR_SELLER_PAYPAL_NOT_FULLY_SETUP:
        messages.error(request, '这个卖单的卖家没有正确设置PayPal支付收款，请选择其他卖单')
    return show_active_sell_orders(request)

@login_required
def show_active_sell_orders(request):
    try:
       logger.debug("get show show_active_sell_orders request")
       username = request.user.username
       status = None
       sellorders = ordermanager.get_all_open_seller_order_exclude_user(request.user.id)
       accountinfo = useraccountinfomanager.get_user_accountInfo(request.user, 'AXFund')
       return render(request, 'trading/purchase.html', {'sellorders': sellorders,
                REQ_KEY_USERNAME: username,
                'useraccountInfo': accountinfo,
                'previous_call_status' : status})

    except Exception as e:
       error_msg = '显示现有卖单出现错误: {0}'.format(sys.exc_info()[0])
       logger.exception(e)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def show_purchase_input(request):
    try:
        if request.method != 'POST':
            error_msg = '购买页面不接受GET请求'
            logger.error('show_purchase_input(): receive GET request from {0}'.format(get_client_ip(request)))
            return errorpageview.show_error(request, ERR_CRITICAL_RECOVERABLE,
                    '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

        username = request.user.username
        userid = request.user.id
        useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
        if len(useraccountInfo.paymentmethods) == 0:
            messages.error(request, '请先注册支付方式再购买')
            return redirect('accountinfo')
        if len(useraccountInfo.paymentmethods[0].account_at_provider) == 0:
            messages.error(request, '请先注册支付账号再购买')
            return redirect('accountinfo')
        if "owner_user_id" not in request.POST:
            messages.warning(request, "回到主页再进行操作")
            return redirect('accountinfo')
        owner_user_id = request.POST["owner_user_id"]

        reference_order_id = request.POST["reference_order_id"]
        paypal_client_id = ''
        sell_order_payment_method = ordermanager.get_and_update_sell_order_payment_methods(reference_order_id)
        paypal_client_id = sell_order_payment_method.client_id if sell_order_payment_method and sell_order_payment_method.client_id else ''
        payment_method = sell_order_payment_method.provider.code if sell_order_payment_method else ''
        bill_no = payment_account = payment_qrcode_url = ''
        if not sell_order_payment_method:
            api_tran = APIUserTransactionManager.get_trans_by_reference_order(reference_order_id)
            if api_tran is None:
                raise ValueError('ERR_API_SELLER_NO_API_RECORD')
            
            bill_no, payment_method, payment_account, payment_qrcode_url = parseInfo(api_tran)
            
        owner_login = request.POST["owner_login"]
        unit_price = float(request.POST["locked_in_unit_price"])
        order_sub_type = request.POST["sub_type"]
        total_units = 0
        if 'quantity' in request.POST:
           total_units = float(request.POST['quantity'])
        available_units = float(request.POST["available_units_for_purchase"])
        order_currency = request.POST['sell_order_currency']
        if order_sub_type == 'ALL_OR_NOTHING':
            total_units = available_units
        
        #owner_payment_methods = ordermanager.get_user_payment_methods(owner_user_id) if not sell_order_payment_method else [
        #    UserPaymentMethodView(0,
        #        0, None,
        #        # TODO: the name of the seller payment provider should come from DB
        #        '微信', '',
        #        '', "", "")]
        #for method in owner_payment_methods:
        #    print ("provider %s has image %s" % (method.provider.name, method.provider_qrcode_image))
        buyorder = OrderItem(
           '',
           userid,
           username,
           unit_price, order_currency,
           total_units, 0,
           0.0, 'AXFund',
           '','','BUY', sub_type = order_sub_type,
           selected_payment_provider = payment_method,
           account_at_payment_provider = payment_account)
        return render(request, 'trading/input_purchase.html',
               {'username': username,
                'buyorder': buyorder,
                'owner_user_id': owner_user_id,
                'sub_type': order_sub_type,
                'reference_order_id': reference_order_id,
                'available_units_for_purchase': available_units,
                'paypal_clientId': paypal_client_id,
                'order_currency': order_currency}
               )
    except ValueError as ve:
        handleValueError(ve, request)
    except Exception as e:
       error_msg = '显示买单出现错误: {0}'.format(sys.exc_info()[0])
       logger.exception(e)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

def send_payment_request_to_heepay(sitesettings, buyorder_id, amount):
    notify_url = settings.HEEPAY_NOTIFY_URL_FORMAT.format(
           sitesettings.heepay_notify_url_host,
           sitesettings.heepay_notify_url_port)
    return_url = settings.HEEPAY_RETURN_URL_FORMAT.format(
           sitesettings.heepay_return_url_host,
           sitesettings.heepay_return_url_port)
    heepay = HeePayManager()
        
    seller_account, buyer_account = ordermanager.get_seller_buyer_payment_accounts(
                buyorder_id, 'heepay')
    logger.info('find seller account {0} and buyer account {1} with provider heepay'.format(
              seller_account, buyer_account))
        
    json_payload = heepay.create_heepay_payload('wallet.pay.apply',
         buyorder_id,
         sitesettings.heepay_app_id,
         sitesettings.heepay_app_key,
         '127.0.0.1', amount,
         seller_account,
         buyer_account,
         notify_url,
         return_url)
    logger.info("send this to heepay {0}".format(json_payload.encode('utf-8')))
    try:
        status, reason, message = heepay.send_buy_apply_request(json_payload)
        if status == 200:
            logger.info("heepay replied: {0}".format(message))
            return json.loads(message)
        else:
            logger.error('Request to heepay failed with {0}:{1}-{2}'.format(
            status, reason, message
            ))
            return None
    except:
        logger.error('send_payment_request_to_heepay() hit exception {0}'.format(
            sys.exc_info[0]
        ))
        return None

def send_payment_request(sitesettings, payment_provider, buyorder_id, amount):
    if payment_provider == 'heepay':
        return send_payment_request_to_heepay(sitesettings, buyorder_id, amount)
    else:
        raise ValueError('Payment method {0} is not supported'.format(payment_provider))

def generate_payment_qrcode(payment_provider,payment_provider_response_json,
         qrcode_image_basedir):
    if payment_provider == 'heepay':
        heepay = HeePayManager()
        return heepay.generate_heepay_qrcode(payment_provider_response_json,
                qrcode_image_basedir)
    else:
        raise ValueError('Payment provider {0} is not supported'.format(payment_provider))

def parseInfo(api_tran):
    username = nickname = payment_method = payment_qrcode_url = ''
    if api_tran.attach :
        parts = api_tran.attach.split(';')
        for part in parts:
            if part.startswith('http'):
                payment_qrcode_url = part.strip()
                continue
            subparts = part.split('=')
            if len(subparts) == 2:
                if subparts[0].strip() == 'weixin':
                    payment_method = 'weixin'
                    nickname = subparts[1].strip()
                elif subparts[0].strip() == 'payment_qrcode_url':
                    payment_qrcode_url = subparts[1].strip()
    if len(payment_qrcode_url) == 0 and api_tran.api_user.user.username.startswith('stakinguser1'):
        payment_qrcode_url = settings.API_SITE_URL['stakinguser1'].format(api_tran.api_out_trade_no)
    return api_tran.api_out_trade_no, payment_method, nickname, payment_qrcode_url
@login_required
def create_purchase_order(request):
    try:
        logger.debug('create_purchase_order()...')
        username = request.user.username
        userid = request.user.id
        logger.info("Begin process user input for creating purchase order")
        if request.method == 'POST':
            reference_order_id = request.POST['reference_order_id']
            owner_user_id = int(request.POST["owner_user_id"])
            quantity = float(request.POST['quantity'])
            unit_price = float(request.POST['unit_price'])
            order_currency = request.POST['order_currency']
            seller_payment_provider = request.POST['seller_payment_provider']
            logger.debug('create_purchase_order(): seller_payment_provider is {0}'.format(
                seller_payment_provider
            ))
            crypto= request.POST['crypto']
            total_amount = float(request.POST['total_amount'])
            buyorder = OrderItem('', userid, username, unit_price, order_currency, quantity,
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
                #owner_payment_methods = ordermanager.get_user_payment_methods(owner_user_id)
                #useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
                return redirect('purchase')
            if buyorderid is None:
               raise ValueError('Failed to get purchase order id')

            if settings.PAYMENT_API_STATUS['heepay'] == 'auto':
                # read the sitsettings
                sitesettings = context_processor.settings(request)['settings']
                json_response = send_payment_request(sitesettings, seller_payment_provider,
                    buyorder.order_id, total_amount)
                if json_response and json_response['return_code'] == 'SUCCESS':
                    ordermanager.post_open_payment_order(
                                    buyorderid, 'heepay',
                                    json_response['hy_bill_no'],
                                    json_response['hy_url'],
                                    username)

                    qrcode_file = generate_payment_qrcode('heepay', json_response, settings.MEDIA_ROOT)
                    return render(request, 'trading/purchase_heepay_qrcode.html',
                            { 'total_units' : quantity, 'unit_price': unit_price,
                            'total_amount': total_amount,
                            'heepay_qrcode_file' : qrcode_file })
                elif json_response and json_response['return_msg'] == HEEPAY_ERR_NONEXIST_RECEIVE_ACCOUNT:
                    purchase_order = Order.objects.get(order_id=buyorderid)
                    admin = User.objects.get(username='admin')
                    ordermanager.cancel_purchase_order(purchase_order, TRADE_STATUS_BADRECEIVINGACCOUNT, 
                        PAYMENT_STATUS_BADRECEIVINGACCOUNT, admin)
                
                owner_payment_methods = ordermanager.get_user_payment_methods(owner_user_id)
                useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
                messages.error(request, '向汇钱包下单申请失败:{0}'.format(json_response['return_msg'] if json_response else '系统错误'))
                return redirect('purchase')
            else:
                api_tran = APIUserTransactionManager.get_trans_by_reference_order(reference_order_id)
                if api_tran is None:
                    raise ValueError('ERR_API_SELLER_NO_API_RECORD')
                
                bill_no, payment_method, payment_account, payment_qrcode_url = parseInfo(api_tran)
                ordermanager.post_open_payment_order(
                                buyorderid, payment_method,
                                bill_no,
                                payment_qrcode_url,
                                username)
                useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
                return render(request, 'trading/purchase_qrcode.html',
                    { 'qrcode_url': payment_qrcode_url,
                      'total_units': quantity,
                      'unit_price': unit_price,
                      'unit_currency': order_currency,
                      'seller_payment_provider': payment_method,
                      'seller_payment_provider_account': payment_account,
                      'total_amount': total_amount}
                )

    except Exception as e:
        error_msg = '创建买单遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def create_paypal_purchase_order(request):
    try:
        logger.debug('create_purchase_order()...')
        username = request.user.username
        userid = request.user.id
        logger.info("Begin process user input for creating purchase order")
        if request.method == 'POST':
            reference_order_id = request.POST['reference_order_id']
            quantity = float(request.POST['quantity'])
            unit_price = float(request.POST['unit_price'])
            total_amount = float(request.POST['total_amount'])
            unit_price_currency = request.POST['unit_price_currency']
            crypto_currency = request.POST['crypto']
            seller_payment_provider = request.POST['seller_payment_provider']
            logger.debug('create_paypal_purchase_order(): seller_payment_provider is {0}'.format(
                seller_payment_provider
            ))

            buy_order_id = [""]

            # 1. Create purchase order
            buyorder = OrderItem('', userid, username, unit_price, unit_price_currency, quantity,
                0, total_amount, crypto_currency, '', '','BUY')

            try:
              buy_order_id[0] = ordermanager.create_purchase_order(buyorder,
                     reference_order_id,
                     seller_payment_provider, username)

            except ValueError as ve:
                if ve.args[0] == 'SELLORDER_NOT_OPEN':
                    return HttpResponseServerError('卖单暂时被锁定，请稍后再试')
                elif ve.args[0] == 'BUY_EXCEED_AVAILABLE_UNITS':
                    return HttpResponseServerError('购买数量超过卖单余额，请按撤销键然后再试')

                logger.error("create_paypal_purchase_order fail, detail is {0}.".format(ve))
                return HttpResponseServerError('遇到未知问题，请按撤销键然后再试')

            # Create Order in Paypal
            sell_order_info = ordermanager.get_order_info(reference_order_id)
            seller_paypal_payment_method = userpaymentmethodmanager.get_user_paypal_payment_method(sell_order_info.user.id)

            clientID = seller_paypal_payment_method.client_id
            clientSecret = seller_paypal_payment_method.client_secret

            purchase_description = "Total amount {0} {1} for {2} {3} with unit price {4} {5}."\
              .format(total_amount, unit_price_currency, quantity, crypto_currency, unit_price, unit_price_currency)

            orderInfo = GetOrder(clientID, clientSecret).create_order(buy_order_id[0], total_amount, purchase_description, unit_price_currency)
            if orderInfo.status_code != 201:
              logger.debug('fail to create paypal order, error code {0}, detail is {1}'.format(orderInfo.status_code, orderInfo))
              return ('PayPal支付请求失败，请按撤销键然后再试')

            # Update WalletTransaction to capture paypal transaction.
            ordermanager.update_purchase_order_payment_transaction(buy_order_id[0], TRADE_STATUS_CREADED, "", orderInfo.result.id)

            data = {}
            data['orderID'] = orderInfo.result.id
            json_data = json.dumps(data)
            return HttpResponse(json_data)
    except Exception as e:
        error_msg = '创建买单遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return HttpResponseServerError('系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
