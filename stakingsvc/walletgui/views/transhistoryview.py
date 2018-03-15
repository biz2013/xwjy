#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from walletgui.views import errorpageview
from walletgui.controller.global_constants import *
from walletgui.views.models.useraccountinfo import *
from walletgui.views.models.userpaymentmethod import *
#from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.balance")

#@login_required
def show(request):
    try:
       return render(request, 'walletgui/translist_investment.html')
    except Exception as e:
       error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
