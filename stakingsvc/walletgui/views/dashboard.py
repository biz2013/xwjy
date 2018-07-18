#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
from django.contrib.auth.decorators import login_required

import walletgui.controller.crypto_utils import CryptoUtility
import walletgui.controller.walletmanager import WalletManager

logger = logging.getLogger("site.dashboard")

@login_required
def show(request):
    crypto_util = WalletManager.create_fund_util('CNY')
    wallet = WalletMAnager.get_wallet_balance(crypto_util, request.user.username, 'CNY')
    
            paymentmethods.append(
          UserPaymentMethodView(1, 1, 'heepay', '汇钱包', '15910978598')
        )
        useraccountInfo = UserAccountInfo(1, 1000.0, 1000.0, 0.0,
            'AXjtBn93Y8Yti6LXWQqwkrF1pHcBRGYEDu', None, paymentmethods)
        return render(request, 'walletgui/balance.html',
                  {'account': useraccountInfo})
    except Exception as e:
        error_msg = '用户主页显示遇到错误: {0}'.format(sys.exc_info()[0])
        logger.exception(error_msg)
        return errorpageview.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
            '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

