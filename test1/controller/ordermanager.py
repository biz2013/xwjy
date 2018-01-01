#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging

from django.db import transaction
from users.models import *
from views.models.orderitem import OrderItem
from views.models.userpaymentmethodview import *

logger = logging.getLogger("site.ordermanager")

def get_user_payment_account(user_id, payment_provider_code):
    return UserPaymentMethod.objects.filter(user__id=user_id).filter(provider__code=payment_provider_code)

def create_sell_order(order, operator):
    userobj = User.objects.get(id = order.owner_user_id)
    operatorObj = UserLogin.objects.get(username = operator)
    crypto = Cryptocurrency.objects.get(currency_code = order.crypto)
    frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
    operation_comment = 'User {0} open sell order {1} with total {2}{3}({4}x@{5})'.format(
        order.owner_user_id, frmt_date, order.total_amount,
        order.unit_price_currency, order.total_units,
        order.unit_price)
    logger.info(operation_comment)
    with transaction.atomic():
        userwallet = UserWallet.objects.select_for_update().get(user__id=order.owner_user_id)
        logger.info('before creating order {0}, userwallet {1} has balance:{2} available_balance:{3} locked_balance: {4}'.format(
           frmt_date, userwallet.id, userwallet.balance, userwallet.available_balance, userwallet.locked_balance
        ))
        orderRecord = Order.objects.create(
           order_id = frmt_date,
           user= userobj,
           created_by = operatorObj,
           lastupdated_by = operatorObj,
           reference_order=None,
           cryptocurrency= crypto,
           order_type='SELL',
           sub_type = 'OPEN',
           units = order.total_units,
           unit_price = order.unit_price,
           unit_price_currency = order.unit_price_currency,
           units_available_to_trade = order.total_units,
           units_balance = order.total_units,
           total_amount = order.total_amount,
           status = 'OPEN')
        orderRecord.save()
        logger.info("order {0} created".format(orderRecord.order_id))
        userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = userwallet,
          balance_begin = userwallet.balance,
          balance_end = userwallet.balance - order.total_units,
          locked_balance_begin = userwallet.locked_balance,
          locked_balance_end = userwallet.locked_balance + order.total_units,
          available_to_trade_begin = userwallet.available_balance,
          available_to_trade_end = userwallet.available_balance - order.total_units,
          reference_order = orderRecord,
          reference_wallet_trxId = '',
          amount = order.total_amount,
          balance_update_type= 'DEBT',
          transaction_type = 'OPEN SELL ORDER',
          comment = operation_comment,
          #TODO: need to get the transaction and its timestamp
          reported_timestamp = 0,
          #TODO: need to make it PENDING, if the transaction's confirmation
          # has not reached the threshold
          status = 'PROCESSED',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
        userwallet_trans.save()
        logger.info('userwallet transaction {0} for order {1} userwallet{2} created'.format(
            userwallet_trans.id, orderRecord.order_id, userwallet.id
        ))
        userwallet.user_wallet_trans_id = userwallet_trans.id
        userwallet.balance = userwallet.balance - order.total_units
        userwallet.available_balance = userwallet.available_balance - order.total_units
        userwallet.save()
        logger.info('After creating order {0}, userwallet {1} has balance:{2} available_balance:{3} locked_balance: {4}'.format(
           orderRecord.order_id, userwallet.id, userwallet.balance, userwallet.available_balance, userwallet.locked_balance
        ))

def get_user_open_sell_orders(user_id):
    # only query seller order that is still opened, not
    # fullfiled or cancelled
    sell_orders = Order.objects.filter(user__id=user_id).exclude(status='CANCELLED').exclude(status='FILLED').order_by('lastupdated_at')
    orders = []
    for order in sell_orders:
        orders.append(OrderItem(order.order_id, order.user.id,
                                order.user.login.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.total_amount,
                                order.cryptocurrency.currency_code,
                                order.lastupdated_at, order.status))
    return orders

def get_all_open_seller_order_exclude_user(user_id):
    sell_orders = Order.objects.exclude(user__id=user_id).exclude(status='CANCELLED').exclude(status='FILLED').order_by('unit_price')
    orders = []
    for order in sell_orders:
        orders.append(OrderItem(order.order_id, order.user.id,
                                order.user.login.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.total_amount,
                                order.cryptocurrency.currency_code,
                                order.lastupdated_at, order.status))
    return orders

