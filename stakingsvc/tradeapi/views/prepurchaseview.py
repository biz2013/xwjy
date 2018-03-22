#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.http import JsonResponse
#from django.contrib.auth.decorators import login_required

# this is for test UI. A fake one
from walletgui.views import errorpageview
from walletgui.controller.global_constants import *

import logging,json

logger = logging.getLogger("tradeapi.prepurchase")

#@login_required
def prepurchase(request):
    try:
        request_json= json.loads(request.body)
        
        response_data = {}
        response_data['return_code'] = 'SUCCESS1'
        print('prepurchase ...')
        return JsonResponse(response_data)
    except Exception as e:
       error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
