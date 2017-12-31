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
        if trx['confirmations'] >= min_trx_confirmations:
           if trx['category'] == 'receive':
              if trx['address'] in wallet_lookup.keys:
                 entry = wallet_lookup[trx.address]
                 user_trans_count = UserWalletTransaction.objects.filter(
                     user_wallet__user__id=entry.user.id,
                     user_wallet__wallet_addr=entry.wallet_addr,
                     reference_wallet_trxId=trx['txid']).count()
                 # if this is new transactin id, then create an credit trans
                 # to UserWalletTransaction
                 if user_trans_count == 0:
                     with transactin.atomic():
                         user_wallet = UserWallet.objects.select_for_update().get(pk=entry.id)
                         balance_end = user_wallet.balance + trx['amount']
                         available_to_trade_end = user_wallet.available_balance + trx['amount']
                         UserWalletTransaction.objects.create(
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
                            status = 'PROCESSED',
                            created_by = operator,
                            lastupdated_by = operator
                         )
                         user_wallet.balance = balance_end
                         user_wallet.available_balance = available_to_trade_end
                         user_wallet.save()
                 elif user_trans_count > 1:
                     logger.error('There are more than one transaction related to txid {0} for user id {1} on receiving address {2}'.format(
                         trx['txid'], entry.userid, entry.address))
                 else:
                     pass

              else:
                 logger.error('Encounter transaction related to address {0} which does not belong to any user'.format(trx['address']))
        else:
           if trx['category'] == 'send':
              if int(dt.datetime.utcnow().timestamp()) - trx['timereceived'] >= 24 * 3600:
                 logger.error('Wallet redeem txid {0} has not had {1} confirmation after more than a day'.format(trx['txid'], min_trx_confirmation))

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
