#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import math
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
from trading.controller.global_constants import *

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

def redeem(command, operator, axfd_tool):
    if not check_send_to_address(command.crypto, command.toaddress):
        raise ValueError("提币地址不可以是交易平台注入地址");
    logger.info('[{0}] about redeem: amount {1} to {2}'.format(
              operator, command.amount, command.toaddress)
    )
    operatorObj = User.objects.get(username=operator)
    with transaction.atomic():
        userwallet = UserWallet.objects.select_for_update().get(
             user__username=operator,
             wallet__cryptocurrency__currency_code=command.crypto)
        logger.info('[{0}] before redeem userwallet {1} has balance: {2} locked: {3} available: {4}'.format(
               operator, userwallet.id, userwallet.balance, userwallet.locked_balance, userwallet.available_balance))

        #
        # Now first check whether balance exceed available amount
        #
        if command.amount - userwallet.available_balance > 0:
            errMsg = '{0}: [{1}] try to redeem {2} from userwallet [{3}] which has available balance of {4}'.format(
                       VE_REDEEM_EXCEED_LIMIT, operator, command.amount, userwallet.id, userwallet.available_balance)
            raise ValueError(errMsg)

        #
        # Then test whether balance=locked+available
        #
        diff = math.fabs(userwallet.balance - userwallet.locked_balance - userwallet.available_balance)
        if diff > 0.00000001:
            errMsg = "{0}: [{1}] userwallet [{2}] has unmatch balance: balance: {3} locked {4} available {5} diff {6}".format(
                     VE_ILLEGAL_BALANCE, operator, userwallet.id, userwallet.balance, userwallet.locked_balance, userwallet.available_balance, diff)
            raise ValueError(errMsg)

        #
        # Now issue wallet command to redeem
        #
        axfd_tool.unlock_wallet(15)
        operation_comment = 'UserId:{0},redeem:{1},to:{2}'.format(
               command.userid, command.amount, command.toaddress)
        trx = axfd_tool.send_fund(command.toaddress, command.amount, operation_comment)
        txid = trx['txid']
        fee = math.fabs(trx['fee'])

        logger.info("passed the redeem coins")

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

        #
        # put redeem fund as locked fund, reduce available balance, and check whether it is
        # still valid (this check is kind of paranoid
        #
        userwallet.locked_balance = userwallet.locked_balance + command.amount + fee
        userwallet.available_balance = userwallet.available_balance - command.amount - fee
        diff = math.fabs(userwallet.balance - userwallet.locked_balance - userwallet.available_balance)
        if diff > 0.00000001:
            errMsg = "{0}: [{1}] userwallet [{2}] has unmatch balance after redeem: balance: {3} locked {4} available {5} diff {6}".format(
                     VE_ILLEGAL_BALANCE, operator, txid, userwallet.balance, userwallet.locked_balance, userwallet.available_balance, diff)
            raise ValueError(errMsg)

        userwallet.lastupdated_at = dt.datetime.utcnow()
        userwallet.lastupdated_by = operatorObj
        userwallet.save()
