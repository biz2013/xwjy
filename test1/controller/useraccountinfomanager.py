#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz

from users.models import *
from views.models.useraccountinfo import *
from views.models.userpaymentmethodview import *

def get_user_accountInfo(userid, crypto):
    user = User.objects.get(pk=userid)
    userwallets = UserWallet.objects.filter(user__id= userid).filter(wallet__cryptocurrency__currency_code=crypto)
    available_balance = 0.0
    locked_balance = 0.0
    balance = 0.0
    receiving_addr = ''
    if (len(userwallets) > 0):
        wallet_obj = userwallets[0]
        balance = wallet_obj.balance
        available_balance = wallet_obj.available_balance
        locked_balance = wallet_obj.locked_balance
        receiving_addr = wallet_obj.wallet_addr
    else:
        print '-------- no wallet info for user {0}'.format(userid)
    userpayments = UserPaymentMethod.objects.filter(user__id=userid)
    external_addresses = UserExternalWalletAddress.objects.filter(user__id= userid).filter(cryptocurrency__currency_code=crypto)
    external_address_str = None
    external_address_alias = None
    if len(external_addresses) > 0:
       entrternal_address_object = external_addresses[0]
       external_address_str =  external_address_object.address
       external_address_alias = external_address_object.alias
    payment_methods= []
    if userpayments is not None:
       for method in userpayments:
          payment_methods.append(UserPaymentMethodView(method.id, method.provider.code,
                method.provider.name,method.account_at_provider,
                method.provider_qrcode_image))
    userInfo = UserAccountInfo(user.login, user.id,
          balance,
          locked_balance,
          available_balance,
          receiving_addr,
          external_address_str,
          external_address_alias,
          payment_methods)
    return userInfo
