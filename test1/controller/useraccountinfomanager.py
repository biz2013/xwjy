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

logger = logging.getLogger(__name__)

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
    user = User.objects.get(pk=userid)
    userwallets = UserWallet.objects.filter(user__id= userid).filter(wallet__cryptocurrency__currency_code=crypto)
    available_balance = 0.0
    locked_balance = 0.0
    balance = 0.0
    receiving_addr = ''
    if (len(userwallets) == 1):
        wallet_obj = userwallets[0]
        balance = wallet_obj.balance
        available_balance = wallet_obj.available_balance
        locked_balance = wallet_obj.locked_balance
        receiving_addr = wallet_obj.wallet_addr
    elif len(userwallets) == 0:
        raise ValueError('There not userwallet for userid {0} crypto {1}'.format(userid, crypto))
    else:
        raise ValueError('There should just be one userwallet for userid {0} crypto {1} but there are {2}'.format(
         userid, crypto, len(userwallets)
        ))
    userpayments = UserPaymentMethod.objects.filter(user__id=userid)
    external_addresses = UserExternalWalletAddress.objects.filter(user__id= userid).filter(cryptocurrency__currency_code=crypto)
    external_address_str = None
    external_address_alias = None
    if len(external_addresses) > 0:
       entrternal_address_object = external_addresses[0]
       external_address_str =  external_address_object.address
       external_address_alias = external_address_object.alias
    payment_methods= []
    if userpayments is not None:
       for method in userpayments:
          payment_methods.append(UserPaymentMethodView(method.id, method.provider.code,
                method.provider.name,method.account_at_provider,
                method.provider_qrcode_image))
    userInfo = UserAccountInfo(user.login, user.id,
          balance,
          locked_balance,
          available_balance,
          receiving_addr,
          external_address_str,
          external_address_alias,
          payment_methods)
    return userInfo
