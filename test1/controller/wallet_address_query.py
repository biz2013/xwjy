#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging

from django.db.models import Count
from django.db import transaction

from users.models import *

logger = logging.getLogger("site.wallet_address_query")

def get_unassigned_userwallets_count():
    return UserWallet.objects.filter(user__isnull=True).count()

def create_user_wallets(addresses, crypto, operator):
    walletObj = Wallet.object.get(cryptocurrency__currency_code = crypto)
    operatorObj = User.object.get(username=operator)
    with transaction.atomic():
        for addr in addresses:
            UserWallet.object.create(
               wallet = walletObj,
               wallet_addr = addr,
               created_by = operatorObj,
               lastupdated_by = operatorObj
            )
