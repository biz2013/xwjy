#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseServerError, HttpResponseBadRequest
from django.utils import timezone

from trading.models import *
from tradeex.models import *
from tradeex.controllers.walletmanager import WalletManager
from tradeex.utils import *

import logging,json

logger = logging.getLogger("tradeex.apiuser")


def create_user(username, password, email, appId, secret, 
        payment_account, external_addr, operator, cny_address = None):
    cny_wallet = Wallet.objects.get(cryptocurrency__currency_code = 'CNY')
    axf_wallet = Wallet.objects.get(cryptocurrency__currency_code = 'AXFund')
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
    
    account_count = user1.id
    account_no = '%d-%04d' % (
        int((100000000 + account_count)/10000),
        (100000000 + account_count) % 10000
    )
    try:
        api_user = APIUserAccount.objects.get(user__username = username)
        logger.info("{0}:{1} api user object already exists".format(username, appId))
    except APIUserAccount.DoesNotExist:
        api_user = APIUserAccount.objects.create(
            user = user1,
            accountNo = account_no,
            apiKey = appId,
            secretKey = secret,
            status = 'ACTIVE',
            created_by = operator,
            lastupdated_by = operator
        )
        logger.info("Create {0}:{1} user object".format(username, appId))
    except APIUserAccount.MultipleObjectsReturned:
        logger.error('There are more than one {0}:{1} api user object'.format(username, appId))
        return False
    
    try:
        userwallet = UserWallet.objects.get(user__id = user1.id, wallet__id = cny_wallet.id)
        logger.info('userwallet {0}:{1} already exists'.format(
                userwallet.id, userwallet.wallet_addr         
        ))
    except UserWallet.DoesNotExist:
        existingwallets = UserWallet.objects.filter(user__isnull = True, wallet__id = cny_wallet.id)
        if len(existingwallets) > 0:
            pickedwallet = UserWallet.objects.select_for_update().get(id = existingwallets[0].id)
            pickedwallet.user = user1
            pickedwallet.lastupdated_by = operator
            pickedwallet.save()
            logger.info('Assign userwallet {0}:{1} to user {2}'.format(
                existingwallets[0].id, existingwallets[0].wallet_addr, username
            ))
        else:
            cnyutil = WalletManager.create_fund_util('CNY')
            addr = cnyutil.create_wallet_address() if not cny_address else cny_address
            userwallet=UserWallet.objects.create(
                user = user1,
                wallet = cny_wallet,
                wallet_addr = addr,
                created_by = operator,
                lastupdated_by = operator
            )

            userwallet.save()

            logger.info('Create userwallet {0}:{1} for user {2}'.format(
                userwallet.id, userwallet.wallet_addr, username
            ))
    except UserWallet.MultipleObjectsReturned:
        logger.error('There are more than one user wallet for api user {0}'.format(username))
        return False

    try:
        axf_userwallet = UserWallet.objects.get(user__id = user1.id, wallet__id = axf_wallet.id)
        logger.info('axf userwallet {0}:{1} already exists'.format(
                axf_userwallet.id, axf_userwallet.wallet_addr         
        ))
    except UserWallet.DoesNotExist:
        axf_existingwallets = UserWallet.objects.filter(user__isnull = True, wallet__id = axf_wallet.id)
        if len(axf_existingwallets) > 0:
            pickedwallet = UserWallet.objects.select_for_update().get(id = axf_existingwallets[0].id)
            pickedwallet.user = user1
            pickedwallet.lastupdated_by = operator
            pickedwallet.save()
            logger.info('Assign userwallet {0}:{1} to user {2}'.format(
                axf_existingwallets[0].id, axf_existingwallets[0].wallet_addr, username
            ))
        else:
            logger.error('There is not existing axf wallet for new user')
            return False
    except UserWallet.MultipleObjectsReturned:
        logger.error('There are more than one user wallet for api user {0}'.format(username))
        return False

    heepay = PaymentProvider.objects.get(pk='heepay')
    try:
        userpayment = UserPaymentMethod.objects.get(user__id = user1.id, provider__code = heepay.code)
        logger.info('user {0} has heepay account {1}'.format(user1.username, userpayment.account_at_provider))
        userpayment.account_at_provider = payment_account
        userpayment.lastupdated_by = operator
        userpayment.save()

    except UserPaymentMethod.DoesNotExist:
        UserPaymentMethod.objects.create(
            user = user1,
            provider = heepay,
            account_at_provider = payment_account,
            created_by = operator,
            lastupdated_by = operator            
        ).save()
        logger.info('Created heepay account for user {0}'.format(user1.username))
    except UserPaymentMethod.MultipleObjectsReturned:
        logger.error('User {0} has more than one heepay account'.format(user1.username))
        return False    

    if external_addr:
        try:
            user_external_addr = UserExternalWalletAddress.objects.get(user__id = user1.id, cryptocurrency__currency_code='CNY')
            logger.info('There is existing external address for user {0}'.format(user1.id))
        except UserExternalWalletAddress.DoesNotExist:
            user_external_addr = UserExternalWalletAddress.objects.create(
                user = user1,
                cryptocurrency = cny,
                address = external_addr,
                alias = 'cny_external_addr',
                created_by = operator,
                lastupdated_by = operator
            )
            user_external_addr.save()
            logger.info('Create user external addr for user {0}'.format(user1.id))
        except UserExternalWalletAddress.MultipleObjectsReturned:
            logger.error('User {0} has more than multiple addr'.format(user1.id))
    return True

@csrf_exempt
def create(request):
    if request.method != 'POST':
        return HttpResponseBadRequest(content='请用POST发送请求')

    logger.info('receive request from: {0}'.format(request.get_host()))
    logger.info('receive request {0}'.format(request.body.decode('utf-8')))
    request_json= json.loads(request.body.decode('utf-8'))

    try:
        if not ('email' in request_json):
            raise ValueError('请提供email')

        if not 'payment_account' in request_json:
            raise ValueError('请提供汇钱包账号')

        appId = id_generator(32)
        secret = create_access_keys(appId)    
        email = request_json['email']
        username = request_json['username'] if 'username' in request_json else email
        password = request_json['password'] if 'password' in request_json else id_generator(16)
        payment_account = request_json['payment_account']
        external_addr = request_json.get('external_cny_addr', None)

        login = User.objects.get(username='admin')
        with transaction.atomic():
            cny_wallet = Wallet.objects.select_for_update().get(cryptocurrency__currency_code='CNY')

            if not create_user(username, password, email, appId, secret, 
                    payment_account, external_addr, login):
                raise ValueError('failed to create test user')

            api_user = APIUserAccount.objects.get(user__username=username)
            response_json = {}
            response_json["result"] = 'ok'
            response_json["apiKey"] = api_user.apiKey
            response_json["secretKey"] = api_user.secretKey
            response_json["accountNo"] = api_user.accountNo    
        return JsonResponse(response_json)
    except ValueError as ve:
        logger.error('Create test user has issue')
        return HttpResponseBadRequest(content='Failed: {0}'.format(ve.args[0]))
