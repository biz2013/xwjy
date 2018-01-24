#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.contrib import messages
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.global_constants import *
from controller.global_utils import *
from controller import ordermanager
from controller import useraccountinfomanager

from views.models.orderitem import OrderItem
from views.models.returnstatus import ReturnStatus
from views import errorpage
from django.contrib.auth.decorators import login_required


logger = logging.getLogger("site.order_batch_process")

def order_batch_process(request):
    pass
