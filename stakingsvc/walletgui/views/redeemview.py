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
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.balance")

@login_required
def show(request):
    try:
        if request.method == POST:
            amount = float(request.POST["amount"]) if request.POST["amount"] else 0
            crypto_util = WalletManager.create_fund_util('CNY')
            wallet = WalletManager.get_wallet_balance(crypto_util, request.user.username, 'CNY')
            userpayment = PaymentMethodManager.get_payment_method(request.user.username)
            if not userpayment:
                messages.error("请设置付款方式，再充值")
                return redirect('balance')
            useraccountInfo = UserAccountInfo(request.user.id,
                wallet.balance, wallet.locked_balance, wallet.available_balance,
                wallet.wallet_addr, None, [ userpayment ])
            return render(request, 'walletgui/redeem_investment.html',
                {'account': useraccountInfo, 'amount': amount})
        else:
            raise ValueError('提现界面只接收POST请求')
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def redeem(request):
    pass