#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging

from django.db import transaction
from django.db.models import F
from users.models import *
from views.models.orderitem import OrderItem
from views.models.userpaymentmethodview import *

logger = logging.getLogger("site.ordermanager")

def get_user_payment_account(user_id, payment_provider_code):
    return UserPaymentMethod.objects.filter(user__id=user_id).filter(provider__code=payment_provider_code)

def get_seller_buyer_payment_accounts(buyorder_id, payment_provider):
    buyorder = Order.objects.get(pk=buyorder_id)
    sellorder = Order.objects.get(pk=buyorder.reference_order.order_id)
    logger.info("seller {0} buyer {1} payment_provider {2}".format(sellorder.user.id, buyorder.user.id, payment_provider))
    seller_payment_method = UserPaymentMethod.objects.get(user__id=sellorder.user.id, provider__code = payment_provider)
    buyer_payment_method = UserPaymentMethod.objects.get(user__id=buyorder.user.id, provider__code = payment_provider)
    return seller_payment_method.account_at_provider, buyer_payment_method.account_at_provider

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
           units_locked = 0,
           total_amount = order.total_amount,
           status = 'OPEN')
        logger.info("order {0} created".format(orderRecord.order_id))
        userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = userwallet,
          balance_begin = userwallet.balance,
          balance_end = userwallet.balance,
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
        logger.info('userwallet transaction {0} for order {1} userwallet{2} created'.format(
            userwallet_trans.id, orderRecord.order_id, userwallet.id
        ))
        userwallet.user_wallet_trans_id = userwallet_trans.id
        userwallet.locked_balance = userwallet.locked_balance + order.total_units
        userwallet.available_balance = userwallet.available_balance - order.total_units
        userwallet.save()
        logger.info('After creating order {0}, userwallet {1} has balance:{2} available_balance:{3} locked_balance: {4}'.format(
           orderRecord.order_id, userwallet.id, userwallet.balance, userwallet.available_balance, userwallet.locked_balance
        ))
        return orderRecord.order_id

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
    crypto_currency = Cryptocurrency.objects.get(pk=buyorder.crypto)
    operation_comment = 'User {0} open buy order {1} with total {2}{3}({4}x@{5})'.format(
        buyorder.owner_user_id, buyorder.order_id, buyorder.total_amount,
        buyorder.unit_price_currency, buyorder.total_units,
        buyorder.unit_price)
    order = None
    with transaction.atomic():
        userwallet = UserWallet.objects.select_for_update().get(user__id=buyorder.owner_user_id)
        reference_order = Order.objects.select_for_update().get(pk=reference_order_id)
        if reference_order.status != 'PARTIALFILLED' and reference_order.status != 'OPEN':
            return None, 'SELLORDER_NOT_OPEN'
        if buyorder.total_units > reference_order.units_available_to_trade:
            logger.error('sell order %s has %f to trade, buyer buy %f units' % (
                      reference_order.order_id,
                      reference_order.units_available_to_trade,
                      buyorder.total_units))
            return None, 'BUY_EXCEED_AVAILABLE_UNITS'
        logger.info('before creating order {0}, userwallet {1} has balance:{2} available_balance:{3} locked_balance: {4}'.format(
           frmt_date, userwallet.id, userwallet.balance, userwallet.available_balance, userwallet.locked_balance
        ))
        order = Order.objects.create(
            order_id = buyorder.order_id,
            user= User.objects.get(pk=buyorder.owner_user_id),
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
        logger.info("order {0} created".format(order.order_id))
        userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = userwallet,
          reference_order = order,
          reference_wallet_trxId = '',
          amount = buyorder.total_amount,
          balance_update_type= 'CREDIT',
          transaction_type = 'OPEN BUY ORDER',
          comment = operation_comment,
          reported_timestamp = 0,
          status = 'PENDING',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
        logger.info('userwallet transaction {0} for order {1} userwallet{2} created'.format(
            userwallet_trans.id, order.order_id, userwallet.id
        ))
        reference_order.status = 'LOCKED'
        reference_order.units_locked = reference_order.units_locked + buyorder.total_units
        reference_order.units_available_to_trade = reference_order.units_available_to_trade - buyorder.total_units
        reference_order.save()
        logger.info('After creating buy order {0}, sell order {1} has available_units:{2} locked_units: {3} original units: {4}'.format(
           order.order_id, reference_order.order_id,
           reference_order.units_available_to_trade,
           reference_order.units_locked,
           reference_order.units
        ))

    return order.order_id if order is not None else None

def update_order_with_heepay_notification(notify_json, operator):
    """ a) the payment provider will call a specific url of us, and post a standard notification http://dev.heepay.com/index.php?s=/55&page_id=540
  b) need to parse and validate it (validate the sign)
  c) if the payment is success, in a transaction.atomic() scope
     i) find referred purchase order, update status to paid,
     ii) find the sell order of the purchase order, find the UserWallet associated with it, create a DEBT UserWalletTransaction, to debt purchased amount from seller UserWallet balance and available balance.
     iii ) update sell order's available_units -= purchase amount.  locked_amount += purchase_amount, order status = 'PARTIALFILLED' if available_balance > 0, and become 'FILLED' if available_balance ==0
    iv ) create UserWalletTransaction for buyer, CREDIT buyer UserWallet with purchase amount on balance and available_balance
    v) purchase order status is 'FILLE
        {
    	"version": "1.0",
    	"app_id": "hyq17121610000800000911220E16AB0",
    	"subject": "购买1.020000CNY",
    	"out_trade_no": "20180102122319_293146",
    	"hy_bill_no": "180102122300364021000081666",
    	"payment_type": "Alipay",
    	"total_fee": "1",
    	"trade_status": "Success",
    	"real_fee": "1",
    	"payment_time": "20180102122507",
    	"api_account_mode": "Account",
    	"to_account": "15811302702",
    	"from_account": "18600701961",
    	"sign": "EEB980CD2663C9E27C7A38094410CB60"
    }
        """
    logger.info('update_order_with_heepay_notification(with hy_bill_no {0} out_trade_no {1}'.format(
        notify_json['hy_bill_no'], notify_json['out_trade_no']
    ))
    operatorObj = UserLogin.objects.get(pk=operator)

    # get original buy order

    #get the original purchase user_wallet_trans
    purchase_trans = UserWalletTransaction.objects.get(
          reference_order__order_id=notify_json['out_trade_no'],
          status='PENDING',
          transaction_type='OPEN BUY ORDER')
    buyer_user_wallet = purchase_trans.user_wallet
    logger.info('For hy_bill_no {0} find purchase userwallet trans id {1}, refer to wallet {2}'.format(
           notify_json['hy_bill_no'], purchase_trans.id, buyer_user_wallet.id
    ))

    buyorder = purchase_trans.reference_order
    logger.info('For hy_bill_no {0} find buy order id {1}'.format(
           notify_json['hy_bill_no'], buyorder.order_id
    ))
    buyer_userid = buyorder.user.id
    sellorder = buyorder.reference_order
    logger.info('for hy_bill_no {0} find related seller order {1}'.format(
          notify_json['hy_bill_no'], sellorder.order_id
    ))
    with transaction.atomic():
        seller_user_wallet = UserWallet.objects.select_for_update().get(
             user__id=sellorder.user.id,
             wallet__cryptocurrency__currency_code = purchase_trans.user_wallet.wallet.cryptocurrency.currency_code)
        buyer_user_wallet = UserWallet.objects.select_for_update().get(
            pk=buyer_user_wallet.id)
        sellorder = Order.objects.get(pk=sellorder.order_id)
        purchase_trans = UserWalletTransaction.objects.select_for_update().get(pk=purchase_trans.id)
        buyorder = Order.objects.select_for_update().get(pk=buyorder.order_id)
        sell_order_fulfill_comment = 'deliver on buyer order {0}, with {1} units on payment bill no {2}'.format(
             buyorder.order_id, buyorder.units, notify_json['hy_bill_no']
        )
        seller_userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = seller_user_wallet,
          balance_begin = seller_user_wallet.balance,
          balance_end = seller_user_wallet.balance - buyorder.units,
          locked_balance_begin = seller_user_wallet.locked_balance,
          locked_balance_end = seller_user_wallet.locked_balance - buyorder.units,
          available_to_trade_begin = seller_user_wallet.available_balance,
          available_to_trade_end = seller_user_wallet.available_balance,
          reference_order = sellorder,
          reference_wallet_trxId = '',
          amount = buyorder.units,
          balance_update_type= 'DEBT',
          transaction_type = 'DELIVER ON PURCHASE',
          comment = sell_order_fulfill_comment,
          reported_timestamp = 0,
          status = 'PROCESSED',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
        purchase_trans.balance_begin = buyer_user_wallet.balance
        purchase_trans.balance_end = buyer_user_wallet.balance + buyorder.units
        purchase_trans.locked_balance_begin = buyer_user_wallet.locked_balance
        purchase_trans.locked_balance_end = buyer_user_wallet.locked_balance
        purchase_trans.available_balance_begin = buyer_user_wallet.available_balance
        purchase_trans.available_balance_end = buyer_user_wallet.available_balance + buyorder.units
        purchase_trans.status = 'PROCESSED'
        purchase_trans.lastupdated_by = operatorObj
        purchase_trans.save()

        sellorder.units_locked = F('units_locked') - buyorder.units
        sellorder.status = 'PARTIALFILLED'
        if sellorder.units_available_to_trade == 0:
            sellorder.status == 'FILLED'
        sellorder.lastupdated_by = operatorObj
        sellorder.save()

        buyorder.payment_bill_no = notify_json['hy_bill_no']
        buyorder.payment_status = 'SUCCESS'
        buyorder.status = 'FILLED'
        buyorder.lastupdated_by = operatorObj
        buyorder.save()

        buyer_user_wallet.balance = purchase_trans.balance_end
        buyer_user_wallet.locked_balance = purchase_trans.locked_balance_end
        buyer_user_wallet.available_balance = purchase_trans.available_balance_end
        buyer_user_wallet.user_wallet_trans_id = buyer_user_wallet.id
        buyer_user_wallet.lastupdated_by = operatorObj
        buyer_user_wallet.save()

        seller_user_wallet.balance = seller_userwallet_trans.balance_end
        seller_user_wallet.locked_balance = seller_userwallet_trans.locked_balance_end
        seller_user_wallet.available_balance = seller_userwallet_trans.available_to_trade_end
        seller_user_wallet.user_wallet_trans_id = seller_userwallet_trans.id
        seller_user_wallet.lastupdated_by = operatorObj
        seller_user_wallet.save()

def get_order_owner_info(order_id):
    order = Order.objects.get(pk=order_id)
    return order.user.id, order.user.login.username

def cancel_sell_order(userid, order_id, crypto, operator):
    operatorObj = UserLogin.objects.get(username=operator)
    with transaction.atomic():
        user_wallet = UserWallet.objects.select_for_update().get(
            user__id=userid,
            wallet__cryptocurrency__currency_code = crypto)
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status == 'LOCKED' or order.status == 'CANCELLED':
            logger.error('order {0} has status {1}, can\'t be cancelled anymore'.format(
               order_id, order.status
            ))
            raise ValueError("order has been locked or cancelled")
        order.status = 'CANCELLED'
        order.lastupdated_by = operatorObj
        order.save()

        locked_balance_end = user_wallet.locked_balance - order.units_available_to_trade
        available_to_trade_end = user_wallet.available_balance + order.units_available_to_trade
        seller_userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = user_wallet,
          balance_begin = user_wallet.balance,
          balance_end = user_wallet.balance,
          locked_balance_begin = user_wallet.locked_balance,
          locked_balance_end = locked_balance_end,
          available_to_trade_begin = user_wallet.available_balance,
          available_to_trade_end = available_to_trade_end,
          reference_order = order,
          reference_wallet_trxId = '',
          amount = order.units_available_to_trade,
          balance_update_type= 'CREDIT',
          transaction_type = 'CANCEL SELL ORDER',
          comment = 'cancel sell order {0}'.format(order.order_id),
          #TODO: need to get the transaction and its timestamp
          reported_timestamp = time.time(),
          #TODO: need to make it PENDING, if the transaction's confirmation
          # has not reached the threshold
          status = 'PROCESSED',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
        seller_userwallet_trans.save()

        user_wallet.locked_balance = locked_balance_end
        user_wallet.available_balance = available_to_trade_end
        user_wallet.lastupdated_by = operatorObj
        user_wallet.save()

def post_open_payment_order(buyorder_id, payment_provider, bill_no, username):
    operator = UserLogin.objects.get(pk=username)
    buyorder = Order.objects.get(pk=buyorder_id)
    sell_order = Order.objects.get(pk=buyorder.reference_order.order_id)
    with transaction.atomic():
        if buyorder.status != 'CANCELLED':
            updated = sell_order.objects.filter(
                       order_id=buyorder.reference_order.order_id,
                       status='LOCKED').update(status='OPEN',
                                lastupdated_at = dt.utcnow())
            if not updated:
                error_msg = "Purchase order {0}:status{1} is not locked by buy order {2} anymore.  Should not happen.".format(
                        sell_order.order_id, sell_order.status, buyorder.order_id)
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.info("update related sell order {0} status to OPEN".format(sell_order.order_id))
            buyorder.payment_bill_no = bill_no
            buyorder.payment_provider = payment_provider
            buyorder.save()
            logger.info("record {0}.bill#: {1} to related buyorder: {2}".format(
                payment_method, bill_no, buyorder.order_id
            ))
            return True
        else:
            return False
