#!/usr/bin/python
# -*- coding: utf-8 -*-
import json, logging
from trading.models import Wallet
from tradeex.controllers.crypto_utils import CryptoUtility

logger = logging.getLogger("tradeex.walletmanager")

class WalletManager(object):

    @staticmethod
    def create_fund_util(crypto):
        try:
            wallet = Wallet.object.get(cryptocurrency__code=crypto)
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