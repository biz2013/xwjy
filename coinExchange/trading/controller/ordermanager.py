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
from tradeex.models import *
from tradeex.utils import *
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
from trading.models import *
from trading.controller.global_constants import *
from trading.views.models.orderitem import OrderItem
from trading.views.models.userpaymentmethodview import *

logger = logging.getLogger("site.ordermanager")

def get_user_payment_account(user_id, payment_provider_code):
    return UserPaymentMethod.objects.filter(user__id=user_id).filter(provider__code=payment_provider_code)

def get_seller_buyer_payment_accounts(buyorder_id, payment_provider):
    buyorder = Order.objects.get(pk=buyorder_id)
    sellorder = Order.objects.get(pk=buyorder.reference_order.order_id)
    seller_payment_method = UserPaymentMethod.objects.get(user__id=sellorder.user.id, provider__code = payment_provider)
    buyer_payment_method = UserPaymentMethod.objects.get(user__id=buyorder.user.id, provider__code = payment_provider)
    return seller_payment_method.account_at_provider, buyer_payment_method.account_at_provider

def create_sell_order(order, operator, api_user = None,  api_redeem_request = None,
         api_trans_id = None):
    userobj = User.objects.get(id = order.owner_user_id)
    operatorObj = User.objects.get(username = operator)
    crypto = Cryptocurrency.objects.get(currency_code = order.crypto)
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
                    action = api_redeem_request.method,
                    client_ip = api_redeem_request.client_ip,
                    subject = api_redeem_request.subject,
                    total_fee = api_redeem_request.total_fee,
                    attach = api_redeem_request.attach,
                    request_timestamp = api_redeem_request.timestamp,
                    original_request = api_redeem_request.original_json_request,
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
            total_fee_in_units = round(float(api_redeem_request.total_fee)/100.0,8)
            if user_cny_wallet.available_balance < total_fee_in_units :
                logger.error("user {0} does not have enough CNY in wallet: available {1} to be sold {2}".format(
                userobj.username, user_cny_wallet.available_balance, total_fee_in_units 
                ))
                api_trans.trade_status = 'NOTSTARTED'
                api_trans.payment_status = 'NOTSTARTED'
                # return transId but none orderId meaning there is no enough fund in the cny wallet
                api_trans.save()
                return None
            user_cny_wallet.available_balance = user_cny_wallet.available_balance - total_fee_in_units
            user_cny_wallet.locked_balance = user_cny_wallet.locked_balance + total_fee_in_units
            user_cny_wallet.save()
        userwallet = UserWallet.objects.select_for_update().get(
                user__id=order.owner_user_id,
                wallet__cryptocurrency = crypto)
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
           selected_payment_provider = PaymentProvider.objects.get(pk=order.selected_payment_provider) if order.selected_payment_provider else None,
           account_at_selected_payment_provider = order.account_at_payment_provider,
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
            api_trans.payment_status = 'NOTSTARTED'
            api_trans.trade_status = 'INPROGRESS'
            api_trans.save()
         
        userwallet.locked_balance = userwallet.locked_balance + order.total_units
        userwallet.available_balance = userwallet.available_balance - order.total_units
        userwallet.save()
        logger.info('create_sell_order(): Created {5} sell order {0}, units {1} user\'s wallet: balance:{2} available_balance:{3} locked_balance: {4} {5}'.format(
           orderRecord.order_id, orderRecord.units, userwallet.balance, userwallet.available_balance, 
           userwallet.locked_balance, order.order_source,
           'reference by api trans {0}'.format(api_trans.transactionId) if api_trans else ''
        ))
        return orderRecord.order_id

