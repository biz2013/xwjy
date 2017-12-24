#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.heepaymanager import HeePayManager
from controller.global_utils import *

# this is for test UI. A fake one
from config import context_processor
from controller.test_model_manager import ModelManager
from controller.global_constants import *
from users.models import *
from views.models.orderitem import OrderItem
from views.models.returnstatus import ReturnStatus

import logging,json

logger = logging.getLogger(__name__)

def home(request):
    """Show the home page."""
    if request.session['username']:
        return redirect('accountinfo')
    return render(request, 'html/index.html')

def logout(request):
    request.session.flush()
    return render(request, 'html/index.html')

def login(request):
    login = UserLogin()
    if request.method == 'POST':
        login.username = request.POST['username']
        login.password = request.POST['password']
        manager = ModelManager()
        rc, msg, user = manager.login(login.username, login.password)
        if rc == 0:
            request.session['username'] = login.username
            request.session['userid'] = user.id

            forwardto = request.POST['forwardto']
            if forwardto:
                return redirect(forwardto)
            else:
                return redirect("accountinfo")
        else:
            return render(request, "html/login.html",
               {'message': msg, 'login':login})
    else:
        return render(request, "html/login.html",
            { 'login' : login})

def registration(request):
    login = UserLogin()
    user = User()
    user.login = login
    if request.method == 'POST':
        login.username = request.POST['username']
        login.password = request.POST['password']
        user.email = request.POST['email']
        print "registration: username %s password %s email %s" % (login.username, login.password, user.email)
        manager = ModelManager()
        rc, msg = manager.register(user)
        if 0 == rc:
            return render(request, 'html/login.html',
              {'message':msg, 'message_type':'success',
              'login': User()})
        return render(request,'html/register.html',
              {'message':msg, 'message_type':'fail', 'registration':user})
    else:
        return render(request,'html/register.html',
              {'registration':user})

def external_address(request):
    manager = ModelManager()
    if request.method == 'GET':
       user_id = int(request.GET.get('id'))
       user_addr = manager.get_user_address(user_id)
       return render(request, 'html/update_external_address.html',
            { 'user_external_address': user_addr })
    else:
        user_id = int(request.POST['userId'])
        address = request.POST['address']
        alias = request.POST['alias']
        rc, message = manager.upsert_user_external_address(user_id, address, alias)
        if rc == 0:
            useraccountInfo = manager.get_user_accountInfo(request.session['username'])
            return render(request, 'html/myaccount.html', {'useraccountInfo': useraccountInfo})
        else:
            user_addr = manager.get_user_address(user_id)
            return render(request, 'html/update_external_adress.html',
               { 'user_external_address': user_addr })
def payment_method(request):
    manager = ModelManager()
    payment_providers = []
    provider = PaymentProvider()
    provider.code = 'weixin'
    provider.name = '微信支付'
    payment_providers.append(provider)
    provider = PaymentProvider()
    provider.code = 'alipay'
    provider.name = '支付宝'
    payment_providers.append(provider)
    provider = PaymentProvider()
    provider.code = 'heepay'
    provider.name = '汇钱包'
    payment_providers.append(provider)

    if request.method == 'GET':
        userid = int(request.GET.get('id'))
        user_payment_methods = manager.get_user_payment_methods(userid)
        return render(request, 'html/update_payment_method.html',
            {'user_payment_methods':user_payment_methods,
             'userid': userid,
             'payment_providers': payment_providers})
    else:
        userid = int(request.POST['id'])
        payment_provider = request.POST['payment_provider']
        account = request.POST['account']
        rc, msg = manager.upsert_user_payment_method(userid, payment_provider, account)
        if rc == 0:
            return redirect(request, 'accountinfo', { 'rc': rc, 'message': msg})
        else:
            user_payment_methods = manager.get_user_payment_methods(userid)
            return render(request, 'html/update_payment_method.html',
               {'user_payment_methods':user_payment_methods,
                'userid': userid,
                'payment_providers': payment_providers})

def query_user_open_sell_orders(userlogin):
    return Order.objects.filter(user__login = userlogin).filter(order_type='SELL').filter(~Q(status='FILLED') | ~Q(status='CANCELLED'))

def query_buy_orders(userlogin):
    return Order.objects.select_related('reference_order','reference_order__user').filter(reference_order__user__login= userlogin)

def transfer(request):
    return render(request, 'html/myaccount.html')

def mysellorder(request):
    username = request.session['username']
    manager = ModelManager()
    status = None
    if request.method == 'POST':
        units = float(request.POST['quantity']),
        unit_price = float(request.POST['unit_price']),
        unit_price_currency = request.POST['unit_price_currency'],
        crypto_currency = request.POST['crypto']
        status = manager.create_sell_order(username, units, unit_price,
                    unit_price_currency, crypto_currency)
    sellorders = manager.get_open_sell_orders_by_user(username)
    buyorders = manager.get_pending_incoming_buy_orders_by_user(username)
    return render(request, 'html/mysellorder.html', {'sellorders': sellorders,
            'buyorders':buyorders,'username': username,
            'previous_call_status' : status})

def create_purchase_order(request):
    logger.debug('create_purchase_order()...')
    username = request.POST['username']
    reference_order_id = request.POST['reference_order_id']
    owner_user_id = request.POST['owner_user_id']
    quantity = request.POST['quantity']
    available_units = request.POST['available_units']
    unit_price = request.POST['unit_price']
    payment_provider = request.POST['payment_provider']
    payment_account = request.POST['payment_account']
    total_amount = float(request.POST['total_amount'])
    manager = ModelManager()
    order = manager.create_purchase_order(username, reference_order_id,
           quantity, unit_price, 'CNY', total_amount, 'AXFund')

    print "payment acount is %s" % payment_account
    returnstatus = None
    # if buyer has payment method that match seller's payment payment_method
    # set buyer account
    buyer_account = ''
    accountinfo = request.session[REQ_KEY_USERACCOUNTINFO]
    if accountinfo is not None and accountinfo.paymentmethods is not None:
       for method in accountinfo.paymentmethods:
           if method.provider_code == payment_provider:
              buyer_account = method.account_at_provider
              break

    # read the sitsettings
    sitesettings = context_processor.settings(request)['settings']
    notify_url = 'http://{0}:{1}/mysellorder/heepay/confirm_payment/'.format(sitesettings.heepay_notify_url_host, sitesettings.heepay_notify_url_port)
    return_url = 'http://{0}:{1}/purchase/createorder2/heepay/confirmed/'.format(sitesettings.heepay_return_url_host, sitesettings.heepay_return_url_port)
    if (payment_provider == 'heepay'):
        heepay = HeePayManager()
        json_payload = heepay.create_heepay_payload('wallet.pay.apply',
             order.order_id,
             sitesettings.heepay_app_id.encode('ascii'),
             sitesettings.heepay_app_key.encode('ascii'),
             '127.0.0.1', order.total_amount,
             payment_account,
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

def confirm_payment(request):
    username = request.session['username']
    orderid = request.POST['order_id']
    manager = ModelManager()
    manager.confirm_payment(username, orderid)
    return redirect('accountinfo')

def heepay_confirm_payment(request):
    if request.method == 'POST':
       json_data = json.loads(request.body) # request.raw_post_data w/ Django < 1.4
       print "we recevied from heepay %s" % json.dumps(json_data)
    else:
       print "surprise we get GET notification from heepay"
    return redirect('purchase')
