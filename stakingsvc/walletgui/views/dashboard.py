#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging, sys
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from walletgui.controller.global_constants import *
from walletgui.controller.crypto_utils import CryptoUtility
from walletgui.controller.walletmanager import WalletManager
from walletgui.views import errorpageview

logger = logging.getLogger("site.dashboard")

@login_required
def show(request):
    try:
        crypto_util = WalletManager.create_fund_util('CNY')
        wallet = WalletMAnager.get_wallet_balance(crypto_util, request.user.username, 'CNY')
        userpaymentmethod = PaymentMethodManager.get_payment_method(request.user.username)
        useraccountInfo = UserAccountInfo(request.user.id,
            wallet.balance, wallet.locked_balance, wallet.available_balance,
            wallet.wallet_addr, None, [ userpaymentmethod ])
        return render(request, 'walletgui/balance.html',
            {'account': useraccountInfo })
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

