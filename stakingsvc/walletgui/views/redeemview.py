#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from walletgui.views import errorpageview
from walletgui.controller.global_constants import *
from walletgui.controller.walletmanager import WalletManager
from walletgui.controller.paymentmethodmanager import PaymentMethodManager
from walletgui.views.models.useraccountinfo import *
from walletgui.views.models.userpaymentmethod import *
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.balance")

@login_required
def show(request):
    try:
        if request.method == "POST":
            amount = float(request.POST["amount"]) if request.POST["amount"] else 0
        else:
            amount = 0

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
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

@login_required
def redeem(request):
    try:
        if request.method == "POST":
            amount = float(request.POST["amount"]) if request.POST["amount"] else 0
            crypto_util = WalletManager.create_fund_util('CNY')
            if math.fabs(amount) < 0.02:
                messages.error(request, '提现数量不可两份钱')
                return redirect(request, 'show_redeem')
            try:
                api_user =  APIUserAccount.objects.get(user__username=request.user.username)
            except APIUserAccount.DoesNotExist:
                raise ValueError(ERR_USER_NOT_FOUND_BASED_ON_APPID)
            except APIUserAccount.MultipleObjectsReturned:
                raise ValueError(ERR_MORE_THAN_ONE_USER_BASED_ON_APPID)

            try:
                userpaymentmethod = UserPaymentMethod.objects.get(
                    user__id = api_user.user.id)
            except UserPaymentMethod.DoesNotExist:
                raise ValueError(ERR_PAYMENTMETHOD_NOT_FOUND)
            except UserPaymentMethod.MultipleObjectsReturned:
                raise ValueError(ERR_MORE_THAN_ONE_PAYMENTMETHOD_FOUND)

            out_trade_no = str(uuid.uuid4())
            request_obj = TradeAPIRequest(
                    API_METHOD_REDEEM,
                    api_user.apiKey,
                    api_user.secretKey,
                    out_trade_no, # order id
                    None, # trx _id
                    (int)(amount * 100), # total fee
                    settings.TRADE_API_CALL_TIMEOUT_IN_MINUTES, # expire_minute
                    userpaymentmethod.provider.code,
                    userpaymentmethod.account_at_provider,
                    '127.0.0.1', #client ip
                    subject='Staking提现请求 {0}'.format(amount),
                    notify_url=None,
                    return_url=None)

            url = TRADE_API_PURCHASE_URL_TEMPLATE.format(settings.TRADE_API_HOST)
            api_client = APIClient(url)
            resp_json = api_client.send_json_request(request_obj.getJsonPayload())
            if resp_json["return_code"] != 'SUCCESS':
                logger.error('redeem(): get failure api response: {0}'.format(json.dumps(resp_json, ensure_ascii=False)))
                errmsg = '提现请求遇到问题：{0}'.format(resp_json["return_code"])
                if 'result_msg' in resp_json:
                    errmsg = '{0}-{1}'.format(errmsg, resp_json['result_msg'])
                messages.error(request, errmsg)
                return redirect('balance')
            else:
                messages.success(request, '提现请求已经成功，请注意收款')
                return redirect('balance')

        else:
            raise ValueError("提现请求必须是POST请求")    
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
    