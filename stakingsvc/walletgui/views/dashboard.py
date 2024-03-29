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
def show(request):
    try:
        crypto_util = WalletManager.create_fund_util('CNY')
        wallet = WalletManager.get_wallet_balance(crypto_util, request.user.username, 'CNY')
        userpayment = PaymentMethodManager.get_payment_method(request.user.username)
        if userpayment:
            logger.info("get user paymentmethod with account {0}".format(userpayment.account_at_provider))
        else:
            logger.info("No user paymentmethod found")
        useraccountInfo = UserAccountInfo(request.user.id,
            wallet.balance, wallet.locked_balance, wallet.available_balance,
            wallet.wallet_addr, None, [ userpayment ])
        return render(request, 'walletgui/balance.html',
            {'account': useraccountInfo, 'userpaymentmethod': userpayment })
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

