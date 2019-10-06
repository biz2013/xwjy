#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
from django.http.response import HttpResponse, HttpResponseNotAllowed,HttpResponseBadRequest,HttpResponseNotFound,HttpResponseServerError
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from trading.controller.heepaymanager import HeePayManager
from trading.controller.global_utils import *

# this is for test UI. A fake one
from trading.controller.global_constants import *
from trading.controller import userpaymentmethodmanager
from trading.models import *
from tradeex.models import *
from trading.views.models.userpaymentmethodview import *
from trading.views.models.orderitem import OrderItem
from trading.views.models.returnstatus import ReturnStatus
from trading.views import errorpageview
from django.contrib.auth.decorators import login_required

import hashlib
import hmac

# logger for user registration
logger = logging.getLogger("site.testpaymentqrcode")

def validate_signature(api_key, externaluserId, secret, original_signature):
    str_to_be_signed = 'api_key={0}&externaluserId={1}&secret={2}'.format(api_key, externaluserId, secret)
    m = hashlib.md5()
    m.update(str_to_be_signed.encode('utf-8'))
    signature = m.hexdigest()
    logger.debug("sign_api_content(): str to be signed {0} with signature {1} and original signature {2}".format(
        str_to_be_signed, signature, original_signature))
    return signature == original_signature

def testpaymentqrcode(request):
    # TO DO: pass down request.user to controller.
    err_msg = {}
    try:
        if request.method == 'GET':
            if 'api_key' not in request.GET:
                err_msg['status'] = 'ERROR_MISSING_API_KEY'
                err_msg['message'] = '你的请求没有包含API KEY'
                return HttpResponseBadRequest(json.dumps(err_msg, ensure_ascii=False))

            api_key = request.GET['api_key']
            externaluserId = request.GET['externaluserId']
            auth_token = request.GET['auth_token']
            auth_check_url = request.GET['auth_check_url']
            signature = request.GET['signature']
            secret = None
            try:
                api_account = APIUserAccount.objects.get(apiKey=api_key)
                secret = api_account.secretKey
            except APIUserAccount.DoesNotExist:
                err_msg['status'] = 'ERROR_API_KEY_NOTFOUND'
                err_msg['message'] = '你的请求中的API KEY不存在'
                return HttpResponseNotFound(json.dumps(err_msg, ensure_ascii=False))

            if not validate_signature(api_key, externaluserId, secret, signature):
                err_msg['status'] = 'ERROR_SIGNATURE_NOTMATCH'
                err_msg['message'] = '你的请求签名不符'
                return HttpResponseBadRequest(json.dumps(err_msg, ensure_ascii=False))

            user_payment_methods = userpaymentmethodmanager.get_user_payment_methods(request.user.id)
            return render(request, 'trading/paymentmethod/qrcode_client.html',
            {  'user_payment_methods':user_payment_methods,
            'api_key': api_key,
            'auth_token': auth_token,
            'auth_check_url': auth_check_url,
            'externaluserId': externaluserId,
            'key': secret,
            'signature': signature,
            'payment_proxy': settings.QRCODE_TEST_PAYMENTPROXY
            })
        else:   
            return HttpResponseNotAllowed(['GET'])
    except Exception as e:
       error_msg = 'testpaymentqrcode'
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

