#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging
import json
from calendar import timegm

from django.db import transaction
from django.db.models import F, Q, Count
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from tradeex.data.api_const import *
from tradeex.models import *
from tradeex.utils import *
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
from trading.models import *
from trading.controller.global_constants import *
from trading.controller import userpaymentmethodmanager
from trading.controller.useraccountinfomanager import *
from trading.views.models.orderitem import OrderItem
from trading.views.models.ordertransitem import *
from trading.views.models.userpaymentmethodview import *

logger = logging.getLogger("site.ordermanager")

def sell_order_to_str(sell_order):
    description = "[{0}]:type: {1} subtype: {2} source: {3} status: {4} total: {5} ({6}*@{7}): locked: {8} available: {9}".format(
        sell_order.order_id,
        sell_order.order_type, sell_order.sub_type, sell_order.order_source,
        sell_order.status,
        sell_order.total_amount, sell_order.units, sell_order.unit_price,
        sell_order.units_locked, sell_order.units_available_to_trade
    )   

    diff = sell_order.units_locked + sell_order.units_available_to_trade - sell_order.units
    if diff > 0 or diff > MIN_CRYPTOCURRENCY_UNITS:
        description = "{0} INCONSISTANT!!! {1}+{2}-{3}={4}".format(
            description, sell_order.units_locked, sell_order.units_available_to_trade,
            sell_order.units, diff
        )

    return description

def get_user_payment_account(user_id, payment_provider_code):
    return UserPaymentMethod.objects.filter(user__id=user_id).filter(provider__code=payment_provider_code)

# Now we expect each sell order has its selected payment method, the legacy
# code does not have it.  So we want to do update here to update the data.
# If sell order is for CNY and seller has weixin fully setup, this function 
# will set selected payment provider to weixin.  If the order is for CAD and 
# seller has paypal setup, we will set payment provider to paypal.  If somehow 
# seller does not have weixin or paypal fully setup we actually will raise 
# value error as this is bad data and indicate bug when sell order was created
def get_and_update_sell_order_payment_methods(sell_order_id):
    with transaction.atomic():
        sell_order = Order.objects.select_for_update().get(pk=sell_order_id)
        if sell_order.order_source == 'TRDESITE':
            if sell_order.selected_payment_provider and sell_order.account_at_selected_payment_provider:
                return UserPaymentMethod.objects.get(user__id=sell_order.user.id, 
                    provider__code=sell_order.selected_payment_provider.code)
            elif sell_order.unit_price_currency == 'CNY':
                weixin = userpaymentmethodmanager.get_weixin_paymentmethod(sell_order.user.id)
                if not (weixin and weixin.provider_qrcode_image):
                    raise ValueError(ERR_SELLER_WEIXIN_NOT_FULLY_SETUP)
                sell_order.selected_payment_provider = weixin
                sell_order.account_at_selected_payment_provider = weixin.account_at_provider
                sell_order.save()
                return weixin
            elif sell_order.unit_price_currency == 'CAD':
                paypal = userpaymentmethodmanager.get_user_paypal_payment_method(sell_order.user.id)
                if not (paypal and paypal.client_id and paypal.client_secret):
                    raise ValueError(ERR_SELLER_PAYPAL_NOT_FULLY_SETUP)
                sell_order.selected_payment_provider = paypal
                sell_order.account_at_selected_payment_provider = paypal.account_at_provider
                sell_order.save()
                return paypal
        else:
            try:
                api_trans = APIUserTransaction.objects.get(reference_order_id=sell_order.order_id, action = API_METHOD_REDEEM)
                return None

            except APIUserTransaction.DoesNotExist:
                raise ValueError(ERR_API_SELLER_NO_API_RECORD)

def get_seller_buyer_payment_accounts(buyorder_id, payment_provider):
    buyorder = Order.objects.get(pk=buyorder_id)
    sellorder = Order.objects.get(pk=buyorder.reference_order.order_id)
    buyer_account = buyorder.account_at_selected_payment_provider
    seller_account = sellorder.account_at_selected_payment_provider

    if not seller_account:
        if sellorder.order_source == 'TRADESITE':
            try:
                seller_payment_method = UserPaymentMethod.objects.get(user__id=sellorder.user.id, provider__code = payment_provider)
                seller_account = seller_payment_method.account_at_provider
            except:
                logger.error('get_seller_buyer_payment_accounts(buyorder: {0}, {1}): seller order {2} could not find payment provider for buyer order'.format(
                    buyorder_id, payment_provider, sellorder.order_id
                ))
                raise ValueError(ERR_CANNOT_FIND_SELLER_PAYMENT_PROVIDER)
        else:
            raise ValueError(ERR_CANNOT_FIND_SELLER_PAYMENT_PROVIDER)
            
    if not buyer_account:
        if buyorder.order_source == 'TRADESITE':
            try:
                buyer_payment_method = UserPaymentMethod.objects.get(user__id=buyorder.user.id, provider__code = payment_provider)
                buyer_account = buyer_payment_method.account_at_provider
            except:
                logger.error('get_seller_buyer_payment_accounts(buyorder: {0}, {1}): could not find payment provider for buyer order'.format(
                    buyorder_id, payment_provider
                ))
                raise ValueError(ERR_CANNOT_FIND_BUYER_PAYMENT_PROVIDER)
        else:
            raise ValueError(ERR_CANNOT_FIND_BUYER_PAYMENT_PROVIDER)

    return seller_account, buyer_account

def get_unfilled_purchase_orders():
    return Order.objects.filter(Q(status='PAYING') |
       Q(status='PAID') | Q(status='OPEN') | Q(status=TRADE_STATUS_BADRECEIVINGACCOUNT),
       Q(order_type='BUY')).order_by('-lastupdated_at')

