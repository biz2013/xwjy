#!/usr/bin/python
# -*- coding: utf-8 -*-
import json, logging
from walletgui.models import *

logger = logging.getLogger("site.paymentmethodmanager")

class PaymentMethodManager(object):

    @staticmethod
    def get_payment_method(username):
        try:
            return UserPaymentMethod.objects.get(user__username=username)
        except UserPaymentMethod.DoesNotExist:
            logger.info("get_payment_method({0}): user has not setup any payment method".format(username))
            return None
        except UserPaymentMethod.MultipleObjectsReturned:
            raise ValueError("get_payment_method({0}) has more than one entry returned".format(username))
