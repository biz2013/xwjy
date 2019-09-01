#!/usr/bin/python
# -*- coding: utf-8 -*-
API_METHOD_PURCHASE='wallet.trade.buy'
API_METHOD_REDEEM='wallet.trade.sell'
API_METHOD_QUERY='wallet.trade.query'
API_METHOD_CANCEL='wallet.trade.cancel'

MIN_CRYPTOCURRENCY_UNITS = 0.00000001
MIN_CRYPTOCURRENCY_UNITS_DECIMAL = 8

HEEPAY_ERR_NONEXIST_RECEIVE_ACCOUNT='收钱方账号不存在'

PAYMENT_STATUS_NOTSTARTED='Not Started'
PAYMENT_STATUS_PAYSUCCESS='PaySuccess'
PAYMENT_STATUS_SUCCESS='Success'
PAYMENT_STATUS_EXPIREDINVALID='ExpiredInvalid'
PAYMENT_STATUS_DEVCLOSE='DevClose'
PAYMENT_STATUS_USERABANDON='UserAbandon'
PAYMENT_STATUS_UNKONWN='UNKNOWN'
PAYMENT_STATUS_FAILURE='Failure'
PAYMENT_STATUS_STARTING='Starting'
PAYMENT_STATUS_BADRECEIVINGACCOUNT='BadReceiveAccount'

TRADE_STATUS_NOTSTARTED='NotStarted'
TRADE_STATUS_PAYSUCCESS='PaidSuccess'
TRADE_STATUS_SUCCESS='Success'
TRADE_STATUS_EXPIREDINVALID='ExpiredInvalid'
TRADE_STATUS_DEVCLOSE='DevClose'
TRADE_STATUS_USERABANDON='UserAbandon'
TRADE_STATUS_UNKNOWN='UnKnown'
TRADE_STATUS_FAILURE='Failure'
TRADE_STATUS_INPROGRESS='InProgress'
TRADE_STATUS_CREADED='PurchaseOrderCreated'
TRADE_STATUS_BADRECEIVINGACCOUNT='BadReceiveAccount'

ERR_USER_NOT_FOUND_BASED_ON_APPID='ERR_USER_NOT_FOUND_BASED_ON_APPID'
ERR_MORE_THAN_ONE_USER_BASED_ON_APPID = 'ERR_MORE_THAN_ONE_USER_BASED_ON_APPID'

ERR_UNEXPECTED_METHOD ='ERR_UNEXPECTED_METHOD'
ERR_INVALID_SIGNATURE = 'ERR_INVALID_SIGNATURE'
ERR_OVER_TRANS_LIMIT = 'ERR_OVER_TRANS_LIMIT'

ERR_REQUEST_MISS_METHOD = 'ERR_REQUEST_MISS_METHOD'
ERR_REQUEST_MISS_BIZCONTENT = 'ERR_REQUEST_MISS_BIZCONTENT'
ERR_REQUEST_MISS_VERSION = 'ERR_REQUEST_MISS_VERSION'
ERR_REQUEST_MISS_CHARSET = 'ERR_REQUEST_MISS_CHARSET'
ERR_REQUEST_MISS_SIGN_TYPE = 'ERR_REQUEST_MISS_SIGN_TYPE'
ERR_REQUEST_MISS_TIMESTAMP = 'ERR_REQUEST_MISS_TIMESTAMP'
ERR_REQUEST_MISS_SIGNATURE = 'ERR_REQUEST_MISS_SIGNATURE'
ERR_REQUEST_MISS_PAYMENT_PROVIDER = 'ERR_REQUEST_MISS_PAYMENT_PROVIDER'
ERR_REQUEST_MISS_PAYMENT_ACCOUNT_FOR_REDEEM = 'ERR_REQUEST_MISS_PAYMENT_ACCOUNT_FOR_REDEEM'

ERR_HEEPAY_REQUEST_EXCEPTION = 'ERR_HEEPAY_REQUEST_EXCEPTION'
ERR_HEEPAY_REQUEST_ERROR = 'ERR_HEEPAY_REQUEST_ERROR'
ERR_HEEPAY_NO_LONGER_SUPPORT_ERROR = 'ERR_HEEPAY_NO_LONGER_SUPPORT_ERROR'
ERR_INVALID_JSON_INPUT = 'ERR_INVALID_JSON_INPUT'
ERR_INVALID_OR_MISSING_PAYMENT_PROVIDER = 'ERR_INVALID_OR_MISSING_PAYMENT_PROVIDER'
ERR_REDEEM_REQUEST_NO_PAYMENT_ACCOUNT = 'ERR_REDEEM_REQUEST_NO_PAYMENT_ACCOUNT'
ERR_CANNOT_FIND_SELLER_PAYMENT_ACCOUNT = 'ERR_CANNOT_FIND_SELLER_PAYMENT_ACCOUNT'
ERR_CANNOT_FIND_SELLER_PAYMENT_PROVIDER = 'ERR_CANNOT_FIND_SELLER_PAYMENT_PROVIDER'
ERR_CANNOT_FIND_BUYER_PAYMENT_PROVIDER = 'ERR_CANNOT_FIND_BUYER_PAYMENT_PROVIDER'
ERR_NO_RIGHT_SELL_ORDER_FOUND = 'ERR_NO_RIGHT_SELL_ORDER_FOUND'
ERR_NO_SELL_ORDER_TO_SUPPORT_PRICE = 'ERR_NO_SELL_ORDER_TO_SUPPORT_PRICE'
ERR_ORDER_USED_OR_LOCKED_CANCELLED = 'ERR_ORDER_USED_OR_LOCKED_CANCELLED'
ERR_MORE_THAN_ONE_OPEN_BUYORDER = 'ERR_MORE_THAN_ONE_OPEN_BUYORDER'
ERR_API_SELLER_NO_API_RECORD = 'ERR_API_SELLER_NO_API_RECORD'
NOTIFY_RESPONSE_LEN=1000