def create_sell_order(order, operator, api_user = None,  api_redeem_request = None,
         api_trans_id = None):
    userobj = User.objects.get(id = order.owner_user_id)
    operatorObj = User.objects.get(username = operator)
    crypto = Cryptocurrency.objects.get(currency_code = order.crypto)

    try:
        seller_payment_method= UserPaymentMethod.objects.get(
                user__id=order.owner_user_id, provider__code = order.selected_payment_provider)
    except UserPaymentMethod.DoesNotExist:
        logger.error('create_sell_order(): failed to find user payment provider code {0} for seller {1}:{2}'.format(
                order.selected_payment_provider, userobj.id, userobj.username
        ))
        raise ValueError(ERR_CANNOT_FIND_SELLER_PAYMENT_PROVIDER)

    seller_payment_account =  order.account_at_payment_provider
    if not seller_payment_account:
        try:
            userpaymentmethod = UserPaymentMethod.objects.get(user__id=userobj.id, provider__code=payment_provider_code)
            seller_payment_account = userpaymentmethod.account_at_provider
        except:
            logger.error('create_sell_order(): failed to find user payment method for seller {0}:{1}'.format(
                userobj.id, userobj.username
            ))

            raise ValueError(ERR_CANNOT_FIND_SELLER_PAYMENT_ACCOUNT)
    logger.info('create_sell_order(): get seller {0}:{1}\'s payment account {2}:{3}'.format(
        userobj.id, userobj.username, seller_payment_method.provider.code, seller_payment_account
    ))

    frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
    operation_comment = 'User {0} open {6} sell order {1} with total {2}{3}({4}x@{5}). {6}'.format(
        order.owner_user_id, frmt_date, order.total_amount,
        order.unit_price_currency, order.total_units,
        order.unit_price, 
        'normal ' if not api_trans_id else 'api')
    logger.info(operation_comment)
    
    with transaction.atomic():
        # if api_trans_id provided, this is an api redeem call, so we create transaction
        # anyway.  then we check whether cny wallet of the api user has enough fund
        # if not, then, return api_tran_id, but no sell_order_id, caller will treat it
        # as signal to wait for fund to be ready.  The waiting time is the same as the
        # expiration time.
        api_trans = None
        user_cny_wallet = None
        total_fee_in_decimal = 0
        logger.debug('begin trans to create sell order')
        if api_trans_id:
            logger.debug('create_sell_order(): create api_trans with id {0}'.format(api_trans_id))
            try:
                api_trans = APIUserTransaction.objects.get(pk=api_trans_id)
            except APIUserTransaction.DoesNotExist:
                api_trans = APIUserTransaction.objects.create(
                    transactionId = api_trans_id,
                    api_out_trade_no = api_redeem_request.out_trade_no,
                    api_user = api_user,
                    payment_provider = PaymentProvider.objects.get(code= api_redeem_request.payment_provider),
                    payment_account = api_redeem_request.payment_account,
                    seller_payment_method = seller_payment_method,
                    action = api_redeem_request.method,
                    client_ip = api_redeem_request.client_ip,
                    subject = api_redeem_request.subject,
                    total_fee = api_redeem_request.total_fee,
                    attach = api_redeem_request.attach,
                    request_timestamp = api_redeem_request.timestamp,
                    original_request = json.dumps(api_redeem_request.original_json_request),
                    payment_provider_last_notify = '',
                    payment_provider_last_notified_at = None,
                    notify_url = api_redeem_request.notify_url,
                    return_url = api_redeem_request.return_url,
                    expire_in_sec=api_redeem_request.expire_minute * 60,
                    created_by = operatorObj,
                    lastupdated_by= operatorObj
                )
            # check current available balance of api user's cny balance 
            user_cny_wallet = UserWallet.objects.select_for_update().get(user__id = userobj.id, wallet__cryptocurrency__currency_code ='CNY')
            total_fee_in_decimal = round(float(api_redeem_request.total_fee)/100.0, 2)
            if round(user_cny_wallet.available_balance - total_fee_in_decimal, 2) < 0:
                error_msg = "user {0} does not have enough CNY in wallet {1}: available {2} to be sold {3}".format(
                userobj.username, user_cny_wallet.id, user_cny_wallet.available_balance, total_fee_in_decimal 
                )
                logger.error(error_msg)
                api_trans.last_status_description = error_msg
                api_trans.trade_status = TRADE_STATUS_NOTSTARTED
                api_trans.payment_status = PAYMENT_STATUS_NOTSTARTED
                # return transId but none orderId meaning there is no enough fund in the cny wallet
                api_trans.save()
                return None

        userwallet = UserWallet.objects.select_for_update().get(
                user__id=order.owner_user_id,
                wallet__cryptocurrency = crypto)
        if round(userwallet.available_balance - order.total_units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL) < 0:
            error_msg = "user {0} does not have enough AXFund in wallet {1}: available {2} to be sold {3}".format(
                userobj.username, userwallet.id, userwallet.available_balance, order.total_units
            )
            logger.error(error_msg)
            if api_trans:
                api_trans.refresh_from_db()
                api_trans.last_status_description = error_msg
                api_trans.trade_status = TRADE_STATUS_USERABANDON
                api_trans.payment_status = PAYMENT_STATUS_NOTSTARTED
                # return transId but none orderId meaning there is no enough fund in the cny wallet
                api_trans.save()
                return None
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
           order_type= order.order_type,
           sub_type = order.sub_type,
           order_source = order.order_source,
           seller_payment_method = seller_payment_method,
           units = order.total_units,
           unit_price = order.unit_price,
           unit_price_currency = order.unit_price_currency,
           units_available_to_trade = order.total_units,
           units_locked = 0,
           total_amount = order.total_amount,
           status = 'OPEN')
        logger.info("create_sell_order(): sell order {0} created".format(orderRecord.order_id))
        
        if api_trans:
            logger.info("create_sell_order(): remember sell order {0} in api transaction {1}".format(
                orderRecord.order_id, api_trans.transactionId
            ))
            api_trans.reference_order = orderRecord
            api_trans.payment_status = PAYMENT_STATUS_NOTSTARTED
            api_trans.trade_status = TRADE_STATUS_INPROGRESS
            api_trans.save()

            user_cny_wallet.available_balance = user_cny_wallet.available_balance - total_fee_in_decimal
            user_cny_wallet.locked_balance = user_cny_wallet.locked_balance + total_fee_in_decimal
            user_cny_wallet.save()
         
        userwallet.locked_balance = userwallet.locked_balance + order.total_units
        userwallet.available_balance = userwallet.available_balance - order.total_units
        userwallet.save()
        logger.info('create_sell_order(): Created {5} sell order {0}, units {1} user\'s wallet: balance:{2} available_balance:{3} locked_balance: {4} {5}'.format(
           orderRecord.order_id, orderRecord.units, userwallet.balance, userwallet.available_balance, 
           userwallet.locked_balance, order.order_source,
           'reference by api trans {0}'.format(api_trans.transactionId) if api_trans else ''
        ))
        return orderRecord.order_id

def update_api_trans_after_cancel_order(api_trans, final_status, payment_status, operator):
    if api_trans:
        api_trans.payment_status = payment_status
        # this is for transaction manager cancel purchase
        if final_status == TRADE_STATUS_USERABANDON and payment_status == PAYMENT_STATUS_USERABANDON:
            api_trans.trade_status = final_status
        elif final_status == 'CANCELLED' and (payment_status.upper() in [ PAYMENT_STATUS_UNKONWN.upper(), 'UNKNOWN']):
            api_trans.trade_status = TRADE_STATUS_EXPIREDINVALID
        elif final_status == TRADE_STATUS_BADRECEIVINGACCOUNT:
            api_trans.trade_status = final_status
        else:
            timediff = timezone.now() - api_trans.created_at
            if timediff.total_seconds() > api_trans.expire_in_sec:
                api_trans.trade_status = TRADE_STATUS_EXPIREDINVALID
            else:
                api_trans.trade_status = TRADE_STATUS_USERABANDON
        api_trans.lastupdated_by = operator
        api_trans.save()
        if api_trans.action == API_METHOD_REDEEM and final_status == TRADE_STATUS_BADRECEIVINGACCOUNT:
            APIUserTransactionManager.on_found_redeem_trans_with_badaccount(api_trans)

