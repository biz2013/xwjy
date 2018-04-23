#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from tradeex.models import APIUserAccount
from trading.models import UserExternalWalletAddress

logger = logging.getLogger("tradeex.apiusermanager")

class APIUserManager(object):
    @staticmethod
    def get_api_user_by_apikey(apikey):
        try:
            return APIUserAccount.objects.get(apiKey=apikey)
        except APIUserAccount.DoesNotExist:
            logger.error("Failed to find api_user for apikey {0}".format(apikey))
            raise ValueError('USER_NOT_FOUND_WITH_API_KEY')
        except APIUserAccount.MultipleObjectsReturned:
            logger.error("Multiple account has the same apikey {0}".format(apikey))
            raise ValueError('MORE_THAN_ONE_USER_WITH_API_KEY')

    @staticmethod
    def get_api_user_external_crypto_addr(userId, crypto):
        try:
            externalobj = UserExternalWalletAddress.objects.get(user__id = userId, cryptocurrency__code = crypto)
            return externalobj.address
        except UserExternalWalletAddress.DoesNotExist:
            logger.warn("get_api_user_external_crypto_addr: Failed to find external address for user {0} crypto {1}".format(userId, crypto))
            return None
        except UserExternalWalletAddress.MultipleObjectsReturned:
            logger.error("get_api_user_external_crypto_addr: Multiple address for user {0} crypto {1}".format(userId, crypto))
            raise ValueError('MORE_THAN_ONE_USER_EXTERNALADDR')
            

