#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

from django.views.decorators.csrf import csrf_exempt

from walletgui.controller.apiusermanager import APIUserManager

import logging,json

logger = logging.getLogger("tradeex.apiuser")

@csrf_exempt
def register(request):
    try:
        
        APIUserManager.create_api_user_account(request.username, 'CNY')
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