def cancel_purchase_order(order, final_status, payment_status,
                         operator):
    if not order.reference_order:
        logger.error("cancel_purchase_order({0}, purchase unit: {3} order status:{1}, payment status:{2}): purchase order does not have related sell order".format(
            order.order_id, final_status, payment_status, order.units
        ))
        return
    operatorObj = User.objects.get(username = operator)
    with transaction.atomic():
        sell_order = Order.objects.select_for_update().get(pk=order.reference_order.order_id)
        logger.info("cancel_purchase_order({0}, purchase unit: {4} order status:{1}, payment status:{2}): BEFORE cancelling, related sell order is {3}".format(
            order.order_id, final_status, payment_status, 
            sell_order_to_str(sell_order), order.units
        ))
        
        if round(sell_order.units_locked - order.units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL) < 0:
            raise ValueError('cancel_purchase_order({0}): sell order locked units {1} is less than purchase order units {2}'.format(
                order.order_id, sell_order.units_locked, order.units
            ))
        sell_order.units_locked = round(sell_order.units_locked - order.units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL)
        sell_order.units_available_to_trade = round(sell_order.units_available_to_trade + order.units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL)
        if sell_order.order_source == 'API':
            sell_order.status = 'TRADE_STATUS_USERABANDON'
        else:
            sell_order.status = 'OPEN' if payment_status != PAYMENT_STATUS_BADRECEIVINGACCOUNT else TRADE_STATUS_BADRECEIVINGACCOUNT
        sell_order.lastupdated_by = operatorObj

        # rollback the AXFund wallet of sell order if sell order is not OPEN
        if sell_order.status != 'OPEN':
            updated = UserWallet.objects.filter(
                user__id = sell_order.user.id,
                wallet__cryptocurrency__currency_code = 'AXFund'
            ).update(
                locked_balance = F('locked_balance') - sell_order.units,
                available_balance = F('available_balance') + sell_order.units,                
                lastupdated_by = operatorObj,
                lastupdated_at = dt.datetime.utcnow()
            )
            if updated:
                logger.info('cancel_purchase_order({0}): revert related sell order {1}\'s axf wallet'.format(
                    order.order_id, sell_order.order_id
                ))
            else:
                logger.error('cancel_purchase_order({0}): failed to revert related sell order {1}\'s axf wallet'.format(
                    order.order_id, sell_order.order_id
                ))

        updated = UserWalletTransaction.objects.filter(
               reference_order__order_id= order.order_id,
               status = 'PENDING').update(
               status = final_status,
               payment_status = payment_status,
               lastupdated_by = operatorObj,
               lastupdated_at = dt.datetime.utcnow()
        )
        if not updated:
            logger.error("cancel_purchase_order({0}, purchase units: {3} order status:{1}, payment status:{2}): purchase order does not have PENDING userwallettrans to be updated".format(
                order.order_id, final_status, payment_status, order.units
            ))

        updated = Order.objects.filter(
           Q(status = 'PAYING')|Q(status='OPEN'), Q(order_id = order.order_id)).update(
           status = final_status,
           lastupdated_by = operatorObj,
           lastupdated_at = dt.datetime.utcnow()
        )
        if not updated:
            logger.error("cancel_purchase_order({0}, purchase units: {3} order status:{1}, payment status:{2}): purchase order status is not OPEN or PAYING, maybe someone had changed its status".format(
                order.order_id, final_status, payment_status, order.units
            ))
        
        # try to cancel the api_trans for buy order, if applicable
        api_trans_purchase = APIUserTransactionManager.get_trans_by_reference_order(order.order_id)
        if api_trans_purchase:
            update_api_trans_after_cancel_order(api_trans_purchase, final_status, payment_status, operatorObj)
            APIUserTransactionManager.on_cancel_transaction(api_trans_purchase)
        # try to cancel the api_trans for the sell order, if applicable. We only do this if
        # payment status 'is bad receive account'.  Otherwise, we leave the original API
        # sell order as it is.
        api_trans_sell = APIUserTransactionManager.get_trans_by_reference_order(sell_order.order_id)
        if api_trans_sell and (payment_status == PAYMENT_STATUS_BADRECEIVINGACCOUNT or final_status == TRADE_STATUS_USERABANDON):
            update_api_trans_after_cancel_order(api_trans_sell, final_status, payment_status, operatorObj)
            updated = UserWallet.objects.filter(
                user__id = api_trans_sell.api_user.user.id,
                wallet__cryptocurrency__currency_code = 'CNY'
            ).update(
                locked_balance = F('locked_balance') - sell_order.total_amount,
                available_balance = F('available_balance') + sell_order.total_amount,                
                lastupdated_by = operatorObj,
                lastupdated_at = dt.datetime.utcnow()                
            )
            if updated:
                logger.info('cancel_purchase_order({0}): revert related sell order {1}\'s CNY wallet'.format(
                    order.order_id, sell_order.order_id
                ))
            else:
                logger.error('cancel_purchase_order({0}): failed to revert related sell order {1}\'s CNY wallet'.format(
                    order.order_id, sell_order.order_id
                ))

        sell_order.save()
        sell_order.refresh_from_db()
        logger.info("cancel_purchase_order({0}, purchase units {3} order status:{1}, payment status:{2}): AFTER cancelling, related sell order is {3}".format(
            order.order_id, final_status, payment_status, 
            sell_order_to_str(sell_order), order.units
        ))

def get_all_open_seller_order_exclude_user(user_id):
    sell_orders = Order.objects.filter(order_type='SELL').exclude(user__id=user_id).exclude(status='CANCELLED').exclude(status='FILLED').exclude(status=TRADE_STATUS_BADRECEIVINGACCOUNT).exclude(status=TRADE_STATUS_USERABANDON).order_by('unit_price','-lastupdated_at')
    orders = []
    for order in sell_orders:
        orders.append(OrderItem(order.order_id, order.user.id,
                                order.user.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.total_amount,
                                order.cryptocurrency.currency_code,
                                order.lastupdated_at, order.status, order.order_type,
                                sub_type= order.sub_type,
                                selected_payment_provider=order.selected_payment_provider.code if order.selected_payment_provider else None,
                                account_at_payment_provider=order.account_at_selected_payment_provider,
                                order_source = order.order_source))
    return orders

# called by mysellorderview to get all the buy order and sell order of a user
def get_orders_by_user(userid):
    sell_orders = Order.objects.filter(Q(order_type='SELL'),
            Q(user__id=userid),
            Q(status='OPEN') | Q(status='PARTIALFILLED') | Q(status='LOCKED')).order_by('-lastupdated_at')
    buyorders = Order.objects.filter(Q(order_type='BUY'),
        Q(reference_order__user__id=userid),
        Q(status='PAYING')| Q(status='PAID')).order_by('-lastupdated_at')
    
    buyorder_api_trans = APIUserTransaction.objects.filter(Q(action=API_METHOD_PURCHASE),
        Q(reference_order__reference_order__user__id=userid),
        Q(reference_order__status='PAYING') | Q(reference_order__status='PAID')).order_by('-lastupdated_at')
    
    sell_order_list = []
    for order in sell_orders:
        order_item = OrderItem(order.order_id, order.user.id, order.user.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.total_amount,
                                order.cryptocurrency.currency_code,
                                order.lastupdated_at, order.status, order.order_type,
                                order.sub_type, 
                                order.seller_payment_method.provider.code if order.seller_payment_method else order.selected_payment_provider,
                                order.seller_payment_method.account_at_provider if order.seller_payment_method else order.account_at_selected_payment_provider,
                                order.order_source)
        sell_order_list.append(order_item)

    api_trans_orders = {}
    for api_tran in buyorder_api_trans:
        api_trans_orders[api_tran.reference_order.order_id] = api_tran

    buy_order_list = []    
    for order in buyorders:
        order_username = order.user.username
        if order.sub_type == 'ALL_OR_NOTHING' and order.order_id in api_trans_orders:
            attach = api_trans_orders[order.order_id].attach
            if attach and attach.startswith('username='):
                order_username = attach[len('username='):]
            elif attach and attach.startswith('weixin='):
                order_username = attach[len('weixin='):]

        order_item = OrderItem(order.order_id, order.user.id, order_username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.total_amount,
                                order.cryptocurrency.currency_code,
                                order.lastupdated_at, order.status, order.order_type)
        buy_order_list.append(order_item)

    return sell_order_list, buy_order_list

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

