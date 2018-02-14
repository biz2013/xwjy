#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from trading.controller.global_constants import *
from trading.controller.global_utils import *
from trading.controller import useraccountinfomanager

from trading.models import *
from trading.views.models.returnstatus import ReturnStatus
from trading.views.models.userexternalwalletaddrinfo import UserExternalWalletAddressInfo
from trading.views import errorpageview
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.externaladdresss")

@login_required
def external_address(request):
    try:
       if not request.user.is_authenticated():
          return render(request, 'login.html', { 'next' : '/accounts/accountinfo/'})
       externaladdress = None
       if request.method == 'GET':
          # if there's id parameter, this is view/update request,
          # query the object first and show
          if 'id' in request.GET:
              id = 0
              id_str = request.GET['id']
              if len(id_str) > 0:
                 id = int(id_str)
              logger.info('Get user {0}\'s external address by {1}'.format(
                  request.user.username, id))
              externaladdress = useraccountinfomanager.get_user_externaladdr_by_id(id)
          else:
              externaladdress = None
          return render(request, 'html/update_external_address.html',
               { 'user_external_address': externaladdress })
       else:
          id = 0
          id_str = request.POST['id']
          if len(id_str) > 0:
             id = int(id_str)
          address = request.POST['address']
          alias = request.POST['alias']
          crypto = request.POST['crypto']
          if len(crypto) == 0:
              crypto = 'AXFund'
          externaladdress = UserExternalWalletAddressInfo(id,
             request.user.id, alias, address, crypto)
          if not useraccountinfomanager.create_update_externaladdr(
                 externaladdress, request.user.username):
              messages.error(request, "您的提币地址属于交易平台注入地址，请修改您的提币地址")
          return redirect('accountinfo')
    except Exception as e:
       error_msg = '添加／修改提币抵制遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
