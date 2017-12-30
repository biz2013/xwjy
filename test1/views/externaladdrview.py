#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import render, redirect

# this is for test UI. A fake one
from controller.global_constants import *
from controller import useraccountinfomanager

from users.models import *
from views.models.returnstatus import ReturnStatus
from views.models.userexternalwalletaddrinfo import UserExternalWalletAddressInfo
import logging,json

logger = logging.getLogger("site.externaladdresss")

def external_address(request):
    try:
       if not user_session_is_valid(request):
          return render(request, 'html/login.html', { 'next_action' : '/accounts/accountinfo/'})
       externaladdress = None
       if request.method == 'GET':
          # if there's id parameter, this is view/update request,
          # query the object first and show
          if 'id' in request.GET:
              id = int(request.GET['id'])
              logger.info('Get user {0}\'s external address by {1}'.format(
                  request.session[REQ_KEY_USERNAME], id))
              externaladdress = useraccountinfomanager.get_user_externaladdr_by_id(id)
          else:
              externaladdress = None
          return render(request, 'html/update_external_address.html',
               { 'user_external_address': externaladdress })
       else:
          id = int(request.POST['id'])
          address = request.POST['address']
          alias = request.POST['alias']
          externaladdress = UserExternalWalletAddressInfo(id,
             request.session[REQ_KEY_USERID], address, alias)
          rc, error_msg = useraccountinfomanager.create_update_externaladdr(
              externaladdress, request.session[REQ_KEY_USERNAME])
          if rc:
             return redirect(request, 'accountinfo')
          #TODO add error message
          else:
             return render(request, 'html/update_external_adress.html',
                  { 'error_msg': error_msg,
                    'user_external_address': externaladdress })
    except:
       error_msg = 'external_address hit exception: {0}'.format(sys.exc_info()[0])
       logger.error(error_msg)
       return errorpage.show_error(request, ERR_CRITICAL_IRRECOVERABLE,
              '系统遇到问题，请稍后再试。。。{0}'.format(error_msg))

    if request.method == 'GET':
       user_id = int(request.GET.get('id'))
       user_addr = manager.get_user_address(user_id)
       return render(request, 'html/update_external_address.html',
            { 'user_external_address': user_addr })
    else:
        user_id = int(request.POST['userId'])
        address = request.POST['address']
        alias = request.POST['alias']
        rc, message = manager.upsert_user_external_address(user_id, address, alias)
        if rc == 0:
            useraccountInfo = manager.get_user_accountInfo(request.session['username'])
            return render(request, 'html/myaccount.html', {'useraccountInfo': useraccountInfo})
        else:
            user_addr = manager.get_user_address(user_id)
            return render(request, 'html/update_external_adress.html',
               { 'user_external_address': user_addr })