def get_pending_incoming_buy_orders_by_user(userid):
    buyorders = Order.objects.filter(order_type='BUY', reference_order__user__id=userid).exclude(status='CANCELLED').exclude(status='DELIVERED')
    orders = []
    for order in buyorders:
        orders.append(OrderItem(order.order_id, order.user.id, order.user.login.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.total_amount,
                                order.cryptocurrency.currency_code,
                                order.lastupdated_at, order.status))
    return orders

def get_user_payment_methods(user_id):
    userpayments = UserPaymentMethod.objects.filter(user__id=user_id)
    payment_methods= []
    if userpayments is not None:
       for method in userpayments:
          payment_methods.append(UserPaymentMethodView(method.id,
                method.user.id, method.provider.code,
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

def create_purchase_order(buyorder, reference_order_id, operator):
    operatorObj = UserLogin.objects.get(pk=operator)
    frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
    buyorder.order_id = frmt_date
    userobj = User.objects.get(pk=buyorder.owner_user_id)
    crypto_currency = Cryptocurrency.objects.get(pk=buyorder.crypto)
    operation_comment = 'User {0} open buy order {1} with total {2}{3}({4}x@{5})'.format(
        buyorder.owner_user_id, buyorder.order_id, buyorder.total_amount,
        buyorder.unit_price_currency, buyorder.total_units,
        buyorder.unit_price)
    with transaction.atomic():
        reference_order = Order.objects.select_for_update().get(pk=reference_order_id)
        if reference_order.status != 'PARTIALFILLED' and reference_order.status != 'OPEN':
            return 'SELLORDER_NOT_OPEN', buyorder
        if buyorder.total_units > reference_order.units_available_to_trade:
            logger.error('sell order %s has %f to trade, buyer buy %f units' % (
                      reference_order.order_id,
                      reference_order.units_available_to_trade,
                      buyorder.total_units))
            return 'BUY_EXCEED_AVAILABLE_UNITS', buyorder
        userwallet = UserWallet.objects.select_for_update().get(user__id=buyorder.owner_user_id)
        logger.info('before creating order {0}, userwallet {1} has balance:{2} available_balance:{3} locked_balance: {4}'.format(
           frmt_date, userwallet.id, userwallet.balance, userwallet.available_balance, userwallet.locked_balance
        ))
        order = Order.objects.create(
            order_id = buyorder.order_id,
            user= userobj,
            created_by = operatorObj,
            lastupdated_by = operatorObj,
            reference_order= reference_order,
            cryptocurrency= crypto_currency,
            order_type='BUY',
            sub_type='BUY_ON_ASK',
            units = buyorder.total_units,
            unit_price = buyorder.unit_price,
            unit_price_currency = buyorder.unit_price_currency,
            total_amount = buyorder.total_amount,
            status = 'OPEN')
        order.save()
        logger.info("order {0} created".format(order.order_id))
        userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = userwallet,
          balance_begin = userwallet.balance,
          balance_end = userwallet.balance + buyorder.total_units,
          locked_balance_begin = userwallet.locked_balance,
          locked_balance_end = userwallet.locked_balance,
          available_to_trade_begin = userwallet.available_balance,
          available_to_trade_end = userwallet.available_balance + buyorder.total_units,
          reference_order = order,
          reference_wallet_trxId = '',
          amount = buyorder.total_amount,
          balance_update_type= 'CREDIT',
          transaction_type = 'OPEN BUY ORDER',
          comment = operation_comment,
          #TODO: need to get the transaction and its timestamp
          reported_timestamp = 0,
          #TODO: need to make it PENDING, if the transaction's confirmation
          # has not reached the threshold
          status = 'PENDING',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
        userwallet_trans.save()
        logger.info('userwallet transaction {0} for order {1} userwallet{2} created'.format(
            userwallet_trans.id, order.order_id, userwallet.id
        ))
        reference_order.status = 'LOCKED'
        reference_order.units_available_to_trade = reference_order.units_available_to_trade - buyorder.total_units
        reference_order.save()
        logger.info('After creating buy order {0}, sell order {1} has available_units:{2} locked_units: {3} original units: {4}'.format(
           order.order_id, reference_order.order_id,
           reference_order.units_available_to_trade,
           reference_order.units - reference_order.units_available_to_trade,
           reference_order.units
        ))

    buyorder.status = 'OPEN'
    return '', buyorder
