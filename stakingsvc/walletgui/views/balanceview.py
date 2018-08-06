#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from walletgui.confit import context_processor
from walletgui.views import errorpageview
from walletgui.controller.global_constants import *
from walletgui.views.models.useraccountinfo import *
from walletgui.views.models.userpaymentmethod import *
from django.contrib.auth.decorators import login_required


import logging,json

logger = logging.getLogger("site.balance")

@login_required
def func(request):

@login_required
def balance(request):paymentmethods = []
        paymentmethods.append(
          UserPaymentMethodView(1, 1, 'heepay', '汇钱包', '15910978598')
        )
        useraccountInfo = UserAccountInfo(1, 1000.0, 1000.0, 0.0,
            'AXjtBn93Y8Yti6LXWQqwkrF1pHcBRGYEDu', None, paymentmethods)
        sitesettings = context_processor.settings(request)['settings']
        master_wallet_known = sitesettings.api_cny_master_wallet_addr is not None and len(sitesettings.api_cny_master_wallet_addr) > 0
        return render(request, 'walletgui/balance.html',
                  {'account': useraccountInfo,
                   'master_wallet_known': master_wallet_known})
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
