#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect
from controller.heepaymanager import HeePayManager
from controller.global_utils import *

# this is for test UI. A fake one
from controller.global_constants import *
from controller import loginmanager
from users.models import *
from views.models.orderitem import OrderItem
from views.models.returnstatus import ReturnStatus
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

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
            username = form.cleaned_data.get('username')
            loginmanager.create_login(form, username)
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'html/register.html', {'form': form})

def transfer(request):
    return render(request, 'html/myaccount.html')
