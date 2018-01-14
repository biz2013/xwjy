#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.global_constants import *
from controller.global_utils import *
from controller import useraccountinfomanager

from users.models import *
from views.models.returnstatus import ReturnStatus
from views.models.userexternalwalletaddrinfo import UserExternalWalletAddressInfo
from views import errorpage
from django.contrib.auth.decorators import login_required

import logging,json

logger = logging.getLogger("site.externaladdresss")

@login_required
def external_address(request):
    try:
       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/accounts/accountinfo/'})
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
                  request.session[REQ_KEY_USERNAME], id))
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
             request.session[REQ_KEY_USERID], alias, address, crypto)
          useraccountinfomanager.create_update_externaladdr(
             externaladdress, request.session[REQ_KEY_USERNAME])
          return redirect('accountinfo')
    except Exception as e:
       error_msg = '添加／修改提币抵制遇到错误: {0}'.format(sys.exc_info()[0])
       logger.exception(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))