def create_purchase_order(buyorder, reference_order_id,
         seller_payment_provider, operator, 
         api_user = None,  api_purchase_request = None,
         api_trans_id = None, ):

    selected_payment_provider = None
    try:
        selected_payment_provider = PaymentProvider.objects.get(pk=seller_payment_provider)
    except:
        logger.error('create_purchase_order(): failed to find payment provider record with code {0}'.format(
            seller_payment_provider
        ))
        raise ValueError(ERR_CANNOT_FIND_BUYER_PAYMENT_PROVIDER)

    # for now we assume buyer payment account is not consider if seller does not use heepay
    buyer_payment_account = api_purchase_request.payment_account if api_purchase_request else None
    if buyer_payment_account and seller_payment_provider != 'heepay':
        buyer_payment_account = None

    frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
    buyorder.order_id = frmt_date
    is_api_call = api_user and api_purchase_request and api_trans_id
    api_call_order_id = api_purchase_request.out_trade_no if api_purchase_request else None
    operation_comment = ''
    if not is_api_call:
        operation_comment = 'User {0} open buy order {1} with total {2}{3}({4}x@{5})'.format(
        buyorder.owner_user_id, buyorder.order_id, buyorder.total_amount,
        buyorder.unit_price_currency, buyorder.total_units,
        buyorder.unit_price)
    else:
        operation_comment = 'API call out_order_no: {0} create buy order {1} with total {2}{3}({4}x@{5})'.format(
        buyorder.owner_user_id, buyorder.order_id, buyorder.total_amount,
        buyorder.unit_price_currency, buyorder.total_units,
        buyorder.unit_price)

    logger.info('create_purchase_order(): {0}'.format(operation_comment))
    logger.info('create_purchase_order(): selected sellorder {0}'.format(reference_order_id))

    # TODO: more validation
    if is_api_call and not api_call_order_id:
        logger.error("create_purchase_order(): api call has no out_order_no")
        raise ValueError('INVALID_PARAM_API_CALL_ORDER_ID')
    
    operatorObj = User.objects.get(username=operator)
    crypto_currency = Cryptocurrency.objects.get(pk=buyorder.crypto)
    order = None
    with transaction.atomic():
        userwallet = UserWallet.objects.select_for_update().get(
              user__id=buyorder.owner_user_id,
              wallet__cryptocurrency = crypto_currency)
        reference_order = Order.objects.select_for_update().get(pk=reference_order_id)
        logger.info('create_purchase_order(): BEFORE creation, purchase order {0}\'s target sellorder is {1}'.format(
            buyorder.order_id, sell_order_to_str(reference_order)))
        if reference_order.status != 'PARTIALFILLED' and reference_order.status != 'OPEN':
            logger.error('create_purchase_order(): reference_order {0} with status {1}: raise SELLORDER_NOT_OPEN'.format(reference_order_id, reference_order.status))
            raise ValueError('SELLORDER_NOT_OPEN')
        if buyorder.total_units - reference_order.units_available_to_trade > 0:
            logger.error('sell order %s has %f to trade, buyer buy %f units' % (
                      reference_order.order_id,
                      reference_order.units_available_to_trade,
                      buyorder.total_units))
            raise ValueError('BUY_EXCEED_AVAILABLE_UNITS')

        # if the target sell order is requires all or nothing then we have to 
        # make sure the difference between purchase amount and is the same
        if reference_order.sub_type == 'ALL_OR_NOTHING':
            if reference_order.units != reference_order.units_available_to_trade:
                logger.error('ALL_OR_NOTHING sell order %s\'s total unit(%f) and available units(%f) does not match' % (
                    reference_order.order_id, reference_order.total_units,
                    reference_order.units_available_to_trade
                ))
                raise ValueError('ALL_OR_NOTHING_ORDER_INVALID_TOTAL_UNITS')
            if reference_order.units_available_to_trade -  buyorder.total_units > MIN_CRYPTOCURRENCY_UNITS:
                logger.error('Purchase amount %f does not match ALL_OR_NOTHING sell order %s\'s total unit(%f)' % (
                    buyorder.total_units, reference_order.order_id, reference_order.total_units
                ))
                raise ValueError('ALL_OR_NOTHING_ORDER_PURCHASE_AMOUNT_NOT_ENOUGH')

        logger.info('create_purchase_order(): before creating purchase order {0}, userwallet {1} has balance:{2} available_balance:{3} locked_balance: {4}'.format(
           frmt_date, userwallet.id, userwallet.balance, userwallet.available_balance, userwallet.locked_balance
        ))

        order = Order.objects.create(
            order_id = buyorder.order_id,
            user= User.objects.get(pk=buyorder.owner_user_id),
            selected_payment_provider = selected_payment_provider,
            account_at_selected_payment_provider = buyer_payment_account,
            created_by = operatorObj,
            lastupdated_by = operatorObj,
            reference_order= reference_order,
            cryptocurrency= crypto_currency,
            order_type='BUY',
            sub_type='BUY_ON_ASK' if not is_api_call else 'ALL_OR_NOTHING',
            order_source = 'TRADESITE' if not is_api_call else 'API',
            units = buyorder.total_units,
            unit_price = buyorder.unit_price,
            unit_price_currency = buyorder.unit_price_currency,
            total_amount = buyorder.total_amount,
            status = 'OPEN',
            api_call_reference_order_id = api_call_order_id if is_api_call else None)
        order.save()

        order.refresh_from_db()
        logger.info("create_purchase_order(): purchase order {0} created with {1} units with total {2}{3}({4}x@{5})".format(
            order.order_id, order.units, order.total_amount,
            order.unit_price_currency, order.units,
            order.unit_price))

        userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = userwallet,
          reference_order = order,
          reference_wallet_trxId = '',
          units = buyorder.total_units,
          fiat_money_amount = buyorder.total_amount,
          payment_provider = selected_payment_provider,
          balance_update_type= 'CREDIT',
          transaction_type = 'OPEN BUY ORDER',
          comment = operation_comment,
          reported_timestamp = timegm(dt.datetime.utcnow().utctimetuple()),
          status = 'PENDING',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
        userwallet_trans.save()
        logger.info('create_purchase_order(): userwallet transaction {0} for purchase order {1} userwallet{2} created'.format(
            userwallet_trans.id, order.order_id, userwallet.id
        ))

        if is_api_call:
            api_trans = APIUserTransaction.objects.create(
                transactionId = api_trans_id,
                api_out_trade_no = api_purchase_request.out_trade_no,
                api_user = api_user,
                payment_provider = PaymentProvider.objects.get(pk= api_purchase_request.payment_provider),
                reference_order = order,
                payment_account = buyer_payment_account,
                action = api_purchase_request.method,
                client_ip = api_purchase_request.client_ip,
                subject = api_purchase_request.subject,
                total_fee = api_purchase_request.total_fee,
                attach = api_purchase_request.attach,
                request_timestamp = api_purchase_request.timestamp,
                original_request = json.dumps(api_purchase_request.original_json_request),
                payment_provider_last_notify = '',
                payment_provider_last_notified_at = None,
                notify_url = api_purchase_request.notify_url,
                return_url = api_purchase_request.return_url,
                expire_in_sec=api_purchase_request.expire_minute * 60,
                created_by = operatorObj,
                lastupdated_by= operatorObj
            )
            api_trans.save()
            logger.info("create_purchase_order(): API call trans {0} created, out_trade_no {1}, reference order: {2}".format(
                api_trans_id, api_purchase_request.out_trade_no, order.order_id
            ))

        logger.info("create_purchase_order(): before updating sell order, it is {0}".format(
            sell_order_to_str(reference_order)
        ))
        reference_order.status = 'LOCKED'
        reference_order.units_locked = reference_order.units_locked + buyorder.total_units
        reference_order.units_available_to_trade = reference_order.units_available_to_trade - buyorder.total_units
        reference_order.save()
        reference_order.refresh_from_db()
        logger.info('create_purchase_order(): AFTER create purchase order {0}, related sell order is {1}'.format(
            order.order_id, sell_order_to_str(reference_order)))

    return order.order_id if order is not None else None

