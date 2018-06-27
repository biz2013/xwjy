#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys, math, json
import qrcode
import datetime as dt
import pytz

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from tradeapi.apiclient import APIClient
from tradeapi.data.tradeapirequest import TradeAPIRequest
from tradeapi.data.api_const import *
from walletgui.views import errorpageview
from walletgui.controller.global_constants import *
from walletgui.views.models.useraccountinfo import *
from walletgui.views.models.userpaymentmethod import *
from walletgui.models import *
#from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.balance")

def create_api_request(method, api_user, amount, payment_provider_code, payment_account_str):
    frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%_S")
    total_fee = int(amount*100)
    out_trade_no = 'API_TRDNO_{0}'.format(frmt_date)
    return TradeAPIRequest(
        API_METHOD_PURCHASE,
        api_user.apikey, api_user.secretKey,
        out_trade_no,
        total_fee=total_fee,
        expire_minute=settings.TRADE_API_CALL_TIMEOUT_IN_MINUTES,
        payment_provider=payment_provider_code,
        payment_account=payment_account_str,
        client_ip='127.0.0.1', #client ip
        subject='充值请求')


def create_qrcode_image(content, qrcode_filename, base_dir):
    dst = os.path.join(base_dir, 'qrcode', qrcode_filename)
    logger.info('generate qrcode for {0} into {1}'.format(content, dst))
    myQR = qrcode.QRCode(
            version = 1,
            error_correction = qrcode.constants.ERROR_CORRECT_H,
            box_size = 6,
            border = 2,
            )
    myQR.add_data(content)
    img = myQR.make_image()
    img.save(dst)
    img_path = os.path.join('qrcode', qrcode_filename)
    return img_path

@login_required
def purchase(request):
    try:
        if request.method == 'POST':
            amount = float(request.POST["amount"]) if request.POST["amount"] else 0
            payment_provider = request.POST['payment_provider']
            if math.fabs(amount) < 0.00000001:
                messages.error(request, '充值数量不可为零')
                return render(request, 'walletgui/purchase/', { 'amount': amount, 'payment_provider': payment_provider})
            if not payment_provider:
                msessages.error(request, '请选择支付提供商')
                return render(request, 'walletgui/purchase/', { 'amount': amount, 'payment_provider': payment_provider})
            try:
                api_user =  APIUserAccount.objects.get(apikey=settings.MY_APIKEY)
            except APIUserAccount.DoesNotExist:
                raise ValueError(ERR_USER_NOT_FOUND_BASED_ON_APPID)
            except APIUserAccount.MultipleObjectsReturned:
                raise ValueError(ERR_MORE_THAN_ONE_USER_BASED_ON_APPID)

            try:
                paymentmethod = UserPaymentMethod.objects.get(
                    user__id = api_user.user.id, 
                    provider__code = payment_provider)
            except UserPaymentMethod.DoesNotExist:
                raise ValueError(ERR_PAYMENTMETHOD_NOT_FOUND)
            except UserPaymentMethod.MultipleObjectsReturned:
                raise ValueError(ERR_MORE_THAN_ONE_PAYMENTMETHOD_FOUND)

            request_obj = create_api_request(
                API_METHOD_PURCHASE,
                api_user, 
                amount,paymentmethod.provider.code,
                paymentmethod.account_at_provider)

            url = TRADE_API_PURCHASE_URL_TEMPLATE.format(settings.TRADE_API_HOST)
            api_client = APIClient(url)
            resp_json = api_client.send_json_request(request_obj.getPayload())
            if resp_json["return_code"] != 'SUCCESS':
                logger.error('purchase(): get failure api response: {0}'.format(json.dumps(resp_json, ensure_ascii=False)))
                errmsg = '充值请求遇到问题：{0}'.format(esp_json["return_code"])
                if 'result_msg' in resp_json:
                    errmsg = '{0}-{1}'.format(errmsg, resp_json['result_msg'])
                messages.error(errmsg)
            else:
                qrcode_filename = '{0}_{1}.png'.format(
                    resp_json['out_trade_no'], resp_json['trx_bill_no']
                )
                qrcode_img_url_path = create_qrcode_image(
                    resp_json['payment_url'], qrcode_filename, settings.MEDIA_ROOT)
                
                return render(request, 'purchase_qrcode.html', {'qrcode_file': qrcode_img_url_path})
    except Exception as e:
       error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
