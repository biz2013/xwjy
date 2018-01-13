#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.test_model_manager import ModelManager
from users.models import *
from controller import useraccountinfomanager
from controller.global_constants import *
from controller.global_utils import *
from views.models.returnstatus import ReturnStatus
from views import errorpage
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.accountinfo")

@login_required
def accountinfo(request):
    try:
#       if !request.user.is_authenticated()

       useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
       request.session[REQ_KEY_USERACCOUNTINFO] = useraccountInfo.tojson()
       return render(request, 'html/myaccount.html', {'useraccountInfo': useraccountInfo,
                     REQ_KEY_USERNAME: request.user.username})
    except Exception as e:
       error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
