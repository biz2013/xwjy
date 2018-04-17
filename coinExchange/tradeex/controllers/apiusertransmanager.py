#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from tradeex.models import APIUserTransaction

logger = logging.getLogger("tradeex.apiusertransmanager")

class APIUserTransactionManager(object):
    @staticmethod
    def get_trans_by_reference_order(orderId):
        try:
            return APIUserTransaction.objects.get(reference_order__order_id=orderId)           
        except APIUserTransaction.DoesNotExist:
            logger.error("Failed to find api_user for reference order {0}".format(orderId))
            raise ValueError('USER_NOT_FOUND_WITH_ORDERID')
        except APIUserTransaction.MultipleObjectsReturned:
            logger.error("Find mutiple APIUserTransaction for reference order {0}".format(orderId))
            raise ValueError('MORE_THAN_ONE_APIUSERTRANSACT')

        
