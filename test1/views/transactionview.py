#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import logging,json

from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.global_constants import *
from controller.global_utils import *
from controller import ordermanager
from controller import useraccountinfomanager

from views.models.orderitem import OrderItem
from views.models.transactionlistitem import TransactionListItem
from views.models.returnstatus import ReturnStatus
from views import errorpage
from django.contrib.auth.decorators import login_required


logger = logging.getLogger("site.sellorder")

def create_trans_list_item(transaction, crypto):
    return TransactionListItem(transaction.id,
       transaction.transaction_type,
       transaction.balance_update_type,
       transaction.units,
       transaction.balance_end,
       transaction.locked_balance_end,
       transaction.available_to_trade_end,
       transaction.status,
       transaction.lastupdated_at,
       crypto)

@login_required
def listusertransactions(request):
    try:
       if not request.user.is_authenticated():
          return render(request, 'login.html', { 'next' : '/transhistory/'})
       username = request.user.username
       userId = request.user.id
       trans = ordermanager.get_user_transactions(userId, 'AXFund')
       pending_trans = []
       transactions = []
       for tran in trans:
           if tran.status == 'PENDING':
               pending_trans.append(create_trans_list_item(tran,'AXFund'))
           else:
               transactions.append(create_trans_list_item(tran, 'AXFund'))
       accountinfo = useraccountinfomanager.get_user_accountInfo(request.user, 'AXFund', True)
       return render(request, 'html/translist.html', {
                'pending_trans': pending_trans,
                'transactions': transactions,
                'useraccountInfo': accountinfo})

    except Exception as e:
       error_msg = '出售美基金遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