def cancel_purchase_order(order, final_status, payment_status,
                         operator):
    operatorObj = User.objects.get(username = operator)
    with transaction.atomic():

        sell_order = Order.objects.select_for_update().get(pk=order.reference_order.order_id)
        sell_order.units_locked = sell_order.units_locked - order.units
        sell_order.units_available_to_trade = sell_order.units_available_to_trade + order.units
        sell_order.status = 'OPEN'
        sell_order.lastupdated_by = operatorObj

        updated = UserWalletTransaction.objects.filter(
               reference_order__order_id= order.order_id,
               status = 'PENDING').update(
               status = final_status,
               payment_status = payment_status,
               lastupdated_by = operatorObj,
               lastupdated_at = dt.datetime.utcnow()
        )
        if not updated:
            logger.error("cancel_purchase_order(): order {0} does not have PENDING userwallettrans to be updated".format(order_id))

        updated = Order.objects.filter(
           Q(status = 'PAYING')|Q(status='OPEN'), Q(order_id = order.order_id)).update(
           status = final_status,
           lastupdated_by = operatorObj,
           lastupdated_at = dt.datetime.utcnow()
        )
        if not updated:
            logger.error("cancel_purchase_order(): did not find order {0} to update, maybe someone changed its status from PAYING already".format(order_id))
        
        api_trans = APIUserTransactionManager.get_trans_by_reference_order(order.order_id)
        if not api_trans:
            api_trans = APIUserTransactionManager.get_trans_by_reference_order(sell_order.order_id)
        if api_trans:
            api_trans.payment_status = payment_status
            if final_status == 'CANCELLED' and payment_status == 'UNKNOWN':
                api_trans.trade_status = 'ExpiredInvalid'
            else:
                timediff = timezone.now() - api_trans.created_at
                if timediff > api_trans.timeout_in_sec:
                    api_trans.trade_status = 'ExpiredInvalid'
                else:
                    api_trans.trade_status = 'UserAbandon'
            api_trans.save()

        # release lock
        sell_order.save()

def get_all_open_seller_order_exclude_user(user_id):
    sell_orders = Order.objects.filter(order_type='SELL').exclude(user__id=user_id).exclude(status='CANCELLED').exclude(status='FILLED').order_by('unit_price','-lastupdated_at')
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
                                selected_payment_provider=order.selected_payment_provider,
                                account_at_payment_provider=order.account_at_selected_payment_provider))
    return orders

def get_sell_transactions_by_user(userid):
    sell_orders = Order.objects.filter(Q(order_type='SELL'),
            Q(user__id=userid),
            Q(status='OPEN') | Q(status='PARTIALFILLED') | Q(status='LOCKED')).order_by('-lastupdated_at')
    buyorders = Order.objects.filter(Q(order_type='BUY'),
        Q(reference_order__user__id=userid),
        Q(status='PAYING')| Q(status='PAID')).order_by('-lastupdated_at')
    order_lookup = {}
    for order in sell_orders:
        order_lookup[order.order_id] = []
        order_item = OrderItem(order.order_id, order.user.id, order.user.username,
                                order.unit_price, order.unit_price_currency,
                                order.units, order.units_available_to_trade,
                                order.total_amount,
                                order.cryptocurrency.currency_code,
                                order.lastupdated_at, order.status, order.order_type)
        order_lookup[order.order_id].append(order_item)

    for order in buyorders:
        if order.reference_order.order_id in order_lookup:
            order_lookup[order.reference_order.order_id].append(OrderItem(order.order_id, order.user.id, order.user.username,
                                    order.unit_price, order.unit_price_currency,
                                    order.units, order.units_available_to_trade,
                                    order.total_amount,
                                    order.cryptocurrency.currency_code,
                                    order.lastupdated_at, order.status, order.order_type))
        else:
            logger.error('Could not find purchase order {0}\'s sell order {1} in user {2}\'s sell order list'.format(
               order.order_id, order.reference_order.order_id, userid
            ))
    order_list = []
    for order in sell_orders:
        for entry in order_lookup[order.order_id]:
            order_list.append(entry)

    return order_list

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

