#!/usr/bin/python
# -*- coding: utf-8 -*-
import json, logging

from django.conf import settings
from tradeapi.apiclient import APIClient
from walletgui.controller.paymentmethodmanager import PaymentMethodManager
from walletgui.models import *

TRADE_API_USER_URL_TEMPLATE="http://{0}/api/v1/apiuser/"

class APIUserManager(object):

    @staticmethod
    def create_api_user_account(username, crypto):
        try:
            loginuser = User.objects.get(username=username)
            userpaymentmethod = PaymentMethodManager.get_payment_method(username)
            if not userpaymentmethod:
                raise ValueError(ERR_NO_PAYMENTMETHOD)

            userwallet = UserWallet.objects.get(wallet__cryptocurrency__currency_code=crypto,
               user__username=username)
            
            request_json = {}
            request_json['username'] = loginuser.username
            request_json['email'] = loginuser.email
            request_json['payment_provider'] = userpaymentmethod.provider.code 
            request_json['payment_account'] = userpaymentmethod.account_at_provider
            request_json['external_cny_addr'] = userwallet.wallet_addr

            url = TRADE_API_USER_URL_TEMPLATE.format(settings.TRADE_API_HOST)
            api_client = APIClient(url)
            resp_json = api_client.send_json_request(request_json)
            if resp_json["result"].upper() != 'OK':
                logger.error('create_api_user_account({0},{1}): get failure api response: {2}'.format(
                    username, crypto, json.dumps(resp_json, ensure_ascii=False),
                    ))
                errmsg = '开户请求遇到问题：{0}'.format(esp_json["return_code"])
                if 'result_msg' in resp_json:
                    errmsg = '{0}-{1}'.format(errmsg, resp_json['result_msg'])
                raise ValueError(errmsg)
            
            APIUserAccount.objects.create(
                user = loginuser,
                apiKey = resp_json['apiKey'],
                secretKey = resp_json['secretKey'],
                accountNo = resp_json['accountNo'],
                lastupdated_by = loginuser,
                created_by = loginuser,
            ).save()

            return APIUserAccount.objects.get(user__username=username)
        except UserWallet.DoesNotExist:
            raise ValueError('There is no userwallet for the user')

