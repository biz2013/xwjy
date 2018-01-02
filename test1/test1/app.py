#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.heepaymanager import HeePayManager
from controller.global_utils import *

# this is for test UI. A fake one
from controller.test_model_manager import ModelManager
from controller.global_constants import *
from users.models import *
from views.models.orderitem import OrderItem
from views.models.returnstatus import ReturnStatus

import logging,json

# root logging.
slogger = logging.getLogger("site")
# logger for user registration
rlogger = logging.getLogger("site.registration")

def testpage(request):
    return render(request, 'html/testpage.html')
def home(request):
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

        rlogger.debug("Get registration request : username %s password %s email %s", login.username, login.password, user.email)
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

def confirm_payment(request):
    if request.method == 'POST':
       json_data = json.loads(request.body) # request.raw_post_data w/ Django < 1.4
       print "Return url:we recevied from heepay %s" % json.dumps(json_data)
    else:
       print "Return url:surprise we get GET notification from heepay"
    return redirect('accountinfo')

def heepay_confirm_payment(request):
    if request.method == 'POST':
       json_data = json.loads(request.body) # request.raw_post_data w/ Django < 1.4
       print "we recevied from heepay %s" % json.dumps(json_data)
    else:
       print "surprise we get GET notification from heepay"
    return redirect('purchase')