def create_purchase_order(buyorder, reference_order_id,
         seller_payment_provider, operator, 
         api_user = None,  api_purchase_request = None,
         api_trans_id = None):

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
        if reference_order.status != 'PARTIALFILLED' and reference_order.status != 'OPEN':
            logger.error('create_purchase_order(): reference_order {0} with status {1}: raise SELLORDER_NOT_OPEN'.format(reference_order_id, reference_order.status))
            raise ValueError('SELLORDER_NOT_OPEN')
        if buyorder.total_units > reference_order.units_available_to_trade:
            logger.error('sell order %s has %f to trade, buyer buy %f units' % (
                      reference_order.order_id,
                      reference_order.units_available_to_trade,
                      buyorder.total_units))
            raise ValueError('BUY_EXCEED_AVAILABLE_UNITS')

        # if the target sell order is requires all or nothing then we have to 
        # make sure the difference between purchase amount and is the same
        if reference_order.order_type == 'ALL_OR_NOTHING':
            if reference_order.total_units != reference_order.units_available_to_trade:
                logger.error('ALL_OR_NOTHING sell order %s\'s total unit(%f) and available units(%f) does not match' % (
                    reference_order.order_id, reference_order.total_units,
                    reference_order.units_available_to_trade
                ))
                raise ValueError('ALL_OR_NOTHING_ORDER_INVALID_TOTAL_UNITS')
            if reference_order.units_available_to_trade -  buyorder.total_units > 0.00000001:
                logger.error('Purchase amount %f does not match ALL_OR_NOTHING sell order %s\'s total unit(%f)' % (
                    buyorder.total_units, reference_order.order_id, reference_order.total_units
                ))
                raise ValueError('ALL_OR_NOTHING_ORDER_PURCHASE_AMOUNT_NOT_ENOUGH')

        logger.info('before creating purchase order {0}, userwallet {1} has balance:{2} available_balance:{3} locked_balance: {4}'.format(
           frmt_date, userwallet.id, userwallet.balance, userwallet.available_balance, userwallet.locked_balance
        ))

        selected_payment_provider = None
        try:
            selected_payment_provider = PaymentProvider.objects.get(pk=seller_payment_provider)
        except:
            logger.error('create_purchase_order(): failed to find payment provider record with code {0}'.format(
                seller_payment_provider
            ))
        order = Order.objects.create(
            order_id = buyorder.order_id,
            user= User.objects.get(pk=buyorder.owner_user_id),
            selected_payment_provider = selected_payment_provider,
            created_by = operatorObj,
            lastupdated_by = operatorObj,
            reference_order= reference_order,
            cryptocurrency= crypto_currency,
            order_type='BUY',
            sub_type='BUY_ON_ASK' if not is_api_call else 'ALL_ALL_NOTHING',
            order_source = 'TRADESITE' if not is_api_call else 'API',
            units = buyorder.total_units,
            unit_price = buyorder.unit_price,
            unit_price_currency = buyorder.unit_price_currency,
            total_amount = buyorder.total_amount,
            status = 'OPEN',
            api_call_reference_order_id = api_call_order_id if is_api_call else None)
        logger.info("purchase order {0} created".format(order.order_id))
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
        logger.info('userwallet transaction {0} for purchase order {1} userwallet{2} created'.format(
            userwallet_trans.id, order.order_id, userwallet.id
        ))

        if is_api_call:
            api_trans = APIUserTransaction.objects.create(
                transactionId = api_trans_id,
                api_out_trade_no = api_purchase_request.out_trade_no,
                api_user = api_user,
                payment_provider = PaymentProvider.objects.get(pk= api_purchase_request.payment_provider),
                reference_order = order,
                payment_account = api_purchase_request.payment_account,
                action = api_purchase_request.method,
                client_ip = api_purchase_request.client_ip,
                subject = api_purchase_request.subject,
                total_fee = api_purchase_request.total_fee,
                attach = api_purchase_request.attach,
                request_timestamp = api_purchase_request.timestamp,
                original_request = api_purchase_request.original_json_request,
                payment_provider_last_notify = '',
                payment_provider_last_notified_at = None,
                notify_url = api_purchase_request.notify_url,
                return_url = api_purchase_request.return_url,
                expire_in_sec=api_purchase_request.expire_minute * 60,
                created_by = operatorObj,
                lastupdated_by= operatorObj
            )

            api_trans.save()

        reference_order.status = 'LOCKED'
        reference_order.units_locked = reference_order.units_locked + buyorder.total_units
        reference_order.units_available_to_trade = reference_order.units_available_to_trade - buyorder.total_units
        reference_order.save()
        logger.info('Created purchase order {0}: units:{1} sell order {2} available_units:{3} locked_units: {4} original units: {5}'.format(
           order.order_id, order.units, reference_order.order_id,
           reference_order.units_available_to_trade,
           reference_order.units_locked,
           reference_order.units
        ))

    return order.order_id if order is not None else None

