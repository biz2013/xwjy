#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, logging, json, traceback
import datetime as dt
import time

from calendar import timegm
from django.db import transaction
from django.utils import timezone

from tradeex.client.apiclient import APIClient
from tradeex.controllers.apiusermanager import APIUserManager
from tradeex.controllers.walletmanager import WalletManager
from trading.controller.coin_utils import *
from tradeex.data.api_const import *
from tradeex.models import APIUserTransaction
from trading.models import User, UserWallet, UserWalletTransaction, CNYFUND_CRYPTO_CODE, PaymentProvider
from tradeex.data.purchase_notify import PurchaseAPINotify
from tradeex.utils import *

logger = logging.getLogger("tradeex.apiusertransmanager")

class APIUserTransactionManager(object):
    @staticmethod
    def get_transaction_by_id(transId):
        try:
            return APIUserTransaction.objects.get(transactionId=transId)           
        except APIUserTransaction.DoesNotExist:
            logger.warn("get_transaction_by_id: Failed to find APIUserTransaction for transId {0}".format(transId))
            return None
        except APIUserTransaction.MultipleObjectsReturned:
            logger.error("get_transaction_by_id: Find mutiple APIUserTransaction for transId order {0}".format(transId))
            raise ValueError('MORE_THAN_ONE_APIUSERTRANSACT')
        
    @staticmethod
    def get_trans_by_reference_order(orderId):
        try:
            return APIUserTransaction.objects.get(reference_order__order_id=orderId)           
        except APIUserTransaction.DoesNotExist:
            logger.warn("get_trans_by_reference_order: Failed to find APIUserTransaction for reference order {0}".format(orderId))
            return None
        except APIUserTransaction.MultipleObjectsReturned:
            logger.error("get_trans_by_reference_order: Find mutiple APIUserTransaction for reference order {0}".format(orderId))
            raise ValueError('MORE_THAN_ONE_APIUSERTRANSACT')
    
    @staticmethod
    def get_pending_redeems():
        return APIUserTransaction.objects.filter(reference_order__isnull = True, action = 'wallet.trade.sell')
        
    @staticmethod
    def update_notification_status(trx_id, notify, notify_resp, comment):
        try:
            logger.info('update_notification_status({0}, ..., response {1}, comment {2}'.format(
                trx_id, notify_resp, comment
            ))
            last_notify_response = 'OK' if notify_resp.upper() == 'OK' else 'ERROR'
                
            if not APIUserTransaction.objects.filter(
               transactionId= trx_id).update(
               last_notify = notify,
               last_notify_response = last_notify_response,
               last_notified_at = dt.datetime.utcnow(),
               last_status_description = comment,
               lastupdated_by = User.objects.get(username='admin'),
               lastupdated_at = dt.datetime.utcnow()):
               logger.error("update_notification_status({0}, ..., {1}, {2}: did not update".format(trx_id, notify_resp, comment))
        except:
            logger.error("update_notification_status: Hit exception {0}".format(sys.exc_info()))
                    
    @staticmethod
    def update_status_info(trx_id, comment):
        try:
            if not APIUserTransaction.objects.filter(
               transactionId= trx_id).update(
               last_status_description = comment,
               lastupdated_by = User.objects.get(username='admin'),
               lastupdated_at = dt.datetime.utcnow()):
               logger.error("update_status_info({0}, {1}): did not update".format(trx_id, comment))
        except:
            logger.error("update_status_info({0}, {1}): Hit exception {2}".format(trx_id, comment,sys.exc_info()))
    
    @staticmethod
    def abandon_trans(api_trans):
        with transaction.atomic():
            api_trans = APIUserTransactionManager.objects.select_for_update().get(pk=api_trans.transactionId)
            api_trans.trade_status = TRADE_STATUS_USERABANDON
            api_trans.save()
        
    @staticmethod
    def on_trans_paid_success(api_trans):
        logger.debug('on_trans_paid_success()')
        operatorObj = User.objects.get(username='admin')
        total_cny_in_units = round(float(api_trans.total_fee)/100.0,8)
        with transaction.atomic():
            api_trans = APIUserTransaction.objects.select_for_update().get(pk=api_trans.transactionId)
            if api_trans.trade_status == TRADE_STATUS_SUCCESS:
                logger.info("on_trans_paid_success(): api trans {0} is already done.  Nothing to do")
                return True

            user_cny_wallet = UserWallet.objects.select_for_update().get(
                user__id = api_trans.api_user.user.id, 
                wallet__cryptocurrency__currency_code ='CNY')
            master_wallet = UserWallet.objects.select_for_update().get(
                user__id = 1,
                wallet__cryptocurrency__currency_code='CNY')
            if api_trans.action == API_METHOD_REDEEM:
                if round(user_cny_wallet.locked_balance - total_cny_in_units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL) < 0:
                    logger.error("INCONSISTENCY!!![out_trade_no: {0}] user {1} does not have enough locked CNY in wallet: locked {2} to be released {3}. ".format(
                        api_trans.api_out_trade_no,
                        api_trans.api_user.user.username, user_cny_wallet.locked_balance, total_cny_in_units 
                    ))
                    return

                logger.info('on_trans_paid_success(): create trans pass CNY from seller to master wallet')
                end_cny_balance = round(user_cny_wallet.balance - total_cny_in_units, MIN_CRYPTOCURRENCY_UNITS_DECIMAL)
                end_cny_available_balance = user_cny_wallet.available_balance
                end_cny_locked_balance = max(0, round(user_cny_wallet.locked_balance - total_cny_in_units,MIN_CRYPTOCURRENCY_UNITS_DECIMAL))

                operation_comment = 'user {0} redeem {1} CNY'.format(api_trans.api_user.user.username, total_cny_in_units)
                user_cny_wallet_trans = UserWalletTransaction.objects.create(
                    user_wallet = user_cny_wallet,
                    reference_order = api_trans.reference_order,
                    reference_wallet_trxId = '',
                    units = total_cny_in_units,
                    balance_begin = user_cny_wallet.balance,
                    balance_end = end_cny_balance,
                    locked_balance_begin = user_cny_wallet.locked_balance,
                    locked_balance_end = end_cny_locked_balance,
                    available_to_trade_begin = user_cny_wallet.available_balance,
                    available_to_trade_end = end_cny_available_balance,
                    fiat_money_amount = total_cny_in_units,
                    payment_provider = api_trans.payment_provider,
                    balance_update_type= 'DBET',
                    transaction_type = 'OPEN SELL ORDER',
                    comment = operation_comment,
                    reported_timestamp = timegm(dt.datetime.utcnow().utctimetuple()),
                    status = 'PROCESSED',
                    created_by = operatorObj,
                    lastupdated_by = operatorObj
                )
                user_cny_wallet_trans.save()

                user_cny_wallet.balance = end_cny_balance
                user_cny_wallet.locked_balance = end_cny_locked_balance
                user_cny_wallet.save()

                end_master_balance = master_wallet.balance + total_cny_in_units
                end_master_available_balance = master_wallet.available_balance + total_cny_in_units
                end_master_locked_balance = master_wallet.locked_balance
                master_wallet_trans = UserWalletTransaction.objects.create(
                    user_wallet = master_wallet,
                    reference_order = api_trans.reference_order,
                    reference_wallet_trxId = '',
                    units = total_cny_in_units,
                    balance_begin = master_wallet.balance,
                    balance_end = end_master_balance,
                    locked_balance_begin = master_wallet.locked_balance,
                    locked_balance_end = end_master_locked_balance,
                    available_to_trade_begin = master_wallet.available_balance,
                    available_to_trade_end = end_master_available_balance,
                    fiat_money_amount = total_cny_in_units,
                    payment_provider = api_trans.payment_provider,
                    balance_update_type= 'CEDIT',
                    transaction_type = 'OPEN SELL ORDER',
                    comment = operation_comment,
                    reported_timestamp = timegm(dt.datetime.utcnow().utctimetuple()),
                    status = 'PROCESSED',
                    created_by = operatorObj,
                    lastupdated_by = operatorObj
                )
                master_wallet_trans.save()

                master_wallet.available_balance = end_master_available_balance
                master_wallet.balance = end_master_balance   
                master_wallet.save()
            elif api_trans.action == API_METHOD_PURCHASE:
                logger.info('on_trans_paid_success(): create trans pass CNY from master wallet to seller')
                end_cny_balance = user_cny_wallet.balance + total_cny_in_units
                end_cny_available_balance = user_cny_wallet.available_balance + total_cny_in_units
                end_cny_locked_balance = user_cny_wallet.locked_balance

                operation_comment = 'user {0} purchase {1} CNY'.format(api_trans.api_user.user.username, total_cny_in_units)
                user_cny_wallet_trans = UserWalletTransaction.objects.create(
                    user_wallet = user_cny_wallet,
                    reference_order = api_trans.reference_order,
                    reference_wallet_trxId = '',
                    units = total_cny_in_units,
                    balance_begin = user_cny_wallet.balance,
                    balance_end = end_cny_balance,
                    locked_balance_begin = user_cny_wallet.locked_balance,
                    locked_balance_end = end_cny_locked_balance,
                    available_to_trade_begin = user_cny_wallet.available_balance,
                    available_to_trade_end = end_cny_available_balance,
                    fiat_money_amount = total_cny_in_units,
                    payment_provider = api_trans.payment_provider,
                    balance_update_type= 'CEDIT',
                    transaction_type = 'OPEN BUY ORDER',
                    comment = operation_comment,
                    reported_timestamp = timegm(dt.datetime.utcnow().utctimetuple()),
                    status = 'PROCESSED',
                    created_by = operatorObj,
                    lastupdated_by = operatorObj
                )
                user_cny_wallet_trans.save()

                user_cny_wallet.balance = end_cny_balance
                user_cny_wallet.available_balance = end_cny_available_balance
                user_cny_wallet.locked_balance = end_cny_locked_balance
                user_cny_wallet.save()

                end_master_balance = master_wallet.balance - total_cny_in_units
                end_master_available_balance = master_wallet.available_balance - total_cny_in_units
                end_master_locked_balance = master_wallet.locked_balance
                master_wallet_trans = UserWalletTransaction.objects.create(
                    user_wallet = master_wallet,
                    reference_order = api_trans.reference_order,
                    reference_wallet_trxId = '',
                    units = total_cny_in_units,
                    balance_begin = master_wallet.balance,
                    balance_end = end_master_balance,
                    locked_balance_begin = master_wallet.locked_balance,
                    locked_balance_end = end_master_locked_balance,
                    available_to_trade_begin = master_wallet.available_balance,
                    available_to_trade_end = end_master_available_balance,
                    fiat_money_amount = total_cny_in_units,
                    payment_provider = api_trans.payment_provider,
                    balance_update_type= 'DEBT',
                    transaction_type = 'DELIVER ON PURCHASE',
                    comment = operation_comment,
                    reported_timestamp = timegm(dt.datetime.utcnow().utctimetuple()),
                    status = 'PROCESSED',
                    created_by = operatorObj,
                    lastupdated_by = operatorObj
                )
                master_wallet_trans.save()


                master_wallet.available_balance = end_master_available_balance
                master_wallet.balance = end_master_balance   
                master_wallet.save()
            else:
                logger.info('on_trans_paid_success(): api action is {0} do nothing'.format(api_trans.action))
            api_trans.trade_status = TRADE_STATUS_SUCCESS
            api_trans.save()
        return True

    @staticmethod
    def on_trans_cancelled(api_trans):
        logger.info("on_trans_cancel(api trans{0})".format(
            api_trans.transactionId
        ))
        with transaction.atomic():
            user_cny_wallet = UserWallet.objects.select_for_update().get(
                user__id = api_trans.api_user.user.id, 
                wallet__cryptocurrency__currency_code ='CNY')
            total_cny_in_units = round(float(api_trans.total_fee)/100.0,8)
            if api_trans.action == API_METHOD_REDEEM:
                logger.info("on_trans_cancel(api trans{0}): trans is sell, so cancel it")
                if user_cny_wallet.locked_balance < total_cny_in_units :
                    logger.error("[out_trade_no: {0}] user {1} does not have enough locked CNY in wallet: locked {2} to be released {3}. ".format(
                        api_trans.api_out_trade_no,
                        api_trans.api_user.username, user_cny_wallet.locked_balance, total_cny_in_units 
                    ))
                    raise ValueError('CNY_WALLET_NOT_ENOUGH_LOCKED')
                user_cny_wallet.available_balance = user_cny_wallet.available_balance + total_cny_in_units
                user_cny_wallet.locked_balance = user_cny_wallet.locked_balance - total_cny_in_units
            else:
                logger.info("on_trans_cancel(api trans{0}): trans is buy, nothing to do")
            user_cny_wallet.save()


    @staticmethod
    def on_found_success_purchase_trans(api_trans):
        logger.debug('on_found_success_purchase_trans')
        total_cny_in_units = round(float(api_trans.total_fee)/100.0,8)

        # send notification if needed
        if api_trans.notify_url:
            logger.debug('on_found_success_purchase_trans(): has notify_url {0}'.format(api_trans.notify_url))
        if api_trans.last_notify_response:
            logger.debug('on_found_success_purchase_trans(): has last_notify_response {0}'.format(
                api_trans.last_notify_response))
        if api_trans.last_status_description:
            logger.debug('on_found_success_purchase_trans(): has last_status_description {0}'.format(
                api_trans.last_status_description))
            
        if api_trans.notify_url and (
            (not api_trans.last_notify_response) or api_trans.last_status_description != 'NOTIFYSUCCESS'):
            need_to_send_notification = False
            if api_trans.last_notified_at:
                since_last_notify = timezone.now() - api_trans.last_notified_at
                since_creation = timezone.now() - api_trans.created_at
                need_to_send_notification = since_last_notify.total_second() >= 180 and since_creation <= api_trans.expire_in_sec
            else:
                need_to_send_notification = True
            if need_to_send_notification:
                logger.info('on_found_success_purchase_trans(): send notification to buyer')
                notify = PurchaseAPINotify(
                    '1.0',
                    api_trans.api_user.apiKey,
                    api_trans.api_user.secretKey,
                    api_trans.api_out_trade_no,
                    api_trans.transactionId,
                    api_trans.payment_provider.code,
                    api_trans.subject,
                    api_trans.total_fee,
                    api_trans.trade_status,
                    api_trans.real_fee,
                    api_trans.payment_provider_last_notified_at.strftime("%Y%m%d%H%M%S") if api_trans.payment_provider_last_notified_at else None,
                    from_account=api_trans.payment_account,
                    #to_account = api_trans.to_account,
                    attach = api_trans.attach
                )
                api_client = APIClient(api_trans.notify_url)
                notify_resp = ""
                try:
                    notify_resp = api_client.send_json_request(notify.to_json(), response_format='text')
                    notify_resp = notify_resp[:NOTIFY_RESPONSE_LEN]
                    if notify_resp.startswith('\ufeff'):
                        notify_resp = notify_resp.encode('utf-8').decode("utf-8-sig")
                    else:
                        notify_resp = notify_resp.decode("utf-8-sig")
                except:
                    logger.info('send api user notification hit error {0}'.format(sys.exc_info()[0]))
                # update notify situation
                comment = 'NOTIFYSUCCESS' if notify_resp and notify_resp.upper() == 'OK' else 'NOTIFYFAILED: {0}'.format(notify_resp)
                APIUserTransactionManager.update_notification_status(
                    api_trans.transactionId, 
                    json.dumps(notify.to_json(), ensure_ascii = False), 
                    notify_resp, comment)
        
        if api_trans.action == API_METHOD_PURCHASE:
            external_crypto_addr = api_trans.external_cny_receive_addr if api_trans.external_cny_receive_addr else APIUserManager.get_api_user_external_crypto_addr(api_trans.api_user.user.id, 'CNY')
            if not external_crypto_addr:
                logger.info('on_found_success_purchase_trans: buyer for api trans {0} has no external cny wallet, nothing to do'.format(
                    api_trans.transactionId
                ))
                return
            logger.info('on_found_success_purchase_trans: buyer for api trans {0} has external cny wallet address {1}, transfer fund'.format(
                api_trans.transactionId, external_crypto_addr
            ))

            operatorObj = User.objects.get(username='admin')
            with transaction.atomic():
                user_cny_wallet = UserWallet.objects.select_for_update().get(
                    user__id = api_trans.api_user.user.id, 
                    wallet__cryptocurrency__currency_code ='CNY')

                user_cny_wallet_trans = None
                try:
                    user_cny_wallet_trans = UserWalletTransaction.objects.get(
                        user_wallet__id=user_cny_wallet.id,
                        reference_order__order_id=api_trans.reference_order.order_id,
                        transaction_type = 'AUTOREDEEM')
                except UserWalletTransaction.DoesNotExist:
                    logger.info('on_found_paid_purchase_trans: try to auto redeem for api trans {0}'.format(
                        api_trans.transactionId
                    ))
                    crypto_util = get_coin_utils(CNYFUND_CRYPTO_CODE)
                    comment = 'userId:{0},amount:{1},trxId:{2},out_trade_no:{3}'.format(
                        api_trans.api_user.user.id, total_cny_in_units, 
                        api_trans.transactionId, api_trans.api_out_trade_no)
                    try:
                        crypto_util.unlock_wallet(15)
                        crypto_trans = crypto_util.send_fund(external_crypto_addr, total_cny_in_units, comment)
                        operation_comment='api user {0} send his purchased {1} CNY back his wallet'.format(
                            api_trans.api_user.user.username, total_cny_in_units
                        )
                        logger.debug('on_found_paid_purchase_trans(): create userwalletrans about {0}'.format(
                            operation_comment
                        ))

                        user_cny_wallet_trans = UserWalletTransaction.objects.create(
                            user_wallet = user_cny_wallet,
                            reference_order = api_trans.reference_order,
                            reference_wallet_trxId = crypto_trans['txid'],
                            units = total_cny_in_units,
                            balance_begin = user_cny_wallet.balance,
                            balance_end = user_cny_wallet.balance,
                            locked_balance_begin = user_cny_wallet.locked_balance,
                            locked_balance_end = user_cny_wallet.locked_balance + total_cny_in_units,
                            available_to_trade_begin = user_cny_wallet.available_balance,
                            available_to_trade_end = user_cny_wallet.available_balance - total_cny_in_units,
                            fiat_money_amount = total_cny_in_units,
                            payment_provider = api_trans.payment_provider,
                            balance_update_type= 'DEBT',
                            transaction_type = 'AUTOREDEEM',
                            comment = operation_comment,
                            reported_timestamp = timegm(dt.datetime.utcnow().utctimetuple()),
                            status = 'PENDING',
                            created_by = operatorObj,
                            lastupdated_by = operatorObj
                        )
                        user_cny_wallet_trans.save()
                        user_cny_wallet.available_balance = user_cny_wallet.available_balance - total_cny_in_units                    
                        user_cny_wallet.locked_balance = user_cny_wallet.locked_balance + total_cny_in_units
                        #unlock the wallet
                        user_cny_wallet.save()
                    except:
                        error_msg = traceback.format_exc()

                        logger.error('on_found_success_purchase_trans(api trans {0}): sending cny upon purchase hit exception {1}, detail is {2}'.format(
                            api_trans.transactionId, sys.exc_info()[0], error_msg
                        ))
                        traceback.print_exc(file=sys.stdout)
                except UserWalletTransaction.MultipleObjectsReturned:
                    logger.error('on_found_success_purchase_trans(api trans {0}): has more than one cny wallet transaction related to order {1}'.format(
                        api_trans.transactionId, api_trans.reference_order.order_id
                    ))

    @staticmethod
    def on_cancel_transaction(api_trans):
        logger.info('on_cancel_transaction(api_trans({0}).orderId={1})'.format(
            api_trans.transactionId, 
            api_trans.reference_order.order_id if api_trans.reference_order is not None else 'N/A'))
        total_cny_in_units = round(float(api_trans.total_fee)/100.0,8)

        crypto_trans = None
        if api_trans.action == API_METHOD_REDEEM:
            logger.info("on_cancel_transaction() will try to repay the CNYF sent here for redeem")
            external_crypto_addr = APIUserManager.get_api_user_external_crypto_addr(api_trans.api_user.user.id, 'CNY')
            if not external_crypto_addr:
                logger.info('on_cancel_transaction: seller for api trans {0} has no external cny wallet, nothing to do'.format(
                    api_trans.transactionId
                ))
                return
            logger.info('on_cancel_transaction: seller for api trans {0} has external cny wallet, transfer fund'.format(
                api_trans.transactionId
            ))

            operatorObj = User.objects.get(username='admin')
            with transaction.atomic():
                user_cny_wallet = UserWallet.objects.select_for_update().get(
                    user__id = api_trans.api_user.user.id, 
                    wallet__cryptocurrency__currency_code ='CNY')

                user_cny_wallet_trans = None
                try:
                    user_cny_wallet_trans = UserWalletTransaction.objects.get(
                        user_wallet__id=user_cny_wallet.id,
                        reference_order__order_id=api_trans.reference_order.order_id,
                        transaction_type = 'AUTOREDEEM')
                    logger.info('on_cancel_transaction: Found AUTOREDEEM transaction api trans {0}'.format(
                        api_trans.transactionId
                    ))
                except UserWalletTransaction.DoesNotExist:
                    logger.info('on_cancel_transaction: try to auto redeem for api trans {0}'.format(
                        api_trans.transactionId
                    ))
                    crypto_util = get_coin_utils(CNYFUND_CRYPTO_CODE)
                    comment = 'userId:{0},amount:{1},trxId:{2},out_trade_no:{3}'.format(
                        api_trans.api_user.user.id, total_cny_in_units, 
                        api_trans.transactionId, api_trans.api_out_trade_no)
                    try:
                        crypto_util.unlock_wallet(15)
                        crypto_trans = crypto_util.send_fund(external_crypto_addr, total_cny_in_units, comment)
                        operation_comment='api user {0} send his redeem amount {1} CNY back his wallet'.format(
                            api_trans.api_user.user.username, total_cny_in_units
                        )
                        logger.info('on_cancel_transaction(): create userwalletrans about {0}'.format(
                            operation_comment
                        ))

                        user_cny_wallet_trans = UserWalletTransaction.objects.create(
                            user_wallet = user_cny_wallet,
                            reference_order = api_trans.reference_order,
                            reference_wallet_trxId = crypto_trans['txid'],
                            units = total_cny_in_units,
                            balance_begin = user_cny_wallet.balance,
                            balance_end = user_cny_wallet.balance,
                            locked_balance_begin = user_cny_wallet.locked_balance,
                            locked_balance_end = user_cny_wallet.locked_balance + total_cny_in_units,
                            available_to_trade_begin = user_cny_wallet.available_balance,
                            available_to_trade_end = user_cny_wallet.available_balance - total_cny_in_units,
                            fiat_money_amount = total_cny_in_units,
                            payment_provider = api_trans.payment_provider,
                            balance_update_type= 'DEBT',
                            transaction_type = 'AUTOREDEEM',
                            comment = operation_comment,
                            reported_timestamp = timegm(dt.datetime.utcnow().utctimetuple()),
                            status = 'PENDING',
                            created_by = operatorObj,
                            lastupdated_by = operatorObj
                        )
                        user_cny_wallet_trans.save()
                        user_cny_wallet.available_balance = user_cny_wallet.available_balance - total_cny_in_units                    
                        user_cny_wallet.locked_balance = user_cny_wallet.locked_balance + total_cny_in_units
                        #unlock the wallet
                        user_cny_wallet.save()
                    except:
                        logger.error('on_cancel_transaction(api trans {0}): sending cny upon purchase hit exception {1}'.format(
                            api_trans.transactionId, sys.exc_info()[0]
                        ))
                        traceback.print_exc(file=sys.stdout)
                except UserWalletTransaction.MultipleObjectsReturned:
                    logger.error('on_cancel_transaction(api trans {0}): has more than one cny wallet transaction related to order {1}'.format(
                        api_trans.transactionId, api_trans.reference_order.order_id
                    ))
        # send notification if needed
        if api_trans.notify_url:
            logger.debug('on_cancel_transaction(): has notify_url {0}'.format(api_trans.notify_url))
        if api_trans.last_notify_response:
            logger.debug('on_cancel_transaction(): has last_notify_response {0}'.format(
                api_trans.last_notify_response))
        if api_trans.last_status_description:
            logger.debug('on_cancel_transaction(): has last_status_description {0}'.format(
                api_trans.last_status_description))
            
        if api_trans.notify_url and (
            (not api_trans.last_notify_response) or api_trans.last_status_description != 'NOTIFYSUCCESS'):
            need_to_send_notification = False
            if api_trans.last_notified_at:
                since_last_notify = timezone.now() - api_trans.last_notified_at
                since_creation = timezone.now() - api_trans.created_at
                need_to_send_notification = since_last_notify.total_seconds() >= 180 and since_creation <= api_trans.expire_in_sec
            else:
                need_to_send_notification = True
            need_to_send_notification =  need_to_send_notification or api_trans.trade_status in [TRADE_STATUS_BADRECEIVINGACCOUNT, TRADE_STATUS_EXPIREDINVALID]
            if need_to_send_notification:
                logger.info('on_cancel_transaction(): send notification to seller because its trade status is {0}'.format(
                    api_trans.trade_status
                ))
                notify = PurchaseAPINotify(
                    '1.0',
                    api_trans.api_user.apiKey,
                    api_trans.api_user.secretKey,
                    api_trans.api_out_trade_no,
                    api_trans.transactionId,
                    api_trans.payment_provider.code,
                    api_trans.subject,
                    api_trans.total_fee,
                    api_trans.trade_status,
                    api_trans.real_fee,
                    api_trans.payment_provider_last_notified_at.strftime("%Y%m%d%H%M%S") if api_trans.payment_provider_last_notified_at else None,
                    from_account=api_trans.payment_account,
                    #to_account = api_trans.to_account,
                    attach = api_trans.attach,
                    txid = crypto_trans['txid']
                )
                api_client = APIClient(api_trans.notify_url)
                notify_resp = ""
                try:
                    notify_resp = api_client.send_json_request(notify.to_json(), response_format='text')
                    notify_resp = notify_resp[:NOTIFY_RESPONSE_LEN]
                    if notify_resp.startswith('\ufeff'):
                        notify_resp = notify_resp.encode('utf-8').decode("utf-8-sig")
                    else:
                        notify_resp = notify_resp.decode("utf-8-sig")
                except:
                    logger.info('send api user notification hit error {0}'.format(sys.exc_info()[0]))
                # update notify situation
                comment = 'NOTIFYSUCCESS' if notify_resp and notify_resp == 'ok' else 'NOTIFYFAILED: {0}'.format(notify_resp)
                APIUserTransactionManager.update_notification_status(
                    api_trans.transactionId, 
                    json.dumps(notify.to_json(), ensure_ascii = False), 
                    notify_resp, comment)


    @staticmethod
    def on_found_redeem_trans_with_badaccount(api_trans):
        logger.debug('on_found_redeem_trans_with_badaccount')
        total_cny_in_units = round(float(api_trans.total_fee)/100.0,8)

        # send notification if needed
        if api_trans.notify_url:
            logger.debug('on_found_redeem_trans_with_badaccount(): has notify_url {0}'.format(api_trans.notify_url))
        if api_trans.last_notify_response:
            logger.debug('on_found_redeem_trans_with_badaccount(): has last_notify_response {0}'.format(
                api_trans.last_notify_response))
        if api_trans.last_status_description:
            logger.debug('on_found_redeem_trans_with_badaccount(): has last_status_description {0}'.format(
                api_trans.last_status_description))
            
        if api_trans.notify_url and (
            (not api_trans.last_notify_response) or api_trans.last_status_description != 'NOTIFYSUCCESS'):
            need_to_send_notification = False
            if api_trans.last_notified_at:
                since_last_notify = timezone.now() - api_trans.last_notified_at
                since_creation = timezone.now() - api_trans.created_at
                need_to_send_notification = since_last_notify.total_second() >= 180 and since_creation <= api_trans.expire_in_sec
            else:
                need_to_send_notification = True
            need_to_send_notification =  need_to_send_notification and (api_trans.trade_status == TRADE_STATUS_BADRECEIVINGACCOUNT or api_trans.trade_status == TRADE_STATUS_USERABANDON)
            if need_to_send_notification:
                logger.info('on_found_redeem_trans_with_badaccount(): send notification to seller because its trade status is {0}'.format(
                    api_trans.trade_status
                ))
                notify = PurchaseAPINotify(
                    '1.0',
                    api_trans.api_user.apiKey,
                    api_trans.api_user.secretKey,
                    api_trans.api_out_trade_no,
                    api_trans.transactionId,
                    api_trans.payment_provider.code,
                    api_trans.subject,
                    api_trans.total_fee,
                    api_trans.trade_status,
                    api_trans.real_fee,
                    api_trans.payment_provider_last_notified_at.strftime("%Y%m%d%H%M%S") if api_trans.payment_provider_last_notified_at else None,
                    from_account=api_trans.payment_account,
                    #to_account = api_trans.to_account,
                    attach = api_trans.attach
                )
                api_client = APIClient(api_trans.notify_url)
                notify_resp = ""
                try:
                    notify_resp = api_client.send_json_request(notify.to_json(), response_format='text')
                    notify_resp = notify_resp[:NOTIFY_RESPONSE_LEN]
                except:
                    logger.info('send api user notification hit error {0}'.format(sys.exc_info()[0]))
                # update notify situation
                comment = 'NOTIFYSUCCESS' if notify_resp and notify_resp.upper() == 'OK' else 'NOTIFYFAILED: {0}'.format(notify_resp)
                APIUserTransactionManager.update_notification_status(
                    api_trans.transactionId, 
                    json.dumps(notify.to_json(), ensure_ascii = False), 
                    notify_resp, comment)
        
