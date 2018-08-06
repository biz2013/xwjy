#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sys
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from walletgui.controller.global_constants import *
from walletgui.controller.crypto_utils import CryptoUtility
from walletgui.controller.walletmanager import WalletManager
from walletgui.controller.paymentmethodmanager import PaymentMethodManager
from walletgui.views import errorpageview
from walletgui.views.models.useraccountinfo import *

logger = logging.getLogger("site.dashboard")

@login_required
def create(request):
    try:
        return render(request, 'walletgui/balance.html',
            {'account': None, 'userpaymentmethod': None })
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

def edit(request):
    try:
        return render(request, 'walletgui/balance.html',
            {'account': None, 'userpaymentmethod': None })
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

def delete(request):
    try:
        return render(request, 'walletgui/balance.html',
            {'account': None, 'userpaymentmethod': None })
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