def lock_trans_of_purchase_order(orderid, bill_no):
    try:
        # TODO: is this needed?
        purchase_trans = UserWalletTransaction.objects.select_for_update().get(
              reference_order__order_id=orderid)
        logger.info("--- trans: orderid {0}, pay bill: {1} status {2} trans_type {3} inside call of {4},{5}".format(
              orderid, purchase_trans.payment_bill_no, purchase_trans.status,
              purchase_trans.transaction_type, orderid, bill_no
        ))
        return UserWalletTransaction.objects.select_for_update().get(
              reference_order__order_id=orderid,
              payment_bill_no = bill_no,
              status='PENDING',
              transaction_type='OPEN BUY ORDER')
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

def update_purchase_transaction(purchase_trans, trade_status, trade_msg):
    normal_status = {'Not Started': 'NOTSTARTED','PaySuccess':'PAYSUCCESS',
         'Starting':'STARTING', 'Unknown':'UNKNOWN'
         }
    bad_status = { 'ExpiredInvalid': 'EXPIREDINVALID',
         'UserAbandon':'USERABANDON', 'DevClose':'DEVCLOSE',
         'Failure':'FAILURE'}
    if trade_status in normal_status:
        purchase_trans.payment_methodstatus = normal_status[trade_status]
    elif trade_status in bad_status:
        purchase_trans.payment_status = bad_status[trade_status]
        purchase_trans.comment = trade_msg
        buyorder = purchase_trans.reference_order
        buyorder.status = 'FAILED'
        #revert locked unit and available units in sell order
        Order.objects.filter(pk = buyorder.reference_order.order_id).update(
             units_locked = F('units_locked') - buyorder.units,
             units_available_to_trade = F('units_available_to_trade') + buyorder.units,
             lastupdated_at = dt.datetime.utcnow())
        buyorder.save()
        purchase_trans.status = 'PROCESSED'
    purchase_trans.save()

