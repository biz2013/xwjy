#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect
from controller.heepaymanager import HeePayManager
from controller.global_utils import *

# this is for test UI. A fake one


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

            user = None
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                user_wallet = UserWallet.objects.select_for_update().filter(Q(user__isnull=True))[0]
                user_wallet.user = user
                user_wallet.save()

            rlogger.info('User register complete') 
            current_site = get_current_site(request)
            mail_subject = '请激活您的美基金账户.'
            message = render_to_string('registration/user_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')

            rlogger.info('Email to {0}'.format(to_email))

            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )

            email.send()
            messages.success(request, '您的注册激活链接已经发到您的注册邮箱{0}。请在三天内激活。'.format(to_email))
            return render(request, 'html/registration/registration_confirm.html')

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
