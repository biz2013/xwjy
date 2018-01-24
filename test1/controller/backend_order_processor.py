#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz
import logging
from calendar import timegm

from django.db import transaction
from django.db.models import F, Q, Count
from django.contrib.auth.models import User

from users.models import *
from views.models.orderitem import OrderItem
from views.models.userpaymentmethodview import *

logger = logging.getLogger("site.backend_order_processor")

def cancelPurchaseOrder(orderid, operator):
    pass


def confirmPurchaseOrder(orderid, operator):
    pass

def get_unfilled_purchase_orders():
    return Orders.objects.filter(Q(status='PAYING') |\
       Q(status='PAID' | Q(status='OPEN')).order_by('-lastupdated_at')
