#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz, math
import logging

from django.db import transaction
from django.contrib.auth.models import User

from trading.models import *
from trading.config import context_processor
from trading.controller.axfd_utils import AXFundUtility
from trading.controller import redeemmanager
from trading.views.models.useraccountinfo import *
from trading.views.models.userpaymentmethodview import *
from trading.views.models.userexternalwalletaddrinfo import *

logger = logging.getLogger("site.useraccountinfomanager")

def update_user_wallet_based_on_deposit(trx, user_wallet_id, min_trx_confirmation,
                                        operator):
    try:
        user_wallet_trans = UserWalletTransaction.objects.get(
            user_wallet__id=user_wallet_id,
            reference_wallet_trxId=trx['txid'],
            transaction_type='DEPOSIT')
        if user_wallet_trans.status == 'PENDING' and trx['confirmations'] >= min_trx_confirmation:
            logger.info('update_user_wallet_based_on_deposit(): txid {0} has just been confirmed, change status of user_wallet_trans {1} to PROCESSED and update wallet balance'.format(
                 trx['txid'], user_wallet_trans.id
            ))

            amount = math.fabs(trx['amount'])
            if math.fabs(user_wallet_trans.units - amount) > 0.00000001:
                raise ValueError('update_user_wallet_based_on_deposit(): Amount not match: usertran {0}: units {1} txid {2}: amount {3}'.format(
                   user_wallet_trans.id, user_wallet_trans.units,
                   trx['txid'], amount
                ))
            with transaction.atomic():
                user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet_id)
                logger.info('update_user_wallet_based_on_deposit(): before updating existing deposit trans, userwallet[{0}:{1}]: balance {2} locked {3} available {4}'.format(
                    user_wallet.id, user_wallet.wallet_addr, user_wallet.balance, user_wallet.locked_balance, user_wallet.available_balance))
                balance_end = user_wallet.balance + trx['amount']
                available_to_trade_end = user_wallet.available_balance + trx['amount']
                user_wallet_trans.balance_begin = user_wallet.balance
                user_wallet_trans.balance_end = balance_end
                user_wallet_trans.available_to_trade_begin = user_wallet.available_balance
                user_wallet_trans.available_to_trade_end = available_to_trade_end
                user_wallet_trans.lastupdated_by = operator
                user_wallet_trans.status = 'PROCESSED'
                user_wallet_trans.save()

                user_wallet.balance = balance_end
                user_wallet.available_balance = available_to_trade_end
                user_wallet.user_wallet_trans_id = user_wallet_trans.id
                user_wallet.lastupdated_by = operator
                user_wallet.save()
                
                logger.info('update_user_wallet_based_on_deposit(): txid {0} updated userwallet[{1}:{2}] to balance {3} locked {4} available {5}'.format(
                    trx['txid'], user_wallet.id, user_wallet.wallet_addr, 
                    user_wallet.balance, user_wallet.locked_balance, user_wallet.available_balance,
                ))
        elif user_wallet_trans.status == 'PENDING' and trx['confirmations'] < min_trx_confirmation:
            if int(time.time()) - trx['timereceived'] >= 24 * 3600:
                error_msg = 'update_user_wallet_based_on_deposit(): Wallet deposite txid {0} has not had {1} confirmation after more than a day'.format(trx['txid'], min_trx_confirmation)
                logger.warn(error_msg)
                raise ValueError(error_msg)
        elif user_wallet_trans.status == 'PROCESSED' and trx['confirmations'] < min_trx_confirmation:
            error_msg = "update_user_wallet_based_on_deposit(): How come txid {0} only has {1} confirmation but wallet_trans {2} is PROCESSED".format(
                trx['txid'], trx['confirmations'], user_wallet_trans.id
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            logger.info('update_user_wallet_based_on_deposit(): txid {0} has been reflected in transaction, nothing to do'.format(trx['txid']))

    except UserWalletTransaction.DoesNotExist:
        with transaction.atomic():
            user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet_id)
            logger.info('update_user_wallet_based_on_deposit(): txid {0} confirmations: {1} vs min_confirmation {2} amount: {3} create deposit user wallet trans for user {4}'.format(
                trx['txid'], trx['confirmations'], min_trx_confirmation, trx['amount'], user_wallet.user.id 
            ))
            logger.info('update_user_wallet_based_on_deposit(): before updating, userwallet[{0}:{1}]: balance {2} locked {3} available {4}'.format(
                user_wallet.id, user_wallet.wallet_addr, user_wallet.balance, user_wallet.locked_balance, user_wallet.available_balance))
            trans_status = 'PENDING'
            balance_begin = 0
            balance_end = 0
            locked_balance_begin = 0
            locked_balance_end = 0
            available_to_trade_begin =0
            available_to_trade_end = 0
            if trx['confirmations'] >= min_trx_confirmation:
                trans_status = 'PROCESSED'
                balance_begin = user_wallet.balance
                balance_end = balance_begin + trx['amount']
                locked_balance_begin = user_wallet.locked_balance
                locked_balance_end = locked_balance_begin
                available_to_trade_begin = user_wallet.available_balance
                available_to_trade_end = available_to_trade_begin + trx['amount']

            wallet_trans = UserWalletTransaction.objects.create(
                user_wallet = user_wallet,
                balance_begin= balance_begin,
                balance_end = balance_end,
                locked_balance_begin = locked_balance_begin,
                locked_balance_end = locked_balance_end,
                available_to_trade_begin = available_to_trade_begin,
                available_to_trade_end = available_to_trade_end,
                reference_order = None,
                reference_wallet_trxId = trx['txid'],
                units = trx['amount'],
                balance_update_type = 'CREDIT',
                transaction_type = 'DEPOSIT',
                comment = 'User deposit',
                reported_timestamp = trx['timereceived'],
                status = trans_status,
                created_by = operator,
                lastupdated_by = operator
            )

            wallet_trans.save()
            logger.info('Create deposit transaction {0} related to txid {1}'.format(
                  wallet_trans.id,trx['txid']))
            if trx['confirmations'] >= min_trx_confirmation:
                user_wallet.balance = balance_end
                user_wallet.available_balance = available_to_trade_end
                user_wallet.user_wallet_trans_id = wallet_trans.id
                user_wallet.lastupdated_by = operator
                user_wallet.save()
                logger.info('update_user_wallet_based_on_deposit(): txid {0} updated userwallet[{1}:{2}] to balance {3} locked {4} available {5}'.format(
                    trx['txid'], user_wallet.id, user_wallet.wallet_addr, 
                    user_wallet.balance, user_wallet.locked_balance, user_wallet.available_balance,
                ))

    except UserWalletTransaction.MultipleObjectsReturned:
         logger.error('update_user_wallet_based_on_deposit(): There are more than one transaction related to txid {0} for user id {1} on receiving address {2}'.format(
             trx['txid'], user_wallet.user.id, user_wallet.wallet_addr))

