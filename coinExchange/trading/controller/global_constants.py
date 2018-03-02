#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# This define all the field keys for HTTP requests/session
#
REQ_KEY_USERNAME = 'username'
REQ_KEY_USERID = 'userid'
REQ_KEY_USERACCOUNTINFO = 'useraccountinfo'

# Value Error Name
VE_REDEEM_EXCEED_LIMIT='Redeem Exceed Limit'
VE_ILLEGAL_BALANCE='Illegal Balance'

#
# These are error level constants tha help us handle
# errors
#
ERR_CRITICAL_RECOVERABLE='ERR_CRITICAL_RECOVERABLE'
ERR_CRITICAL_IRRECOVERABLE='ERR_CRITICAL_IRRECOVERABLE'

# heepay url
HEEPAYREGISTRY='https://wallet.heepay.com/Account/Register?returnUrl=%s'
