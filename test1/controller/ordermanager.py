#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz

import time
import datetime as dt
import pytz

from users.models import *
from views.models.orderitem import OrderItem

def create_sell_order(user_id, units, unit_price,
              unit_price_currency, crypto_currency,
              created_by):
    userobj = User.objects.get(id = user_id)
    created_by_user = UserLogin.objects.get(username = created_by)
    crypto = Cryptocurrency.objects.get(currency_code = crypto_currency)
    frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
    order = Order.objects.create(
        order_id = frmt_date,
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
        units_available_to_trade = units,
        units_balance = units,
        status = 'OPEN')
    order.save()

def get_user_open_sell_orders(user_id):
    sell_orders = Order.objects.filter(user__id=user_id)
    orders = []
    for order in sell_orders:
        orders.append(OrderItem(order.order_id, order.user.id, order.user.login.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.lastupdated_at, order.status))
    return orders
