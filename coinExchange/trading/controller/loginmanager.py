#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import transaction
from django.db.models import Q
from trading.models import *
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm

#from trading.forms import *
import logging,json

# logger for user registration
logger = logging.getLogger("site.registration")

def create_login(regform, username):
    with transaction.atomic():
        regform.save()
        user = User.objects.get(username=username)
        if (len(UserWallet.objects.all())!=3):
            raise ValueError("There is no user wallet data here")
        user_wallet = UserWallet.objects.select_for_update().filter(Q(user__isnull=True))[0]
        user_wallet.user = user
        user_wallet.save()
