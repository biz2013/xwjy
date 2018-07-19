#!/usr/bin/python
# -*- coding: utf-8 -*-
import json, logging
from walletgui.models import *
from walletgui.controller.crypto_utils import CryptoUtility

logger = logging.getLogger("tradeex.walletmanager")

class WalletManager(object):

    @staticmethod
    def update_wallet_balance(crypto_util, username, crypto):
        wallet = UserWallet.objects.select_for_update().get(
            user__username=username, crytocurrency__code=crypto)

        #TODO: later we may need to query transaction and create user_wallet_transaction 
        wallet.balance = crypto_util.get_balance()
        wallet.save()

    @staticmethod
    def get_wallet_balance(crypto_util, username, crypto):
        WalletManager.update_wallet_balance(crypto_util, username, crypto)
        wallet = UserWallet.objects.get(user__username=username, crytocurrency__code=crypto)
        return wallet


    @staticmethod
    def create_fund_util(crypto):
        try:
            wallet = Wallet.objects.get(cryptocurrency__currency_code=crypto)
            if not wallet.config_json:
                logger.error('create_fund_util({0}): the wallet does not have config'.format(crypto))
                raise ValueError('CRYPTO_WALLET_NO_CONFIG')
            return CryptoUtility(json.loads(wallet.config_json))

        except Wallet.DoesNotExist:
            logger.error('create_fund_util({0}): the wallet does not exist'.format(crypto))
            raise ValueError('CRYPTO_WALLET_NOTFOUND')
        except Wallet.MultipleObjectsReturned:
            logger.error('create_fund_util({0}): there are more than one wallets'.format(crypto))
            raise ValueError('CRYPTO_WALLET_NOT_UNIQUE') 
