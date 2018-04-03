#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from tradeex.models import APIUserAccount

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

        
