#!/usr/bin/python
# -*- coding: utf-8 -*-
from tradeex.controllers.walletmanager import WalletManager

def check_on_wallet(request):
    try:
        client_ip = get_client_ip(request)
        if client_ip != '127.0.0.1':
            message = 'update_account_with_receiving_fund() only accept request from localhost. The client ip is {0}'.format(client_ip)
            logger.error(message)
            return HttpResponseForbidden()
        WalletManager.check_wallets('CNY')


        useraccountinfomanager.update_account_balance_with_wallet_trx(
                'AXFund', trans, min_trx_confirmation)
        return HttpResponse('OK')
    except Exception as e:
       error_msg = 'check_on_wallet hit exception: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return HttpResponseServerError(error_msg)
