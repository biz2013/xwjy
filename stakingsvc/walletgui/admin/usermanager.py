#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json
import datetime

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from walletgui.models import *
from tradeapi.utils import *
from tradeapi.walletmanager import WalletManager

from tradeapi.models import *

logger = logging.getLogger("site.create_user_account")

def create_user(username, password, email, operator, cny_address):
    cny_wallet = Wallet.objects.get(cryptocurrency__currency_code = 'CNY')
    cny = Cryptocurrency.objects.get(currency_code = 'CNY')

    try:
        user1 = User.objects.get(username = username)
        logger.info("{0} user object already exists".format(username))
    except User.DoesNotExist:
        get_user_model().objects.create_user(username, email, password)
        user1 = User.objects.get(username = username)
        logger.info("Create {0} user object".format(user1.username))
    except User.MultipleObjectsReturned:
        logger.error('There are more than one {0} user object'.format(username))
        return False

    try:
        userwallet = UserWallet.objects.get(user__id = user1.id, wallet__id = cny_wallet.id)
        logger.info('userwallet {0}:{1} already exists'.format(
                userwallet.id, userwallet.wallet_addr         
        ))
    except UserWallet.DoesNotExist:
        user_cny_wallet = UserWallet.objects.create(
            user = user1,
            wallet = cny_wallet,
            wallet_addr = cny_address,
            lastupdated_by = operator,
            created_by = operator
        )
        user_cny_wallet.save()
    except UserWallet.MultipleObjectsReturned:
        logger.error('There are more than one user wallet for api user {0}'.format(username))
        return False

    except UserWallet.MultipleObjectsReturned:
        logger.error('There are more than one user wallet for api user {0}'.format(username))
        return False

    return True


@csrf_exempt
def create(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('请用POST方式')

    request_str = request.body.decode('utf-8')
    logger.info('create_api_user receive request {0}'.format(request_str))
    request_json= json.loads(request_str)
    if not ('email' in request_json):
        logger.error("not email")
        return HttpResponseBadRequest(content='请提供email')

    if not settings.CNYADDRESS or len(settings.CNYADDRESS) == 0:
        logger.error("not cnyaddress")
        return HttpResponseBadRequest(content='请提供钱包地址')
    email = request_json['email']
    username = request_json['username'] if 'username' in request_json else email
    password = request_json['password'] if 'password' in request_json else id_generator(16)

    login = User.objects.get(username='admin')
    try:
        with transaction.atomic():
            if not create_user(username, password, email, login, settings.CNYADDRESS):
                raise ValueError('failed to create test user')
    except ValueError:
        logger.error('Create test user has issue')
        return HttpResponseBadRequest(content='error')
    return HttpResponse(content='ok')
