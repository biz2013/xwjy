#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging

from django.db import transaction

from users.models import *
from config import context_processor
from controller.axfd_utils import AXFundUtility
from views.models.useraccountinfo import *
from views.models.userpaymentmethodview import *
from views.models.userexternalwalletaddrinfo import *

logger = logging.getLogger("site.useraccountinfomanager")

def update_user_wallet_based_on_deposit(trx, user_wallet, min_trx_confirmation,
                                        operator):
    try:
        user_wallet_trans = UserWalletTransaction.objects.get(
            user_wallet__user__id=user_wallet.user.id,
            user_wallet__wallet_addr=user_wallet.wallet_addr,
            reference_wallet_trxId=trx['txid'])
        if user_wallet_trans.status == 'PENDING' and trx['confirmations'] >= min_trx_confirmation:
            logger.info('txid {0} is confirmed, need to change status for user_wallet_trans {1}'.format(
                 trx['txid'], user_wallet_trans.id
            ))
            with transaction.atomic():
                user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet.id)
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
            logger.info('Update user wallet balance for user id {0} address {1} related to newly confirmed txid {2}'.format(
                 user_wallet.user.id, user_wallet.wallet_addr, trx['txid']))
        elif user_wallet_trans.status == 'PENDING' and trx['confirmations'] < min_trx_confirmation:
            if int(time.time()) - trx['timereceived'] >= 24 * 3600:
                error_msg = 'Wallet deposite txid {0} has not had {1} confirmation after more than a day'.format(trx['txid'], min_trx_confirmation)
                logger.warn(error_msg)
                raise ValueError(error_msg)
        elif user_wallet_trans.status == 'PROCESSED' and trx['confirmations'] < min_trx_confirmation:
            error_msg = "How come txid {0} only has {1} confirmation but wallet_trans {2} is PROCESSED".format(
                trx['txid'], trx['confirmations'], user_wallet_trans.id
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            logger.info('txid {0} has been reflected in transaction, nothing to do'.format(trx['txid']))

    except UserWalletTransaction.DoesNotExist:
        with transaction.atomic():
            print 'come to create trans for deposit, trx confirmation is {0}, amount is {1} min_confirmation is {2}'.format(
                trx['confirmations'], trx['amount'], min_trx_confirmation
            )
            trans_status = 'PENDING'
            balance_end = user_wallet.balance
            available_to_trade_end = user_wallet.available_balance
            if trx['confirmations'] >= min_trx_confirmation:
                user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet.id)
                trans_status = 'PROCESSED'
                balance_end = user_wallet.balance + trx['amount']
                available_to_trade_end = user_wallet.available_balance + trx['amount']
            wallet_trans = UserWalletTransaction.objects.create(
                user_wallet = user_wallet,
                balance_begin= user_wallet.balance,
                balance_end = balance_end,
                locked_balance_begin = user_wallet.locked_balance,
                locked_balance_end = user_wallet.locked_balance,
                available_to_trade_begin = user_wallet.available_balance,
                available_to_trade_end = available_to_trade_end,
                reference_order = None,
                reference_wallet_trxId = trx['txid'],
                amount = trx['amount'],
                balance_update_type = 'CREDIT',
                transaction_type = 'DEPOSIT',
                comment = 'User deposit',
                reported_timestamp = trx['timereceived'],
                status = trans_status,
                created_by = operator,
                lastupdated_by = operator
            )
            logger.info('Create deposit transaction {0} related to txid {1}'.format(
                  wallet_trans.id,trx['txid']))
            if trx['confirmations'] >= min_trx_confirmation:
                user_wallet.balance = balance_end
                user_wallet.available_balance = available_to_trade_end
                user_wallet.user_wallet_trans_id = wallet_trans.id
                user_wallet.lastupdated_by = operator
                user_wallet.save()
                logger.info('Update user wallet balance for user id {0} address {1} related to txid {2}'.format(
                    user_wallet.user.id, user_wallet.wallet_addr, trx['txid']))

    except UserWalletTransaction.MultipleObjectsReturned:
         logger.error('There are more than one transaction related to txid {0} for user id {1} on receiving address {2}'.format(
             trx['txid'], user_wallet.user.id, user_wallet.wallet_addr))

