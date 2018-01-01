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

logger = logging.getLogger("site.redeemmanager")

def redeem(command, operator):
    operatorObj = UserLogin.objects.get(pk=operator)
    operation_comment = 'User (id:{0}) redeem {1}'.format(command.userid,
             command.amount)
    txid = axfd_utils.sendtoaddress(command.toaddress, command.amount,
        operation_comment)
    with transaction.atomic():
        userwallet = UserWallet.objects.select_for_update().get(user__id=userid,
             wallet__cryptocurrency__currency_code=command.crypto)
        userwallet_trans = UserWalletTransaction.objects.create(
          user_wallet = userwallet,
          balance_begin = userwallet.balance,
          balance_end = userwallet.balance - command.amount,
          locked_balance_begin = userwallet.locked_balance,
          locked_balance_end = userwallet.locked_balance,
          available_to_trade_begin = userwallet.available_balance,
          available_to_trade_end = userwallet.available_balance - command.amount,
          reference_order = None,
          reference_wallet_trxId = txid,
          amount = command.amount,
          balance_update_type= 'DEBT',
          transaction_type = 'REDEEM',
          comment = operation_comment,
          #TODO: need to get the transaction and its timestamp
          reported_timestamp = 0,
          #TODO: need to make it PENDING, if the transaction's confirmation
          # has not reached the threshold
          status = 'PROCESSED',
          created_by = operatorObj,
          lastupdated_by = operatorObj
        )
        userwallet_trans.save()
        userwallet.user_wallet_trans_id = userwallet_trans.id
        userwallet.balance = userwallet.balance - command.amount
        userwallet.available_balance = userwallet.available_balance - command.amount
        userwallet.save()
