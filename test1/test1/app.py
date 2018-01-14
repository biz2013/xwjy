#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.heepaymanager import HeePayManager
from controller.global_utils import *

# this is for test UI. A fake one
from controller.test_model_manager import ModelManager
from controller.token import account_activation_token

from controller.global_constants import *
from controller import loginmanager
from users.models import *
from views.models.orderitem import OrderItem
from views.models.returnstatus import ReturnStatus

from django.template.loader import render_to_string
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.sites.shortcuts import get_current_site

from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from django.core.mail import EmailMessage
from django.http import HttpResponse

from test1.forms import *
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

def registration(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # username = form.cleaned_data.get('username')
            # loginmanager.create_login(form, username)
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=username, password=raw_password)
            # login(request, user)
            # return redirect('home')
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your blog account.'
            message = render_to_string('registration/user_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignUpForm()
    return render(request, 'html/register.html', {'form': form})

def activate_user_registration(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')
        #return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')

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
    slogger.info("get into return_url")
    if request.method == 'POST':
       json_data = json.loads(request.body) # request.raw_post_data w/ Django < 1.4
       slogger.info("Return url:we recevied from heepay %s" % json.dumps(json_data))
    else:
       slogger.info("Return url:surprise we get GET notification from heepay")
    return redirect('accountinfo')

def heepay_confirm_payment(request):
    slogger.info("enter heepay_confirm_payment")
    if request.method == 'POST':
       json_data = json.loads(request.body) # request.raw_post_data w/ Django < 1.4
       slogger.info("we recevied from heepay %s" % json.dumps(json_data))
    else:
       slogger.info("surprise we get GET notification from heepay")
    return redirect('purchase')