def update_user_wallet_based_on_redeem(trx, user_wallet, min_trx_confirmation,
                                        operator):
    try:
        user_wallet_trans = UserWalletTransaction.objects.get(
            user_wallet__user__id=user_wallet.user.id,
            user_wallet__wallet_addr=user_wallet.wallet_addr,
            reference_wallet_trxId=trx['txid'])
        if user_wallet_trans.status == 'PENDING' and trx['confirmations'] >= min_trx_confirmation:
            logger.info('txid {0} is confirmed, need to change status for user_wallet_trans {1}'.format(
                 trx['txid'], user_wallet_trans.id
            ))
            with transaction.atomic():
                user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet.id)
                balance_end = user_wallet.balance - trx['amount']
                available_to_trade_end = user_wallet.available_balance - trx['amount']
                user_wallet_trans.balance_begin = user_wallet.balance
                user_wallet_trans.balance_end = balance_end
                user_wallet_trans.available_to_trade_begin = user_wallet.available_balance
                user_wallet_trans.available_to_trade_end = available_to_trade_end
                user_wallet_trans.lastupdated_by = operator
                user_wallet_trans.save()

                user_wallet.balance = balance_end
                user_wallet.available_balance = available_to_trade_end
                user_wallet.user_wallet_trans_id = user_wallet_trans.id
                user_wallet.lastupdated_by = operator
                user_wallet.save()
            logger.info('Update user wallet balance for user id {0} address {1} related to newly confirmed txid {2}'.format(
                 user_wallet.user.id, user_wallet.wallet_addr, trx['txid']))
        elif user_wallet_trans.status == 'PENDING' and trx['confirmations'] < min_trx_confirmation:
            if int(time.time()) - trx['timereceived'] >= 24 * 3600:
                logger.warn('Wallet redeem txid {0} has not had {1} confirmation after more than a day'.format(trx['txid'], min_trx_confirmation))
        elif user_wallet_trans.status == 'PROCESSED' and trx['confirmations'] < min_trx_confirmation:
            logger.error("How come txid {0} only has {1} confirmation but wallet_trans {2} is PROCESSED".format(
                trx['txid'], trx['confirmations'], user_wallet_trans.id
            ))
        else:
            logger.info('txid {0} has been reflected in transaction, nothing to do'.format(trx['txid']))

    except UserWalletTransaction.DoesNotExist:
        with transaction.atomic():
            trans_status = 'PENDING'
            balance_end = 0
            available_to_trade_end = 0
            if trx['confirmations'] >= min_trx_confirmation:
                user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet.id)
                trans_status = 'PROCESSED'
                balance_end = user_wallet.balance + trx['amount']
                available_to_trade_end = user_wallet.available_balance + trx['amount']
            wallet_trans = UserWalletTransaction.objects.create(
                user_wallet = user_wallet,
                balance_begin= user_wallet.balance,
                balance_end = balance_end,
                locked_balance_begin = user_wallet.locked_balance,
                locked_balance_end = user_wallet.locked_balance,
                available_to_trade_begin = user_wallet.available_balance,
                available_to_trade_end = available_to_trade_end,
                reference_order = None,
                reference_wallet_trxId = trx['txid'],
                amount = trx['amount'],
                balance_update_type = 'DEBT',
                transaction_type = 'REDEEM',
                comment = 'User redeem',
                reported_timestamp = trx['timereceived'],
                status = trans_status,
                created_by = operator,
                lastupdated_by = operator
            )
            logger.info('Create redeem transaction {0} related to txid {1}'.format(
                  wallet_trans.id,trx['txid']))
            if trx['confirmations'] >= min_trx_confirmation:
                user_wallet.balance = balance_end
                user_wallet.available_balance = available_to_trade_end
                user_wallet.user_wallet_trans_id = wallet_trans.id
                user_wallet.lastupdated_by = operator
                user_wallet.save()
                logger.info('Update user wallet balance for user id {0} address {1} related to txid {2}'.format(
                    user_wallet.user.id, user_wallet.wallet_addr, trx['txid']))

    except UserWalletTransaction.MultipleObjectsReturned:
         logger.error('There are more than one transaction related to txid {0} for user id {1} on receiving address {2}'.format(
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
    print 'update_account_balance_with_wallet_trx'
    # prepare the data for sysop, which will be the created_by and last
    # updated by
    operator = UserLogin.objects.get(pk='sysop')

    # get all user's Wallets
    user_wallets = UserWallet.objects.filter(user__isnull=False, wallet__cryptocurrency__currency_code=crypto)

    # build a lookup table based on user's wallet receiving address
    # so that we can create new trx entry for the user account
    wallet_lookup_by_addr = {}
    wallet_lookup_by_userid = {}

    for wallet in user_wallets:
        print 'come into wallets'
        if wallet.wallet_addr not in wallet_lookup_by_addr:
           wallet_lookup_by_addr[wallet.wallet_addr]= wallet
        else:
           raise ValueError('address {0} should not have more than one entry in userwallets'.format(wallet.wallet_addr))

        if wallet.user.id not in wallet_lookup_by_userid:
           wallet_lookup_by_userid[wallet.user.id] = wallet
        else:
           raise ValueError('user id {0} should not have more than one entry in userwallets'.format(wallet.user.id))

    print 'calling listtransaction return {0}'.format(trans)
    for trx in trans:
        # only process confirmed wallet transactions
        if trx['category'] == 'receive':
            if trx['address'] in wallet_lookup_by_addr:
                entry = wallet_lookup_by_addr[trx['address']]
                update_user_wallet_based_on_deposit(
                      trx, entry, min_trx_confirmation, operator)
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
                entry = wallet_lookup_by_userid[userid]
                update_user_wallet_based_on_redeem(
                      trx, entry, min_trx_confirmation, operator)
            else:
                logger.error('Could not find user wallet for Transaction {0} with  comment {1} '.format(
                        trx['txid'],trx['comment']))

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
          balance,
          locked_balance,
          available_balance,
          receiving_addr,
          externaladdr,
          payment_methods)
    return userInfo

def get_user_externaladdr_by_id(id):
    record = UserExternalWalletAddress.objects.get(pk=id)
    return UserExternalWalletAddressInfo(record.id, record.user.id,
        record.alias, record.address, record.cryptocurrency.currency_code)

def create_update_externaladdr(externaladdress, operator):
    operatorObj = UserLogin.objects.get(pk=operator)
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
