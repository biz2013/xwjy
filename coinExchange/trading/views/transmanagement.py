#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from trading.models import *
from trading.controller import useraccountinfomanager, userpaymentmethodmanager
from trading.controller.global_constants import *
from trading.controller.global_utils import *
from trading.views.models.returnstatus import ReturnStatus
from trading.views import errorpageview
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.accountinfo")

@login_required
def gettrans(request):
    try:
       useraccountInfo = useraccountinfomanager.get_user_accountInfo(request.user,'AXFund')
       weixin, weixin_payment_image, weixin_shop_assistant_image = userpaymentmethodmanager.load_weixin_info(request.user)
       request.session[REQ_KEY_USERACCOUNTINFO] = useraccountInfo.tojson()
       return render(request, 'trading/admin/transmanagement.html', 
              {'useraccountInfo': useraccountInfo,
               REQ_KEY_USERNAME: request.user.username,
               'weixin':weixin,
               'weixin_payment_image': weixin_payment_image, 
               'weixin_shop_assistant_image': weixin_shop_assistant_image}
               'buyorders' : {})
    except Exception as e:
       error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
