#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.conf import settings
from django.http import HttpResponse, HttpResponseServerError,HttpResponseForbidden

from trading.config import context_processor
from trading.controller.global_utils import *
from trading.controller.coin_utils import *
from trading.models import *
from trading.controller import wallet_address_query

logger = logging.getLogger("site.wallet_address_batch")

def create_wallet_address(request):
    try:
        client_ip = get_client_ip(request)
        if client_ip not in settings.ALLOWED_HOSTS:
            message = 'create_wallet_address() only accept request from localhost. The client ip is {0}'.format(client_ip)
            logger.error(message)
            return HttpResponseForbidden()

        axfd_tool = get_coin_utils(AXFUND_CRYPTO_CODE)

        sitesettings = context_processor.settings(request)['settings']
        config_json = json.loads(sitesettings.config_json)
        batch_size = 20
        if 'wallet_address_batch_size' in config_json:
            batch_size = config_json['wallet_address_batch_size']
        batch_start_threshold = 10
        if 'wallet_address_batch_threshold' in config_json:
            batch_start_threshold = config_json['wallet_address_batch_threshold']

        unassigned_count = wallet_address_query.get_unassigned_userwallets_count()
        if unassigned_count > batch_start_threshold:
            logger.info("There are still {0} address left.  Not creating new addresses".format(unassigned_count))
            return HttpResponse('OK --- No change')

        logger.info("Unlock wallet before generating address")
        axfd_tool.unlock_wallet(15)
        new_addresses = []
        for i in range(0, batch_size - unassigned_count):
            new_addresses.append(axfd_tool.create_wallet_address())
            logger.info("Create address[{0}]={1}".format(i, new_addresses[i]))

        wallet_address_query.create_user_wallets(new_addresses, 'AXFund', 'admin')
        return HttpResponse('OK')

    except Exception as e:
       error_msg = 'create_wallet_address hit exception: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return HttpResponseServerError(error_msg)
