#!/usr/bin/python
# -*- coding: utf-8 -*-
class TransactionListItem(object):
    def __init__(self, id, trans_type, balance_update_type, units, balance, locked_balance, available_balance, status , lastupdated_at, crypto):
        lookup = {'CANCEL SELL ORDER':'取消卖单',
                   'OPEN BUY ORDER': '购买',
                   'OPEN SELL ORDER': '出售',
                   'CANCEL BUY ORDER': '取消买单',
                   'DELIVER ON PURCHASE': '交货',
                   'REDEEM': '提币',
                   'DEPOSIT': '存币'}
        self.id = id
        self.trans_type = trans_type
        self.trans_type_display = lookup[trans_type]
        self.balance_update_type = balance_update_type
        self.units = units
        self.balance = balance
        self.locked_balance = locked_balance
        self.available_balance = available_balance
        self.status = status
        self.crypto = crypto
        self.lastupdated_at = lastupdated_at
