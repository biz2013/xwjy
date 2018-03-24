#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse

from walletgui.config import context_processor

#from django.contrib.auth.decorators import login_required

# this is for test UI. A fake one
from walletgui.views import errorpageview
from walletgui.controller.global_constants import *
from tradeapi.data.traderequest import *
from tradeapi.utils import *

import logging,json

logger = logging.getLogger("tradeapi.prepurchase")

# in case in the future we need to reconstruct the
# response from trade exchange.  For now, it is
# just straight return
def handle_prepurchase_response(response):
    return response


#@login_required
def prepurchase(request):
    try:
        logger.debug('receive request from: {0}'.format(request.get_host()))
        logger.info('receive request {0}'.format(request.body.decode('utf-8')))
        request_json= json.loads(request.body)
        request_obj = PrepurchaseRequest.parseFromJson(request_json)

        # TODO: read config to get trade exchange url
        tradeEx_api_url = settings.TRADE_EXCHANGE_API_URL
        # forward request to trade exchange
        trade_client = TradeExchangeAPIClent(tradeEx_api_url)

        tradeEx_response = TradeExRequest.create_with_meta_info(
                request_obj,
                # create info telling trade exchange where the request come
                # from
                # TODO: define what we want to put there
                create_tradeEx_request_meta_info(context_processor.settings['settings']))
        trade_response = trade_client.sendrequest(request_obj)
        return JsonResponse(handle_prepurchase_response(trade_response))
    except Exception as e:
       error_msg = 'prepurchase()遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return HttpResponseServerError('系统处理充值请求时出现系统错误')