def update_user_wallet_based_on_redeem(trx, user_wallet_id, min_trx_confirmation,
                                        operator):
    try:
        user_wallet_trans = UserWalletTransaction.objects.get(
            transaction_type ='REDEEM',
            user_wallet__id=user_wallet_id,
            reference_wallet_trxId=trx['txid'])
        user_wallet_fee_trans = UserWalletTransaction.objects.get(
            transaction_type ='REDEEMFEE',
            user_wallet__id=user_wallet_id,
            reference_wallet_trxId=trx['txid'])
        if user_wallet_trans.status == 'PENDING' and trx['confirmations'] >= min_trx_confirmation:
            logger.info('update_user_wallet_based_on_redeem(): txid {0} has just been confirmed, change status of user_wallet_trans {1} and fee trans {2} to PROCESSED and update wallet balance'.format(
                 trx['txid'], user_wallet_trans.id, user_wallet_fee_trans.id
            ))

            amount = math.fabs(trx['amount'])
            fee = math.fabs(trx['fee'])
            if math.fabs(user_wallet_trans.units - amount) > 0.00000001:
                raise ValueError('update_user_wallet_based_on_redeem(): Amount not match: usertran {0}: units {1} txid {2}: amount {3}'.format(
                   user_wallet_trans.id, user_wallet_trans.units,
                   trx['txid'], amount
                ))
            if math.fabs(user_wallet_fee_trans.units - fee) > 0.00000001:
                raise ValueError('update_user_wallet_based_on_redeem(): Amount not match: user_fee_tran {0}: fee {1} txid {2}: fee {3}'.format(
                   user_wallet_fee_trans.id, user_wallet_fee_trans.units,
                   trx['txid'], fee
                ))

            with transaction.atomic():
                user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet_id)
                logger.info('update_user_wallet_based_on_redeem(): before updating existing redeem trans, userwallet[{0}:{1}]: balance {2} locked {3} available {4}'.format(
                    user_wallet.id, user_wallet.wallet_addr, user_wallet.balance, user_wallet.locked_balance, user_wallet.available_balance))

                balance_begin = user_wallet.balance
                balance_end = user_wallet.balance - amount
                balance_fee_begin = balance_end
                balance_fee_end = balance_fee_begin - fee

                locked_balance_begin = user_wallet.locked_balance
                locked_balance_end = user_wallet.locked_balance - amount 
                locked_balance_fee_begin = locked_balance_end
                locked_balance_fee_end = locked_balance_fee_begin - fee

                available_to_trade_begin = user_wallet.available_balance
                available_to_trade_end = available_to_trade_begin
                available_to_trade_fee_begin = available_to_trade_end
                available_to_trade_fee_end = available_to_trade_fee_begin

                # update original pending redeem trans
                user_wallet_trans.balance_begin = balance_begin
                user_wallet_trans.balance_end = balance_end
                user_wallet_trans.locked_balance_begin =  locked_balance_begin
                user_wallet_trans.locked_balance_end =  locked_balance_end
                user_wallet_trans.available_to_trade_begin = available_to_trade_begin
                user_wallet_trans.available_to_trade_end = available_to_trade_end
                user_wallet_trans.lastupdated_by = operator
                user_wallet_trans.status = 'PROCESSED'
                user_wallet_trans.save()

                user_wallet_fee_trans.balance_begin = balance_fee_begin
                user_wallet_fee_trans.balance_end = balance_fee_end
                user_wallet_fee_trans.locked_balance_begin =  locked_balance_fee_begin
                user_wallet_fee_trans.locked_balance_end =  locked_balance_fee_end
                user_wallet_fee_trans.available_to_trade_begin = available_to_trade_fee_begin
                user_wallet_fee_trans.available_to_trade_end = available_to_trade_fee_end
                user_wallet_fee_trans.lastupdated_by = operator
                user_wallet_fee_trans.status = 'PROCESSED'
                user_wallet_fee_trans.save()

                user_wallet.balance = round(balance_fee_end,8)
                user_wallet.locked_balance = round(locked_balance_fee_end, 8)
                user_wallet.available_balance = round(available_to_trade_fee_end, 8)
                user_wallet.user_wallet_trans_id = user_wallet_trans.id
                user_wallet.lastupdated_by = operator
                user_wallet.save()

                logger.info('update_user_wallet_based_on_redeem(): txid {0} updated userwallet[{1}:{2}] to balance {3} locked {4} available {5}'.format(
                    trx['txid'], user_wallet.id, user_wallet.wallet_addr, 
                    user_wallet.balance, user_wallet.locked_balance, user_wallet.available_balance,
                ))
        elif user_wallet_trans.status == 'PENDING' and trx['confirmations'] < min_trx_confirmation:
            if int(time.time()) - trx['timereceived'] >= 24 * 3600:
                logger.warn('update_user_wallet_based_on_redeem(): Wallet redeem txid {0} has not had {1} confirmation after more than a day'.format(trx['txid'], min_trx_confirmation))
        elif user_wallet_trans.status == 'PROCESSED' and trx['confirmations'] < min_trx_confirmation:
            logger.error("update_user_wallet_based_on_redeem(): How come txid {0} only has {1} confirmation but wallet_trans {2} is PROCESSED".format(
                trx['txid'], trx['confirmations'], user_wallet_trans.id
            ))
        else:
            logger.info('update_user_wallet_based_on_redeem(): txid {0} has been reflected in transaction, nothing to do'.format(trx['txid']))

    except UserWalletTransaction.DoesNotExist:
        with transaction.atomic():
            user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet_id)
            logger.info('update_user_wallet_based_on_redeem(): txid {0} confirmations: {1} vs min_confirmation {2} amount: {3} fee: {4} create deposit user wallet trans for user {5}'.format(
                trx['txid'], trx['confirmations'], min_trx_confirmation, trx['amount'], trx['fee'], user_wallet.user.id 
            ))
            logger.info('update_user_wallet_based_on_redeem(): before updating, userwallet[{0}:{1}]: balance {2} locked {3} available {4}'.format(
                user_wallet.id, user_wallet.wallet_addr, user_wallet.balance, user_wallet.locked_balance, user_wallet.available_balance))

            trans_status = 'PENDING'
            amount = math.fabs(trx['amount'])
            fee = math.fabs(trx['fee'])
            user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet.id)
            if trx['confirmations'] >= min_trx_confirmation:
                trans_status = 'PROCESSED'
                balance_begin = user_wallet.balance
                balance_end = user_wallet.balance - amount
                balance_fee_begin = balance_end
                balance_fee_end = balance_fee_begin - fee

                locked_balance_begin = user_wallet.locked_balance
                locked_balance_end = user_wallet.locked_balance
                locked_balance_fee_begin = locked_balance_end
                locked_balance_fee_end = locked_balance_fee_begin

                available_to_trade_begin = user_wallet.available_balance
                available_to_trade_end = available_to_trade_begin - amount
                available_to_trade_fee_begin = available_to_trade_end
                available_to_trade_fee_end = available_to_trade_fee_begin - fee
            else:
                trans_status = 'PENDING'
                balance_begin = user_wallet.balance
                balance_end = balance_begin
                balance_fee_begin = balance_end
                balance_fee_end = balance_fee_begin

                locked_balance_begin = user_wallet.locked_balance
                locked_balance_end = user_wallet.locked_balance + amount
                locked_balance_fee_begin = locked_balance_end
                locked_balance_fee_end = locked_balance_fee_begin + fee

                available_to_trade_begin = user_wallet.available_balance
                available_to_trade_end = available_to_trade_begin - amount
                available_to_trade_fee_begin = available_to_trade_end
                available_to_trade_fee_end = available_to_trade_fee_begin - fee
                

            logger.info('update_user_wallet_based_on_redeem(): about to create {0} user wallet trasaction for txid {1}'.format(
                trans_status, trx['txid']
            ))
            UserWalletTransaction.objects.create(
                user_wallet = user_wallet,
                balance_begin= balance_begin,
                balance_end = balance_end ,
                locked_balance_begin = locked_balance_begin,
                locked_balance_end = locked_balance_end,
                available_to_trade_begin = available_to_trade_begin,
                available_to_trade_end = available_to_trade_end,
                reference_order = None,
                reference_wallet_trxId = trx['txid'],
                units = amount,
                balance_update_type = 'DEBT',
                transaction_type = 'REDEEM',
                comment = 'User redeem',
                reported_timestamp = trx['timereceived'],
                status = trans_status,
                created_by = operator,
                lastupdated_by = operator
            ).save()

            UserWalletTransaction.objects.create(
                user_wallet = user_wallet,
                balance_begin= balance_fee_begin,
                balance_end = balance_fee_end,
                locked_balance_begin = locked_balance_fee_begin,
                locked_balance_end = locked_balance_fee_end,
                available_to_trade_begin = available_to_trade_fee_begin,
                available_to_trade_end = available_to_trade_fee_end,
                reference_order = None,
                reference_wallet_trxId = trx['txid'],
                units = fee,
                balance_update_type = 'DEBT',
                transaction_type = 'REDEEMFEE',
                comment = 'User redeem fee',
                reported_timestamp = trx['timereceived'],
                status = trans_status,
                created_by = operator,
                lastupdated_by = operator
            ).save()

            user_wallet.balance = round(balance_fee_end,8)
            user_wallet.locked_balance = round(locked_balance_fee_end,8)
            user_wallet.available_balance = round(available_to_trade_fee_end,8)
            user_wallet.lastupdated_by = operator
            user_wallet.save()

            logger.info('update_user_wallet_based_on_redeem(): txid {0} updated userwallet[{1}:{2}] to balance {3} locked {4} available {5}'.format(
                trx['txid'], user_wallet.id, user_wallet.wallet_addr, 
                user_wallet.balance, user_wallet.locked_balance, user_wallet.available_balance,
            ))
    except UserWalletTransaction.MultipleObjectsReturned:
         logger.error('update_user_wallet_based_on_redeem(): There are more than one transaction related to txid {0} for user id {1} on receiving address {2}'.format(
             trx['txid'], user_wallet.user.id, user_wallet.wallet_addr))

