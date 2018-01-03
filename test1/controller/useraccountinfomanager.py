#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging

from django.db import transaction

from users.models import *
from config import context_processor
from controller import axfd_utils
from views.models.useraccountinfo import *
from views.models.userpaymentmethodview import *
from views.models.userexternalwalletaddrinfo import *

logger = logging.getLogger("site.useraccountinfomanager")

def update_user_wallet_based_on_deposit(trx, user_wallet, min_trx_confirmation,
                                        operator):
    try:
        user_wallet_trans = UserWalletTransaction.objects.filter(
            user_wallet__user__id=entry.user.id,
            user_wallet__wallet_addr=entry.wallet_addr,
            reference_wallet_trxId=trx['txid'])
        if user_wallet_trans.status == 'PENDING' and trx['confirmation'] >= min_trx_confirmation:
            logger.info('txid {0} is confirmed, need to change status for user_wallet_trans {1}'.format(
                 trx['txid'], user_wallet_trans.id
            ))
            with transactin.atomic():
                user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet.id)
                balance_end = user_wallet.balance + float(trx['amount'])
                available_to_trade_end = user_wallet.available_balance + float(trx['amount'])
                user_wallet_trans.balance_begin = user_wallet.balance
                user_wallet_trans.balance_end = balance_end
                user_wallet_trans.available_to_trade_begin = user_wallet.available_balance
                user_wallet_trans.available_to_trade_end = available_to_trade_end
                user_wallet_trans.lastupdated_by = operator
                user_wallet_trans.save()

                user_wallet.balance = balance_end
                user_wallet.available_balance = available_to_trade_end
                user_wallet.user_wallet_trans_id = wallet_trans.id
                user_wallet.lastupdated_by = operator
                user_wallet.save()
            logger.error('Update user wallet balance for user id {0} address {1} related to newly confirmed txid {2}'.format(
                 user_wallet.user.id, user_wallet.address, trx['txid']))
        elif user_wallet_trans.status == 'PENDING' and trx['confirmation'] < min_trx_confirmation:
            if int(dt.datetime.utcnow().timestamp()) - trx['timereceived'] >= 24 * 3600:
                logger.warn('Wallet deposite txid {0} has not had {1} confirmation after more than a day'.format(trx['txid'], min_trx_confirmation))
        elif user_wallet_trans.status == 'PROCESSED' and trx['confirmation'] < min_trx_confirmation:
            logger.error("How come txid {0} only has {1} confirmation but wallet_trans {2} is PROCESSED".format(
                trx['txid'], trx['confirmation'], user_wallet_trans.id
            ))
        else:
            logger.info('txid {0} has been reflected in transaction, nothing to do'.format(trx['txid']))

    except UserWalletTransaction.DoesNotExist:
        with transactin.atomic():
            trans_status = 'PENDING'
            if trx['confirmation'] >= min_trx_confirmation:
                user_wallet = UserWallet.objects.select_for_update().get(pk=user_wallet.id)
                trans_status = 'PROCESSED'
            balance_end = user_wallet.balance + float(trx['amount'])
            available_to_trade_end = user_wallet.available_balance + float(trx['amount'])
            wallet_trans = UserWalletTransaction.objects.create(
                user_wallet = user_wallet,
                balance_begin= user_wallet.balance,
                balance_end = balance_end,
                locked_balance_begin = user_wallet.locked_balance,
                locked_balance_end = user_wallet.locked_balance,
                available_to_trade_begin = user_wallet.available_balance,
                available_to_trade_end = available_to_trade_end,
                reference_order = null,
                reference_wallet_trxId = trx['txid'],
                amount = trx['amount'],
                balance_update_type = 'CREDIT',
                transaction_type = 'DEPOSIT',
                comment = 'User deposit',
                reported_timestamp = trx['timereceived'],
                status = status,
                created_by = operator,
                lastupdated_by = operator
            )
            wallet_trans.save()
            logger.info('Create deposit transaction {0} related to txid {1}'.format(
                  wallet_trans.id,trx['txid']))
            if trx['confirmation'] >= min_trx_confirmation:
                user_wallet.balance = balance_end
                user_wallet.available_balance = available_to_trade_end
                user_wallet.user_wallet_trans_id = wallet_trans.id
                user_wallet.lastupdated_by = operator
                user_wallet.save()
                logger.error('Update user wallet balance for user id {0} address {1} related to txid {2}'.format(
                    user_wallet.user.id, user_wallet.address, trx['txid']))

    except UserWalletTransaction.MultipleObjectsReturned:
         logger.error('There are more than one transaction related to txid {0} for user id {1} on receiving address {2}'.format(
             trx['txid'], user_wallet.user.id, user_wallet.address))

