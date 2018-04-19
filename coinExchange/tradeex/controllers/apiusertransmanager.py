#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, logging
import datetime as dt

from tradeex.models import APIUserTransaction
from trading.models import User

logger = logging.getLogger("tradeex.apiusertransmanager")

class APIUserTransactionManager(object):
    @staticmethod
    def get_trans_by_reference_order(orderId):
        try:
            return APIUserTransaction.objects.get(reference_order__order_id=orderId)           
        except APIUserTransaction.DoesNotExist:
            logger.error("get_trans_by_reference_order: Failed to find api_user for reference order {0}".format(orderId))
            raise ValueError('USER_NOT_FOUND_WITH_ORDERID')
        except APIUserTransaction.MultipleObjectsReturned:
            logger.error("get_trans_by_reference_order: Find mutiple APIUserTransaction for reference order {0}".format(orderId))
            raise ValueError('MORE_THAN_ONE_APIUSERTRANSACT')
    
    @staticmethod
    def update_notification_status(trx_id, notify, notify_resp, comment):
        try:
            if not APIUserTransaction.objects.filter(
               transactionId= trx_id).update(
               last_notify = notify,
               last_notify_response = notify_resp,
               last_notified_at = dt.datetime.utcnow(),
               last_status_description = comment,
               lastupdated_by = User.objects.get(username='admin'),
               lastupdated_at = dt.datetime.utcnow()):
               logger.error("update_notification_status({0}, ..., {1}, {2}: did not update".format(trx_id, notify_resp, comment))
        except:
            logger.error("update_notification_status: Hit exception {0}".format(sys.exc_info()))
                    
    @staticmethod
    def update_status_info(trx_id, comment):
        try:
            if not APIUserTransaction.objects.filter(
               transactionId= trx_id).update(
               last_status_description = comment,
               lastupdated_by = User.objects.get(username='admin'),
               lastupdated_at = dt.datetime.utcnow()):
               logger.error("update_status_info({0}, {1}): did not update".format(trx_id, comment))
        except:
            logger.error("update_status_info({0}, {1}): Hit exception {2}".format(trx_id, comment,sys.exc_info()))
        

        