def lock_trans_of_purchase_order(orderid, bill_no):
    try:
        # TODO: is this needed?
        purchase_trans = UserWalletTransaction.objects.select_for_update().get(
              reference_order__order_id=orderid,
              payment_bill_no = bill_no,
              status='PENDING',
              transaction_type='OPEN BUY ORDER')
        logger.info("--- trans: orderid {0}, pay bill: {1} status {2} trans_type {3} inside call of {4},{5}".format(
              orderid, purchase_trans.payment_bill_no, purchase_trans.status,
              purchase_trans.transaction_type, orderid, bill_no
        ))
        return purchase_trans;
    except UserWalletTransaction.DoesNotExist:
        logger.warn("lock_trans_of_purchase_order(): could not find PENDING trans for purchase order {0} with bill_no {1}, maybe it has been processed".format(orderid, bill_no))
        try:
            return UserWalletTransaction.objects.select_for_update().get(
                  reference_order__order_id=orderid,
                  payment_bill_no = bill_no,
                  status='PROCESSED',
                  transaction_type='OPEN BUY ORDER')
        except UserWalletTransaction.DoesNotExist:
            raise ValueError("lock_trans_of_purchase_order(): could not find the processed trans for purchase order {0} with bill_no {1}, maybe payment failed.".format(orderid, bill_no))
        except UserWalletTransaction.MultipleObjectsReturned:
            raise ValueError("lock_trans_of_purchase_order(): There should be just one processed  trans for purchase order {0} with bill_no {1}".format(orderid, bill_no))
    except UserWalletTransaction.MultipleObjectsReturned:
        raise ValueError("lock_trans_of_purchase_order(): There should be just one wallet transaction for purchase order {0} with bill_no {1}".format(orderid, bill_no))

# Update
def update_purchase_order_payment_transaction(buy_order_id, tran_payment_status, message, external_transaction_id = 'None'):
    with transaction.atomic():
        external_transaction = UserWalletTransaction.objects.select_for_update().get(
            reference_order__order_id=buy_order_id,
            transaction_type='OPEN BUY ORDER')

        if external_transaction_id != 'None':
            external_transaction.payment_bill_no = external_transaction_id

        update_purchase_transaction(external_transaction, tran_payment_status, message)

def update_purchase_transaction(purchase_trans, trade_status, trade_msg):
    normal_status = [ TRADE_STATUS_NOTSTARTED, TRADE_STATUS_PAYSUCCESS, 
          TRADE_STATUS_INPROGRESS, TRADE_STATUS_UNKNOWN, TRADE_STATUS_CREADED, TRADE_STATUS_SUCCESS]

    bad_status = [ TRADE_STATUS_EXPIREDINVALID, TRADE_STATUS_USERABANDON, 
        TRADE_STATUS_DEVCLOSE, TRADE_STATUS_FAILURE]

    if trade_status in normal_status:
        purchase_trans.payment_status = trade_status.upper()
    elif trade_status in bad_status:
        purchase_trans.payment_status = trade_status.upper()
        purchase_trans.comment = trade_msg
        buyorder = purchase_trans.reference_order
        buyorder.status = 'FAILED'
        logger.info("update_purchase_transaction(trade_status {0}): purchase order {1} is set to be failed with payment status {2}, revert locked unit and available units in sell order".format(
            trade_status, buyorder.order_id, purchase_trans.payment_status
        ))

        sell_order = Order.objects.get(pk = buyorder.reference_order.order_id)
        logger.info("update_purchase_transaction(trade_status {0}): BEFORE revert sell order is: {1}".format(
            trade_status, sell_order_to_str(buyorder.reference_order)))
        
        if round(sell_order.units_locked - buyorder.units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL) < 0:
            raise ValueError("update_purchase_transaction(): related purchase order {0}\'s sell order {1} has locked units {2} less then purchase order\'s units {3} ".format(
                buyorder.order_id, sell_order.order_id, 
                sell_order.units_locked, buyorder.units
            ))
        #revert locked unit and available units in sell order
        Order.objects.filter(pk = buyorder.reference_order.order_id).update(
             units_locked = F('units_locked') - buyorder.units,
             units_available_to_trade = F('units_available_to_trade') + buyorder.units,
             lastupdated_at = dt.datetime.utcnow())
        buyorder.save()
        purchase_trans.status = 'PROCESSED'
        sell_order.refresh_from_db()
        logger.info("update_purchase_transaction(trade status {0}): AFTER revert, seller order is : {1}".format(
            trade_status, sell_order_to_str(buyorder.reference_order)))            

    purchase_trans.save()

def get_associated_api_trans_of_buyorder(buy_order_id):
    logger.info('get_order_associated_api_trans({0})'.format(buy_order_id))
    order = Order.objects.get(order_id = buy_order_id)
    if order.order_type != 'BUY':
        raise ValueError('UNEXPECTED_BUY_ORDER')
    
    api_order_id = None
    if order.order_source == 'API':
        api_order_id = order.order_id
    elif order.reference_order and order.reference_order.order_source == 'API':
        api_order_id = order.reference_order.order_id
    else:
        logger.info('get_associated_api_trans_of_buyorder({0}): order has no associated api_trans'.format(
            buy_order_id
        ))
        return None

    try:
        return APIUserTransaction.objects.get(reference_order__order_id= api_order_id)
    except APIUserTransaction.DoesNotExist:
        logger.error('get_associated_api_trans_of_buyorder({0}): the order or its sell order {1}\'s associated api transaction could not be found'.format(
            buy_order_id, order.reference_order.order_id
        ))
        raise ValueError('API_TRANS_SHOULD_HAVE_EXISTED')
    except APIUserTransaction.MultipleObjectsReturned:
        logger.error('get_associated_api_trans_of_buyorder({0}): the order or its sell order {1} has more than one associated api transaction'.format(
            buy_order_id, order.reference_order.order_id
        ))
        raise ValueError('TOO_MANY_ASSOCIATED_API_TRANS')

