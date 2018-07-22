#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from walletgui.controller.apiusermanager import APIUserManager

import logging,json

from walletgui.models import *

logger = logging.getLogger("tradeex.apiuser")

@csrf_exempt
def register(request):
    try:
        user = User.objects.get(id=2)
        APIUserManager.create_api_user_account(user.username, 'CNY')
        api_user = APIUserAccount.objects.get(user__username=username)
        response_json = {}
        response_json["result"] = 'ok'
        response_json["apiKey"] = api_user.apiKey
        response_json["secretKey"] = api_user.secretKey
        response_json["accountNo"] = api_user.accountNo    
        return JsonResponse(response_json)
    except ValueError as ve:
        logger.error('Create test user has issue {0}'.format(ve.args[0]))
        response_json={}
        response_json["result"] = 'error'
        response_json["resulet_msg"] = ve.args[0]
           
        return HttpResponseBadRequest(content=json.dumps(response_json, ensure_ascii = False))
