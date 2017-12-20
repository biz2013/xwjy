#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz

from users.models import *

def create_sell_order(user_id, units, unit_price,
              unit_price_currency, crypto_currency,
              created_by):
    userobj = User.objects.get(id = user_id)
    created_by_user = UserLogin.objects.get(username = created_by)
    crypto = Cryptocurrency.objects.get(currency_code = crypto_currency)
    order = Order.objects.create(
        user= userobj,
        created_by = created_by_user,
        lastupdated_by = created_by_user,
        reference_order=None,
        cryptocurrency= crypto,
        order_type='SELL',
        sub_type = 'OPEN',
        units = units,
        unit_price = unit_price,
        unit_price_currency = unit_price_currency,
        status = 'OPEN')
    order.save()