def update_order_with_heepay_notification(notify_json, operator):
    logger.info('update_order_with_heepay_notification(with hy_bill_no {0} out_trade_no {1}'.format(
        notify_json['hy_bill_no'], notify_json['out_trade_no']
    ))
    operatorObj = User.objects.get(username=operator)

    with transaction.atomic():
        #get the original purchase user_wallet_trans
        purchase_trans = lock_trans_of_purchase_order(notify_json['out_trade_no'],
             notify_json['hy_bill_no'])
        if purchase_trans.status == 'PROCESSED':
            logger.info("The transaction has been processed.  Nothing to do")
            return

        updated = APIUserTransaction.objects.filter(
                Q(reference_order__order_id=purchase_trans.reference_order.order_id) | 
                Q(reference_order__order_id=purchase_trans.reference_order.reference_order.order_id)
            ).update(
                real_fee = notify_json['real_fee'],
                payment_provider_last_notify = json.dumps(notify_json, ensure_ascii=False),
                payment_provider_last_notified_at = dt.datetime.utcnow(),
                payment_account = notify_json.get('from_account', None) if purchase_trans.reference_order.order_source == 'API' else None,
                payment_status = notify_json['trade_status'],
                trade_status = heepay_status_to_trade_status(notify_json['trade_status']),
                lastupdated_by = operatorObj,
                lastupdated_at = dt.datetime.utcnow()
            )

        if not updated and (purchase_trans.reference_order.order_source == 'API' or 
            purchase_trans.reference_order.reference_order.order_source == 'API'):
            raise ValueError('either purchase {0} or its matching sell order {1} did not update its api trans with heepay notification'.format(
                purchase_trans.reference_order.order_id, 
                purchase_trans.reference_order.reference_order.order_id
            ))

        if notify_json['trade_status'] != 'Success':
            update_purchase_transaction(purchase_trans, 
                notify_json['trade_status'],
                'heepay notify payment status {0}'.format(notify_json['trade_status']))
            return

        # get original buy order
        buyorder = Order.objects.select_for_update().get(
            pk = notify_json['out_trade_no'])
        buyorder.status = 'PAID'
        buyorder.lastupdated_by = operatorObj
        buyorder.save()

        # release lock at the last moment
        purchase_trans.payment_status = 'SUCCESS'
        # we still make status = 'PENDING'
        purchase_trans.lastupdated_by = operatorObj
        purchase_trans.save()

        return buyorder.order_id

def lock_paid_trans_of_purchase_order(order_id):
    try:
        return UserWalletTransaction.objects.select_for_update().get(
           reference_order__order_id = order_id, payment_status = 'SUCCESS',
           status='PENDING')
    except UserWalletTransaction.DoesNotExist:
        try:
            return UserWalletTransaction.objects.select_for_update().get(
              reference_order__order_id = order_id, payment_status = 'SUCCESS',
              status='PROCESSED')
        except UserWalletTransaction.DoesNotExist:
            try:
                return UserWalletTransaction.objects.select_for_update().get(
                reference_order__order_id = order_id, payment_status = 'UNKNOWN',
                status='PENDING')
            except UserWalletTransaction.DoesNotExist:
                raise ValueError('Somehow there\'s no payment success transaction record regarding purchase order {0}'.format(order_id))
            except UserWalletTransaction.MultipleObjectsReturned:
                raise ValueError('There should be no more than one PENDING UNKNOWN payment transaction for the purchase order {0}'.format(order_id))
        except UserWalletTransaction.MultipleObjectsReturned:
            raise ValueError('There should be no more than one PROCESSED successful payment transaction for the purchase order {0}'.format(order_id))
    except UserWalletTransaction.MultipleObjectsReturned:
        raise ValueError('There should be no more than one PENDING successful payment transaction for the purchase order {0}'.format(order_id))

