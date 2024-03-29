#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from tradeex.data.api_const import *
from tradeex.models import APIUserAccount
from trading.models import UserExternalWalletAddress

logger = logging.getLogger("tradeex.apiusermanager")

class APIUserManager(object):
    @staticmethod
    def get_api_user_by_apikey(apikey):
        logger.debug('get_api_user_by_apikey({0})'.format(apikey))
        try:
            return APIUserAccount.objects.get(apiKey=apikey)
        except APIUserAccount.DoesNotExist:
            logger.error("Failed to find api_user for apikey {0}".format(apikey))
            raise ValueError(ERR_USER_NOT_FOUND_BASED_ON_APPID)
        except APIUserAccount.MultipleObjectsReturned:
            logger.error("Multiple account has the same apikey {0}".format(apikey))
            raise ValueError(ERR_MORE_THAN_ONE_USER_BASED_ON_APPID)

    @staticmethod
    def get_api_user_external_crypto_addr(userId, crypto):
        try:
            externalobj = UserExternalWalletAddress.objects.get(user__id = userId, cryptocurrency__currency_code = crypto)
            return externalobj.address
        except UserExternalWalletAddress.DoesNotExist:
            logger.warn("get_api_user_external_crypto_addr: Failed to find external address for user {0} crypto {1}".format(userId, crypto))
            return None
        except UserExternalWalletAddress.MultipleObjectsReturned:
            logger.error("get_api_user_external_crypto_addr: Multiple address for user {0} crypto {1}".format(userId, crypto))
            raise ValueError('MORE_THAN_ONE_USER_EXTERNALADDR')
            