def get_send_money_trans_userid(trx):
    try:
        comment_parts = trx['comment'].split(',')
        if len(comment_parts) < 3:
            logger.error("The comment {0} is not in expected format of User:id redeem: amount to:address".format(trx['comment']))
            return -1
        parts1 = comment_parts[0].split(':')
        return int(parts1[1])
    except Exception as e:
        error_msg = "Failed to parse userid from trx[{0}], with comment {1}".format(
            trx['txid'],trx['comment'])
        logger.exception(error_msg)
        return -1

def update_account_balance_with_wallet_trx(crypto, trans, min_trx_confirmation):
    # prepare the data for sysop, which will be the created_by and last
    # updated by
    operator = User.objects.get(username='admin')

    # get all user's Wallets
    user_wallets = UserWallet.objects.filter(user__isnull=False, wallet__cryptocurrency__currency_code=crypto)

    # build a lookup table based on user's wallet receiving address
    # so that we can create new trx entry for the user account
    wallet_lookup_by_addr = {}
    wallet_lookup_by_userid = {}

    for wallet in user_wallets:
        if wallet.wallet_addr not in wallet_lookup_by_addr:
           wallet_lookup_by_addr[wallet.wallet_addr]= wallet.id
        else:
           raise ValueError('address {0} should not have more than one entry in userwallets'.format(wallet.wallet_addr))

        if wallet.user.id not in wallet_lookup_by_userid:
           wallet_lookup_by_userid[wallet.user.id] = wallet.id
        else:
           raise ValueError('user id {0} should not have more than one entry in userwallets'.format(wallet.user.id))

    for trx in trans:
        # only process confirmed wallet transactions
        try:
            if trx['category'] == 'receive':
                if trx['address'] in wallet_lookup_by_addr:
                    wallet_id = wallet_lookup_by_addr[trx['address']]
                    update_user_wallet_based_on_deposit(
                          trx, wallet_id, min_trx_confirmation, operator)
                else:
                    logger.error('Transaction {0} with address {1} does not belong to any user'.format(
                            trx['txid'],trx['address']))
            elif trx['category'] == 'send':
                userid = get_send_money_trans_userid(trx)
                logger.info("Get user id {0} from trx[{1}]'s comment {2}'".format(
                      userid, trx['txid'], trx['comment']))
                if userid == -1:
                    # means userid parse has issue, the logger should have logged it
                    pass
                elif userid in wallet_lookup_by_userid:
                    wallet_id = wallet_lookup_by_userid[userid]
                    update_user_wallet_based_on_redeem(
                          trx, wallet_id, min_trx_confirmation, operator)
                else:
                    logger.error('Could not find user wallet for Transaction {0} with  comment {1} '.format(
                            trx['txid'],trx['comment']))
        except ValueError as ve:
            logger.exception('Encounter error when processing transaction: {0}'.format(trx['txid']))