def update_account_balance_with_wallet_trx(crypto, wallet_account_name, lookback_count, min_trx_confirmation):
    # prepare the data for sysop, which will be the created_by and last
    # updated by
    operator = UserLogin.objects.get(pk='sysop')

    # get all user's Wallets
    user_wallets = UserWallet.objects.filter(user is not None, wallet__cryptocurrency__currency_code=crypto)

    # build a lookup table based on user's wallet receiving address
    # so that we can create new trx entry for the user account
    wallet_lookup = {}

    for wallet in user_wallets:
        if wallet.wallet_addr not in wallet_lookup:
           wallet_lookup.add(wallet.wallet_addr, wallet)
           """entry.latest_trxId = wallet.last_wallet_trxId
           entry.origin_timestamp = wallet.last_wallet_timestamp
           entry.accumulated_amount = wallet.balance
           wallet_lookup.add(wallet.wallet_addr, entry)"""
        else:
           raise ValueError('address {0} should not have more than one entry in userwallets'.format(wallet.wallet_addr))

    # get all past 10000 transactions in wallet
    trans = axfd_utils.axfd_listtransactions(wallet_account_name, lookback_count)
    for trx in trans:
        # only process confirmed wallet transactions
        if trx['category'] == 'receive':
            if trx['address'] in wallet_lookup.keys:
                entry = wallet_lookup[trx.address]
                update_user_wallet_based_on_deposit(
                      trx, entry, min_trx_confirmation, operator)
            else:
                logger.error('Encounter transaction related to address {0} which does not belong to any user'.format(trx['address']))
        elif trx['category'] == 'send':
            if trx['address'] in wallet_lookup.keys:
                entry = wallet_lookup[trx.address]
                update_user_wallet_based_on_deposit(
                      trx, entry, min_trx_confirmation, operator)
            else:
                logger.error('Encounter transaction related to address {0} which does not belong to any user'.format(trx['address']))

def get_user_accountInfo(userid, crypto):
    logger.info("get account info for user {0} in {1}".format(userid, crypto))
    user = User.objects.get(pk=userid)
    userwallet = UserWallet.objects.get(user__id= userid, wallet__cryptocurrency__currency_code=crypto)
    balance = userwallet.balance
    available_balance = userwallet.available_balance
    locked_balance = userwallet.locked_balance
    receiving_addr = userwallet.wallet_addr
    userpayments = UserPaymentMethod.objects.filter(user__id=userid)
    external_addresses = UserExternalWalletAddress.objects.filter(user__id= userid).filter(cryptocurrency__currency_code=crypto)
    externaladdr = None
    if external_addresses:
       logger.info('Found the external address record for user {0} with {1}'.format(userid, crypto))
       record = external_addresses[0]
       externaladdr = UserExternalWalletAddressInfo(record.id, record.user.id,
           record.address, record.alias, record.cryptocurrency.currency_code)
    else:
       logger.info('There is no external address for user {0} with {1}'.format(userid, crypto))
    payment_methods= []
    if userpayments:
       logger.info('User {0} has setup payment methods'.format(userid))
       for method in userpayments:
          payment_methods.append(UserPaymentMethodView(method.id,
                user.id, method.provider.code,
                method.provider.name,method.account_at_provider,
                method.provider_qrcode_image))
    userInfo = UserAccountInfo(user.login, user.id,
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
        record.address, record.alias,record.cryptocurrency.currency_code)

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
