#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging

from django.db import transaction
from django.db.models import F
from django.contrib.auth.models import User

from users.models import *
from config import context_processor
from controller import axfd_utils
from views.models.useraccountinfo import *
from views.models.userpaymentmethodview import *
from views.models.userexternalwalletaddrinfo import *

logger = logging.getLogger("site.redeemmanager")

def check_send_to_address(crypto, address):
    try:
        userwallet = UserWallet.objects.get(wallet_addr = address,
         wallet__cryptocurrency__currency_code=command.crypto)
        return False
    except UserWallet.DoesNotExist:
        return True
    except UserWallet.MultipleObjectsReturned:
        return False
def redeem(command, operator, txid, fee, operation_comment):
    if not check_send_to_address(command.crypto, command.toaddress):
        raise ValueError("提币地址不可以是交易平台注入地址");
    operatorObj = User.objects.get(username=operator)
    with transaction.atomic():
        userwallet = UserWallet.objects.get(user__username=operator,
             wallet__cryptocurrency__currency_code=command.crypto)
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

        UserWallet.objects.filter(id=userwallet.id).update(
          locked_balance = F('locked_balance') + command.amount + fee,
          available_balance = F('available_balance') - command.amount - fee,
          lastupdated_at = dt.datetime.utcnow(),
          lastupdated_by = operatorObj
        )
