#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger("tradeex.api_notify_test")

@csrf_exempt
def api_notify_test(request):
    logger.info('api_notify_test(): receive notification from: {0}'.format(request.get_host()))
    logger.info('api_notify_test(): notification is {0}'.format(request.body.decode('utf-8')))
    return HttpResponse(content='OK')