def confirm_purchase_order(order_id, operator):
    logger.info('confirm_purchase_order({0})'.format(order_id))
    operatorObj = User.objects.get(username=operator)

    with transaction.atomic():
        #get the original purchase user_wallet_trans
        purchase_trans = lock_paid_trans_of_purchase_order(order_id)
        if purchase_trans.status == 'PROCESSED':
            logger.info("confirm_purchase_order(): The the payment transaction has been processed.  Nothing to do")
            return

        # get original buy order
        buyorder = Order.objects.select_for_update().get(pk=order_id)
        sell_order = Order.objects.select_for_update().get(
            pk = buyorder.reference_order.order_id)

        logger.info("confirm_purchase_order({0}): BEFORE updating, sell order is : {1}".format(
            order_id, sell_order_to_str(sell_order)
        ))

        logger.info("confirm_purchase_order({0}): BEFORE updating, purchase order is {1}{2} ({3}x@{4}) ".format(
            order_id, buyorder.total_amount, buyorder.unit_price_currency,
            buyorder.units, buyorder.unit_price
        ))

        seller_user_wallet = UserWallet.objects.select_for_update().get(
             user__id= sell_order.user.id,
             wallet__cryptocurrency = purchase_trans.user_wallet.wallet.cryptocurrency)
        sell_order_fulfill_comment = 'deliver on buyer order {0}, with {1} units on payment bill no {2}'.format(
             buyorder.order_id, buyorder.units, purchase_trans.payment_bill_no
        )

        seller_userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = seller_user_wallet,
          balance_begin = seller_user_wallet.balance,
          balance_end = seller_user_wallet.balance - buyorder.units,
          locked_balance_begin = seller_user_wallet.locked_balance,
          locked_balance_end = seller_user_wallet.locked_balance - buyorder.units,
          available_to_trade_begin = seller_user_wallet.available_balance,
          available_to_trade_end = seller_user_wallet.available_balance,
          reference_order = sell_order,
          reference_wallet_trxId = '',
          units = buyorder.units,
          fiat_money_amount = buyorder.total_amount,
          payment_provider = purchase_trans.payment_provider,
          payment_bill_no = purchase_trans.payment_bill_no,
          payment_status = 'SUCCESS',
          balance_update_type= 'DEBT',
          transaction_type = 'DELIVER ON PURCHASE',
          comment = sell_order_fulfill_comment,
          reported_timestamp = timegm(dt.datetime.utcnow().utctimetuple()),
          status = 'PROCESSED',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )

        seller_userwallet_trans.save()

        seller_user_wallet.balance = seller_userwallet_trans.balance_end
        seller_user_wallet.locked_balance = seller_userwallet_trans.locked_balance_end
        seller_user_wallet.available_balance = seller_userwallet_trans.available_to_trade_end
        seller_user_wallet.user_wallet_trans_id = seller_userwallet_trans.id
        seller_user_wallet.lastupdated_by = operatorObj
        seller_user_wallet.save()

        if round(sell_order.units_locked - buyorder.units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL) < 0:
            raise ValueError('confirm_purchase_order({0}): sell order locked units {1} is less than purchase order units {2}'.format(
                order_id, sell_order.units_locked, buyorder.units
            ))

        sell_order.units_locked = round(sell_order.units_locked - buyorder.units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL)
        sell_order.status = 'PARTIALFILLED'
        if sell_order.units_available_to_trade - MIN_CRYPTOCURRENCY_UNITS <= 0:
            sell_order.status == 'FILLED'
        sell_order.lastupdated_by = operatorObj
        sell_order.save()
        sell_order.refresh_from_db()
        logger.info("confirm_purchase_order({0}): AFTER update sell order: {1}".format(
            order_id, sell_order_to_str(sell_order)
        ))

        buyer_user_wallet = UserWallet.objects.select_for_update().get(
             user_id = buyorder.user.id,
             wallet__cryptocurrency = purchase_trans.user_wallet.wallet.cryptocurrency)

        new_payment_status = 'MANUALCONFIRMED' if purchase_trans.payment_status == 'UNKNOWN' else purchase_trans.payment_status
        purchase_trans.balance_begin = buyer_user_wallet.balance
        purchase_trans.balance_end = buyer_user_wallet.balance + buyorder.units
        purchase_trans.locked_balance_begin = buyer_user_wallet.locked_balance
        purchase_trans.locked_balance_end = buyer_user_wallet.locked_balance
        purchase_trans.available_to_trade_begin = buyer_user_wallet.available_balance
        purchase_trans.available_to_trade_end = buyer_user_wallet.available_balance + buyorder.units
        purchase_trans.payment_status = new_payment_status
        purchase_trans.status = 'PROCESSED'
        purchase_trans.lastupdated_by = operatorObj

        buyer_user_wallet.balance = purchase_trans.balance_end
        buyer_user_wallet.locked_balance = purchase_trans.locked_balance_end
        buyer_user_wallet.available_balance = purchase_trans.available_to_trade_end
        buyer_user_wallet.user_wallet_trans_id = buyer_user_wallet.id
        buyer_user_wallet.lastupdated_by = operatorObj
        buyer_user_wallet.save()

        buyorder.status = 'FILLED'
        buyorder.lastupdated_by = operatorObj
        buyorder.save()

        # release lock at the last moment
        purchase_trans.save()
        buyorder.refresh_from_db()
        logger.info("confirm_purchase_order({0}): AFTER update buyer order: {1}".format(
            order_id, sell_order_to_str(buyorder)
        ))

        if sell_order.order_source == 'API':
            api_trans = APIUserTransaction.objects.get(reference_order__order_id = sell_order.order_id) 
            if api_trans.trade_status != TRADE_STATUS_SUCCESS and api_trans.trade_status != TRADE_STATUS_PAYSUCCESS:
                api_trans.payment_status = PAYMENT_STATUS_SUCCESS
                api_trans.trade_status = TRADE_STATUS_PAYSUCCESS
                api_trans.save()
            api_trans.refresh_from_db()
            logger.info("'confirm_purchase_order({0}): sell order {1} update its api_trans {2}: trade_status: {3}, payment status: {4}".format(
                order_id, sell_order.order_id, api_trans.transactionId, api_trans.trade_status, api_trans.payment_status
            ))
            if api_trans.trade_status == TRADE_STATUS_PAYSUCCESS:
                APIUserTransactionManager.on_trans_paid_success(api_trans)
                api_trans.refresh_from_db()
                if api_trans.trade_status == TRADE_STATUS_SUCCESS:
                    APIUserTransactionManager.on_found_success_purchase_trans(api_trans)
            elif api_trans.trade_status in ['ExpiredInvald', 'UserAbandon', 'DevClose']:
                APIUserTransactionManager.on_trans_cancelled(api_trans)

        if buyorder.order_source =='API':
            api_trans = APIUserTransaction.objects.get(reference_order__order_id = buyorder.order_id)
            if api_trans.trade_status != TRADE_STATUS_SUCCESS and api_trans.trade_status != TRADE_STATUS_PAYSUCCESS:
                api_trans.payment_status = PAYMENT_STATUS_SUCCESS
                api_trans.trade_status = TRADE_STATUS_PAYSUCCESS
                api_trans.save()
            api_trans.refresh_from_db()
            logger.info("'confirm_purchase_order({0}): purchase order update its api_trans {1}: trade_status: {2}, payment status: {3}".format(
                order_id, api_trans.transactionId, api_trans.trade_status, api_trans.payment_status
            ))
            if api_trans.trade_status == TRADE_STATUS_PAYSUCCESS:
                APIUserTransactionManager.on_trans_paid_success(api_trans)
                api_trans.refresh_from_db()
                if api_trans.trade_status == TRADE_STATUS_SUCCESS:
                    APIUserTransactionManager.on_found_success_purchase_trans(api_trans)
            elif api_trans.trade_status in ['ExpiredInvald', 'UserAbandon', 'DevClose']:
                APIUserTransactionManager.on_trans_cancelled(api_trans)


def get_order_info(order_id):
    return Order.objects.get(pk=order_id)

def cancel_sell_order(userid, order_id, crypto, operator):
    operatorObj = User.objects.get(username=operator)
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        logger.info("select to cancel order {0}".format(order_id))
        if order.status == 'LOCKED' or order.status=='CANCELLED' or \
            Order.objects.filter(
            Q(reference_order__order_id = order.order_id),
            Q(order_type = 'BUY'),
            Q(status = 'OPEN') | Q(status = 'PAYING') | Q(status='PAID')).count() > 0:
            logger.error('order {0} has status {1} or has open buy orders. can\'t be cancelled anymore'.format(
               order_id, order.status
            ))
            raise ValueError("ORDER_USED_OR_LOCKED_CANCELLED")

        user_wallet = UserWallet.objects.select_for_update().get(
           user__id = order.user.id,
           wallet__cryptocurrency__currency_code = crypto
        )
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
          units = order.units_available_to_trade,
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

        order.status = 'CANCELLED'
        order.lastupdated_by = operatorObj
        order.save()

        user_wallet.locked_balance = locked_balance_end
        user_wallet.available_balance = available_to_trade_end
        user_wallet.lastupdated_by = operatorObj
        user_wallet.save()

