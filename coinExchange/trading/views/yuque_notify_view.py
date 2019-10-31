#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json, sys

from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from tradeex.client.apiclient import APIClient
from tradeex.controllers.apiusertransmanager import APIUserTransactionManager
from trading.config import context_processor
from trading.controller.global_constants import *
from trading.controller.heepaymanager import *
from trading.controller import ordermanager
from trading.views import errorpageview

from tradeex.data.tradeapiresponse import TradeAPIResponse
logger = logging.getLogger("site.yuque_confirm")


# This is the handler of notification from heepay
# If it is POST, it can only return 'ok' or 'error'
#
@csrf_exempt
def yuque_confirm_payment(request):
    try:
        if request.method == 'POST':
            json_data = json.loads(request.body.decode('utf-8'))
            logger.info("Receive async payment notification from yuque API: {0}".format(
                json.dumps(json_data, ensure_ascii=False)
            ))
            return HttpResponse(content='OK')
        else:
        return HttpResponseNotAllowed
    except Exception as e:
        error_msg = 'Confirmation processing hit exception: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        if request.method == 'GET':
            return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
               '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
        else:
            return HttpResponseNotAllowed(['POST'])