def get_order_associated_api_trans(buy_order_id):
    order = Order.objects.get(order_id = buy_order_id)
    if order.order_type != 'BUY':
        raise ValueError('UNEXPECTED_BUY_ORDER')
    
    api_order_id = None
    if order.order_source == 'API':
        api_order_id = order.order_id
    elif order.reference_order.order_source == 'API':
        api_order_id = order.reference_order.order_id
    else:
        return None

    try:
        return APIUserTransaction.objects.get(reference_order__order_id= api_order_id)
    except APIUserTransaction.DoesNotExist:
        logger.error('get_sell_order_associated_api_trans(): buyorder {0} or its sell order {1}\'s associated api transaction could not be found'.format(
            buy_order_id, order.reference_order.order_id
        ))
        raise ValueError('API_TRANS_SHOULD_HAVE_EXISTED')
    except APIUserTransaction.MultipleObjectsReturned:
        logger.error('get_sell_order_associated_api_trans(): buyorder {0} or its sell order {1} has more than one associated api transaction'.format(
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
        purchase_trans.lastupdated_by = operatorObj
        purchase_trans.save()


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
             raise ValueError('Somehow there\'s no payment success transaction record regarding purchase order {0}'.format(order_id))
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

        seller_user_wallet = UserWallet.objects.select_for_update().get(
             user__id= sell_order.user.id,
             wallet__cryptocurrency = purchase_trans.user_wallet.wallet.cryptocurrency)
        buyer_user_wallet = UserWallet.objects.select_for_update().get(
             user_id = buyorder.user.id,
             wallet__cryptocurrency = purchase_trans.user_wallet.wallet.cryptocurrency)
        sell_order_fulfill_comment = 'deliver on buyer order {0}, with {1} units on payment bill no {2}'.format(
             buyorder.order_id, buyorder.units, purchase_trans.payment_bill_no
        )

        api_trans = None
        if buyorder.order_source =='API':
            api_trans = APIUserTransaction.objects.get(reference_order__order_id = buyorder.order_id)
        elif sell_order.order_source == 'API':
            api_trans = APIUserTransaction.objects.get(reference_order__order_id = sell_order.order_id) 
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
        purchase_trans.balance_begin = buyer_user_wallet.balance
        purchase_trans.balance_end = buyer_user_wallet.balance + buyorder.units
        purchase_trans.locked_balance_begin = buyer_user_wallet.locked_balance
        purchase_trans.locked_balance_end = buyer_user_wallet.locked_balance
        purchase_trans.available_to_trade_begin = buyer_user_wallet.available_balance
        purchase_trans.available_to_trade_end = buyer_user_wallet.available_balance + buyorder.units
        purchase_trans.status = 'PROCESSED'
        purchase_trans.lastupdated_by = operatorObj

        sell_order.units_locked = sell_order.units_locked - buyorder.units
        sell_order.status = 'PARTIALFILLED'
        if sell_order.units_available_to_trade < 0.00000001:
            sell_order.status == 'FILLED'
        sell_order.lastupdated_by = operatorObj
        sell_order.save()

        buyorder.status = 'FILLED'
        buyorder.lastupdated_by = operatorObj
        buyorder.save()

        buyer_user_wallet.balance = purchase_trans.balance_end
        buyer_user_wallet.locked_balance = purchase_trans.locked_balance_end
        buyer_user_wallet.available_balance = purchase_trans.available_to_trade_end
        buyer_user_wallet.user_wallet_trans_id = buyer_user_wallet.id
        buyer_user_wallet.lastupdated_by = operatorObj
        buyer_user_wallet.save()

        seller_user_wallet.balance = seller_userwallet_trans.balance_end
        seller_user_wallet.locked_balance = seller_userwallet_trans.locked_balance_end
        seller_user_wallet.available_balance = seller_userwallet_trans.available_to_trade_end
        seller_user_wallet.user_wallet_trans_id = seller_userwallet_trans.id
        seller_user_wallet.lastupdated_by = operatorObj
        seller_user_wallet.save()

        if api_trans:
            if api_trans.trade_status != 'Success' and api_trans.trade_status != 'PaidSuccess':
                api_trans.payment_status = 'Success'
                api_trans.trade_status = 'PaidSuccess'
                api_trans.save()

        # release lock at the last moment
        purchase_trans.save()

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

def post_open_payment_order(buyorder_id, payment_provider, bill_no, hy_url, username):
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
        
        buyorder.comment = 'hy_url: {0}'.format(hy_url)
        buyorder.status = 'PAYING'
        buyorder.save()

        # if the buy order comes from API call, update its api trans'
        # reference bill no
        if buyorder.order_source == 'API':
            updated = APIUserTransaction.objects.filter(
                    reference_order__order_id = buyorder.order_id
                ).update(
                    reference_bill_no = bill_no,
                    trade_status = 'InProgress',
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
                    trade_status = 'InProgress',
                    lastupdated_by = operator,
                    lastupdated_at = dt.datetime.utcnow()
                )
            if not updated:
                raise ValueError("Purchase order {0}'s sell order {1} should have api_trans associated".format(
                    buyorder_id, buyerorder.reference_order.order_id
                ))

        logger.info("post_open_payment_order(): update related status of sell order {0} (of purchase order {1}) to OPEN".format(
            buyorder.reference_order.order_id, buyorder_id))

        purchase_trans.payment_bill_no = bill_no
        purchase_trans.save()
        logger.info("post_open_payment_order(): record {0}.bill#: {1} to related buyorder: {2}".format(
           payment_provider, bill_no, buyorder.order_id
        ))

def get_user_transactions(userid, crypto):
    return UserWalletTransaction.objects.filter(user_wallet__user__id= userid,
        user_wallet__wallet__cryptocurrency__currency_code = crypto, status='PROCESSED').order_by('-lastupdated_at')

def get_order_transactions(orderid):
    return UserWalletTransaction.objects.get(reference_order__order_id = orderid)
