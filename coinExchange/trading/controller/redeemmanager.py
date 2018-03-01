#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging

from django.db import transaction
from django.db.models import F
from django.contrib.auth.models import User

from trading.models import *
from trading.config import context_processor
from trading.controller import axfd_utils
from trading.views.models.useraccountinfo import *
from trading.views.models.userpaymentmethodview import *
from trading.views.models.userexternalwalletaddrinfo import *

logger = logging.getLogger("site.redeemmanager")

def check_send_to_address(crypto, address):
    try:
        userwallet = UserWallet.objects.get(wallet_addr = address,
         wallet__cryptocurrency__currency_code=crypto)
        return False
    except UserWallet.DoesNotExist:
        return True
    except UserWallet.MultipleObjectsReturned:
        return False
def redeem(command, operator, txid, fee, operation_comment):
    if not check_send_to_address(command.crypto, command.toaddress):
        raise ValueError("提币地址不可以是交易平台注入地址");
    logger.info('[{0}][txid: {1}] about to create DB record for redeem: amount {2} fee {3} to {4}'.format(
              operator, txid, command.amount, fee, command.toaddress)
    )
    operatorObj = User.objects.get(username=operator)
    with transaction.atomic():
        userwallet = UserWallet.objects.select_for_update().get(
             user__username=operator,
             wallet__cryptocurrency__currency_code=command.crypto)
        balance_begin = userwallet.balance
        locked_begin = userwallet.locked_balance
        available_begin = userwallet.available_balance
        logger.info('[{0}][txid: {1}] before create redeem record, userwallet {2} has balance: {3} locked: {4} available: {5}'.format(
               operator, txid, balance_begin, locked_begin, available_begin))
        
        userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = userwallet,
          reference_order = None,
          reference_wallet_trxId = txid,
          units = command.amount,
          balance_update_type= 'DEBT',
          transaction_type = 'REDEEM',
          comment = operation_comment,
          #TODO: need to get the transaction and its timestamp
          reported_timestamp = 0,
          status = 'PENDING',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
        userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = userwallet,
          reference_order = None,
          reference_wallet_trxId = txid,
          units = fee,
          balance_update_type= 'DEBT',
          transaction_type = 'REDEEMFEE',
          comment = operation_comment,
          #TODO: need to get the transaction and its timestamp
          reported_timestamp = 0,
          status = 'PENDING',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )

        userwallet.locked_balance = locked_begin + command.amount + fee
        userwallet.available_balance = available_begin - command.amount - fee
        UserWallet.objects.filter(id=userwallet.id).update(
          locked_balance = F('locked_balance') + command.amount + fee,
          available_balance = F('available_balance') - command.amount - fee,
          lastupdated_at = dt.datetime.utcnow(),
          lastupdated_by = operatorObj
        )
