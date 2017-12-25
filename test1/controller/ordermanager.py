#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz

from users.models import *
from views.models.orderitem import OrderItem
from views.models.userpaymentmethodview import *

def get_user_payment_account(user_id, payment_provider_code):
    return UserPaymentMethod.objects.filter(user__id=user_id).filter(provider__code=payment_provider_code)

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
    # only query seller order that is still opened, not
    # fullfiled or cancelled
    sell_orders = Order.objects.filter(user__id=user_id).exclude(status='CANCELLED').exclude(status='FILLED').order_by('lastupdated_at')
    orders = []
    for order in sell_orders:
        orders.append(OrderItem(order.order_id, order.user.id, order.user.login.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.lastupdated_at, order.status))
    return orders

def get_all_open_seller_order_exclude_user(user_id):
    sell_orders = Order.objects.exclude(user__id=user_id).exclude(status='CANCELLED').exclude(status='FILLED').order_by('unit_price')
    orders = []
    for order in sell_orders:
        orders.append(OrderItem(order.order_id, order.user.id, order.user.login.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.lastupdated_at, order.status))
    return orders

def get_pending_incoming_buy_orders_by_user(userid):
    buyorders = Order.objects.filter(order_type='BUY', reference_order__user__id=userid).exclude(status='CANCELLED').exclude(status='DELIVERED')
    orders = []
    for order in buyorders:
        orders.append(OrderItem(order.order_id, order.user.id, order.user.login.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.lastupdated_at, order.status))
    return orders

def get_user_payment_methods(user_id):
    userpayments = UserPaymentMethod.objects.filter(user__id=user_id)
    payment_methods= []
    if userpayments is not None:
       for method in userpayments:
          payment_methods.append(UserPaymentMethodView(method.id, method.provider.code,
                method.provider.name,method.account_at_provider,
                method.provider_qrcode_image))
    return payment_methods

def get_sellorder_seller_payment_methods(sell_order_id):
    order = Order.objects.get(pk=sell_order_id)
    userpayments = UserPaymentMethod.objects.filter(user__id=order.user.id)
    payment_methods= []
    if userpayments is not None:
       for method in userpayments:
          payment_methods.append(UserPaymentMethodView(method.id, method.provider.code,
                method.provider.name,method.account_at_provider,
                method.provider_qrcode_image))
    return payment_methods

def create_purchase_order(buyorder, reference_order_id, crypto):
    reference_order = Order.objects.get(pk=reference_order_id)
    if reference_order.status != 'PARTIALFILLED' and reference_order.status != 'OPEN':
        return 'SELLORDER_NOT_OPEN', buyorder
    if buyorder.total_units > reference_order.units_available_to_trade:
        print 'sell order %s has %f to trade, buyer buy %f units' % (
                  reference_order.order_id,
                  reference_order.units_available_to_trade,
                  buyorder.total_units)
        return 'BUY_EXCEED_AVAILABLE_UNITS', buyorder
    frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
    buyorder.order_id = frmt_date
    userobj = User.objects.get(pk=buyorder.owner_user_id)
    created_by_user = UserLogin.objects.get(pk=buyorder.owner_login)
    crypto_currency = Cryptocurrency.objects.get(pk=crypto)
    reference_order.status = 'LOCKED'
    reference_order.units_available_to_trade = reference_order.units_available_to_trade - buyorder.total_units
    reference_order.save()
    order = Order.objects.create(
        order_id = buyorder.order_id,
        user= userobj,
        created_by = created_by_user,
        lastupdated_by = created_by_user,
        reference_order= reference_order,
        cryptocurrency= crypto_currency,
        order_type='BUY',
        sub_type='BUY_ON_ASK',
        units = buyorder.total_units,
        unit_price = buyorder.unit_price,
        unit_price_currency = buyorder.unit_price_currency,
        status = 'OPEN')
    order.save()
    buyorder.status = 'OPEN'
    return '', buyorder