# After creating buy order, our system will try to create purchase order in payment provider
# no matter whether that is doable, now call this routine to make sure that the buy order 
# enters PAYING state from OPEN.  At the same time it will unlock seller order, change its
# status from LOCKED to OPEN
def post_open_payment_order(buyorder_id, payment_provider, bill_no, payment_url, username):
    operator = User.objects.get(username=username)
    with transaction.atomic():
        purchase_trans = UserWalletTransaction.objects.select_for_update().get(
            reference_order__order_id = buyorder_id)
        if purchase_trans.status == 'FAILED':
            raise ValueError("Purchase user wallet transaction for purchase order {0} had failed before starting payment".format(buyorder_id))
        if purchase_trans.payment_status != 'UNKNOWN':
            raise ValueError("Purchase user wallet transaction for purchase order {0} had payemnt status {1} before starting payment".format(
                  buyorder_id, purchase_trans.payment_status))
        buyorder = Order.objects.select_for_update().get(pk=buyorder_id)
        if buyorder.status != 'OPEN':
            raise ValueError("Purchase order {0} should not become {1} before starting payment".format(
                buyorder_id, buyorder.status
            ))
        
        buyorder.comment = 'payment url to buyer: {0}'.format(payment_url)
        buyorder.status = 'PAYING'
        buyorder.save()

        # if the buy order comes from API call, update its api trans'
        # reference bill no
        if buyorder.order_source == 'API':
            updated = APIUserTransaction.objects.filter(
                    reference_order__order_id = buyorder.order_id
                ).update(
                    reference_bill_no = bill_no,
                    trade_status = TRADE_STATUS_INPROGRESS,
                    lastupdated_by = operator,
                    lastupdated_at = dt.datetime.utcnow()
                )
            if not updated:
                raise ValueError("Purchase order {0} should have api_trans associated".format(
                    buyorder_id
                ))

        # update sell order status
        updated = Order.objects.filter(
                   order_id=buyorder.reference_order.order_id,
                   status='LOCKED').update(status='OPEN',
                            lastupdated_by = operator,
                            lastupdated_at = dt.datetime.utcnow())
        if not updated:
            error_msg = "Sell order {0}:status{1} is not locked by buy order {2} anymore.  Should not happen.".format(
                    buyorder.reference_order.order_id,
                    buyorder.reference_order.status, buyorder.order_id)
            logger.error(error_msg)
            raise ValueError(error_msg)

        # if the buy order's matching sell order comes from API call, 
        # update its api trans' reference bill no
        if buyorder.reference_order.order_source == 'API':
            updated = APIUserTransaction.objects.filter(
                    reference_order__order_id = buyorder.reference_order.order_id
                ).update(
                    reference_bill_no = bill_no,
                    trade_status = TRADE_STATUS_INPROGRESS,
                    lastupdated_by = operator,
                    lastupdated_at = dt.datetime.utcnow()
                )
            if not updated:
                raise ValueError("Purchase order {0}'s sell order {1} should have api_trans associated".format(
                    buyorder_id, buyorder.reference_order.order_id
                ))

        logger.info("post_open_payment_order(): update related status of sell order {0} (of purchase order {1}) to OPEN".format(
            buyorder.reference_order.order_id, buyorder_id))

        purchase_trans.payment_bill_no = bill_no
        purchase_trans.save()
        logger.info("post_open_payment_order(): record {0}.bill#: [{1}] to related buyorder: {2}".format(
           payment_provider, bill_no, buyorder.order_id
        ))

def get_user_transactions(userid, crypto):
    return UserWalletTransaction.objects.filter(user_wallet__user__id= userid,
        user_wallet__wallet__cryptocurrency__currency_code = crypto, status='PROCESSED').order_by('-lastupdated_at')

def get_order_transactions(orderid):
    return UserWalletTransaction.objects.get(reference_order__order_id = orderid)

# assume the api_tran is a purchase API call, parse buyer info out of it
def parse_buyer_info_from_apitran(api_tran):
    username = nickname = sitename = ''
    if api_tran.attach :
        parts = api_tran.attach.split(';')
        for part in parts:
            subparts = part.split('=')
            if len(subparts) == 2:
                if subparts[0].strip() == 'username':
                    username = subparts[1].strip()
                elif subparts[0].strip() == 'weixin':
                    nickname = subparts[1].strip()
    if len(username) == 0 and len(nickname) == 0:
        username = api_tran.attach if api_tran.attach else '未知'
    if api_tran.api_user.user.username.startswith('stakinguser1'):
        sitename = '投资网站'
    return username, nickname, sitename    

# assume the api_tran is a purchase API call, parse seller info out of it
def parse_seller_info_from_apitran(api_tran):
    username = nickname = sitename = ''
    order = api_tran.reference_order.reference_order
    if order.order_source == 'TRADESITE':
        username = order.user.username
        nickname = order.seller_payment_method.account_alias if order.seller_payment_method else '未知'
        sitename = '场外交易'
    elif order.order_source == 'API':
        purchase_tran = APIUserTransaction.objects.get(reference_order__order_id=order.order_id)
        return parse_buyer_info_from_apitran(purchase_tran)
    return username, nickname, sitename    

# assume the order is a buy order, parse buyer info out of it
def parse_buyer_info_from_order(order):
    return order.user.username, order.seller_payment_method.account_alias if order.seller_payment_method else '未知','场外交易'

# assume the order is a buy order, parse seller info out of it
def parse_seller_info_from_order(buyorder):
    order = buyorder.reference_order
    if order.order_source == 'TRADESITE':
        username = order.user.username
        nickname = order.seller_payment_method.account_alias if order.seller_payment_method else '未知'
        sitename = '场外交易'
    elif order.order_source == 'API':
        purchase_tran = APIUserTransaction.objects.get(reference_order__order_id=order.order_id)
        return parse_buyer_info_from_apitran(purchase_tran)
    return username, nickname, sitename    


def search_orders(keyword, from_date, to_date):
    buyer_orders = []
    apiTrans = APIUserTransaction.objects.filter(
        Q(action=API_METHOD_PURCHASE),
        Q(trade_status=TRADE_STATUS_NOTSTARTED) | Q(trade_status=TRADE_STATUS_UNKNOWN) |
        Q(trade_status=TRADE_STATUS_INPROGRESS),
        Q(attach__contains=keyword)).order_by('-lastupdated_at')

    for api_tran in apiTrans:
        order = api_tran.reference_order
        buyer_username, buyer_weixin_nickname, buyer_site = parse_buyer_info_from_apitran(api_tran)
        seller_username, seller_weixin_nickname, seller_site = parse_seller_info_from_apitran(api_tran)
        trans_item = OrderTransactionItem(
            order.order_id,
            buyer_username,
            buyer_weixin_nickname,
            buyer_site,
            seller_username,
            seller_weixin_nickname,
            seller_site,
            order.order_source,
            order.units,
            order.total_amount,
            order.unit_price,
            order.unit_price_currency,
            order.status,
            order.created_at,
            order.lastupdated_at
        )

        buyer_orders.append(trans_item)

    buyorder_exchanges = Order.objects.filter(
        Q(order_type= 'BUY'),
        Q(order_source = 'TRADESITE'),
        Q(status = 'OPEN') | Q(status = 'PAYING'),
        Q(user__username__contains=keyword)
    ).order_by('-lastupdated_at')
    for buyorder in buyorder_exchanges:
        buyer_username, buyer_weixin_nickname, buyer_site = parse_buyer_info_from_order(buyorder)
        seller_username, seller_weixin_nickname, seller_site = parse_seller_info_from_order(buyorder)
        trans_item = OrderTransactionItem(
            buyorder.order_id,
            buyer_username,
            buyer_weixin_nickname,
            buyer_site,
            seller_username,
            seller_weixin_nickname,
            seller_site,
            buyorder.order_source,
            buyorder.units,
            buyorder.total_amount,
            buyorder.unit_price,
            buyorder.unit_price_currency,
            buyorder.status,
            buyorder.created_at,
            buyorder.lastupdated_at
        )
        buyer_orders.append(trans_item)

    return buyer_orders