def get_user_accountInfo(user, crypto, load_balance_only=False):
    logger.info("get account info for user {0} in {1}".format(user.username, crypto))
    #user = User.objects.get(pk=userid)
    userwallet = UserWallet.objects.get(user=user, wallet__cryptocurrency__currency_code=crypto)
    balance = userwallet.balance
    available_balance = userwallet.available_balance
    locked_balance = userwallet.locked_balance
    receiving_addr = userwallet.wallet_addr
    externaladdr = None
    payment_methods= []
    if not load_balance_only:
        userpayments = UserPaymentMethod.objects.filter(user=user)
        external_addresses = UserExternalWalletAddress.objects.filter(user= user).filter(cryptocurrency__currency_code=crypto)
        if external_addresses:
           logger.info('Found the external address record for user {0} with {1}'.format(user.username, crypto))
           record = external_addresses[0]
           externaladdr = UserExternalWalletAddressInfo(record.id, record.user.id,
               record.alias, record.address, record.cryptocurrency.currency_code)
        else:
           logger.info('There is no external address for user {0} with {1}'.format(user.username, crypto))
        if userpayments:
           logger.info('User {0} has setup payment methods'.format(user.username))
           for method in userpayments:
              payment_methods.append(UserPaymentMethodView(method.id,
                    user.id, method.provider.code,
                    method.provider.name,method.account_at_provider,
                    method.provider_qrcode_image))
    userInfo = UserAccountInfo(user.username, user.id,
          round(balance,8),
          round(locked_balance,8),
          round(available_balance,8),
          receiving_addr,
          externaladdr,
          payment_methods)
    return userInfo

def get_user_externaladdr_by_id(id):
    record = UserExternalWalletAddress.objects.get(pk=id)
    return UserExternalWalletAddressInfo(record.id, record.user.id,
        record.alias, record.address, record.cryptocurrency.currency_code)

def create_update_externaladdr(externaladdress, operator):
    operatorObj = User.objects.get(username=operator)
    if not redeemmanager.check_send_to_address(externaladdress.crypto,
           externaladdress.address):
        return False
    if externaladdress.id == 0:
        UserExternalWalletAddress.objects.create(
          user = User.objects.get(pk=externaladdress.userid),
          cryptocurrency = Cryptocurrency.objects.get(pk=externaladdress.crypto),
          address = externaladdress.address,
          alias = externaladdress.alias,
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
    else:
        with transaction.atomic():
            addr = UserExternalWalletAddress.objects.select_for_update().get(pk=externaladdress.id)
            addr.address = externaladdress.address
            addr.alias = externaladdress.alias
            addr.lastupdated_by = operatorObj
            addr.save()
    return True
