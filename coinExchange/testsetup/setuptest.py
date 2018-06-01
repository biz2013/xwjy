#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging, json
import datetime
from tradeex.models import *
from trading.models import *
from django.db import transaction
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from tradeex.controllers.walletmanager import WalletManager

logger = logging.getLogger("site.testsetup")

def setupbasic(operator):
    login = operator

    logger.info("About to create CNY currency entry")
    try:
        crypto = Cryptocurrency.objects.get(currency_code = 'CNY')
        logger.info("CNY currency object already exists")
    except Cryptocurrency.DoesNotExist:
        logger.info("Create CNY object")
        crypto = Cryptocurrency.objects.create(
            currency_code = 'CNY',
            name = '人民币',
            created_by = login,
            lastupdated_by = login
        )
        crypto.save()
        logger.info("Create CNY object")
    except Cryptocurrency.MultipleObjectsReturned:
        logger.error("There are more than one CNY currency objects")
        return False

    logger.info("About to create CNY wallet entry for wallet config")
    try:
        wallet = Wallet.objects.get(cryptocurrency__currency_code = 'CNY')
        wallet_config = json.loads(wallet.config_json)
        logger.info("CNY wallet object already exists.  Getting config {0}".format(
            json.dumps(wallet_config, ensure_ascii=False)))
    except Wallet.DoesNotExist:
        wallet_config = {}
        wallet_config['bin_path'] = "/usr/bin/peercoind"
        wallet_config['passphrase'] = ""
        wallet_config['datadir'] = "/home/ubuntu/.peercoin"
        wallet_config['list_trans_count'] = 100000
        wallet_config["account_name"] = ""
        Wallet.objects.create(
            name = 'CNY',
            cryptocurrency = crypto,
            config_json = json.dumps(wallet_config, ensure_ascii=False),
            created_by = login,
            lastupdated_by = login
        ).save()
        logger.info("Create CNY wallet object")
    except Wallet.MultipleObjectsReturned:
        logger.error("There are more than one CNY wallet objects")
        return False
    
    return True

def create_user(username, password, email, apiaccount, appId, secret, operator):
    wallet = Wallet.objects.get(cryptocurrency__currency_code = 'CNY')
    try:
        user1 = User.objects.get(username = username)
        logger.info("{0} user object already exists".format(username))
    except User.DoesNotExist:
        user1= User.objects.create(
            username = username,
            password = '',
            email = email,
            is_staff = 0,
            is_active = 1,
            date_joined = datetime.datetime.utcnow()
        )
        logger.info("Create {0} user object".format(username))
    except User.MultipleObjectsReturned:
        logger.error('There are more than one {0} user object'.format(username))
        return False
    
    try:
        api_user = APIUserAccount.objects.get(user__username = username)
        logger.info("{0}:{1} api user object already exists".format(username, appId))
    except APIUserAccount.DoesNotExist:
        api_user = APIUserAccount.objects.create(
            user = user1,
            accountNo = apiaccount,
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
        userwallet = UserWallet.objects.get(user__id = user1.id, wallet__id = wallet.id)
        logger.info('userwallet {0}:{1} already exists'.format(
                userwallet.id, userwallet.wallet_addr         
        ))
    except UserWallet.DoesNotExist:
        existingwallets = UserWallet.objects.filter(user__isnull = True, wallet__id = wallet.id)
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
            addr = cnyutil.create_wallet_address()
            userwallet=UserWallet.objects.create(
                user = user1,
                wallet = wallet,
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
    
    heepay = PaymentProvider.objects.get(pk='heepay')
    try:
        userpayment = UserPaymentMethod.objects.get(user__id = user1.id, provider__code = heepay.code)
        logger.info('user {0} has heepay account {1}'.format(user1.username, userpayment.account_at_provider))
    except UserPaymentMethod.DoesNotExist:
        UserPaymentMethod.objects.create(
            user = user1,
            provider = heepay,
            account_at_provider = '13910978598',
            created_by = operator,
            lastupdated_by = operator            
        ).save()
        logger.info('Created heepay account for user {0}'.format(user1.username))
    except UserPaymentMethod.MultipleObjectsReturned:
        logger.error('User {0} has more than one heepay account'.format(user1.username))
        return False    

    return True

@csrf_exempt
def setuptestuser(request):
    login = User.objects.get(username='admin')
    try:
        with transaction.atomic():
            if not setupbasic(login):
                raise ValueError('failed to setup basics')
            if not create_user('api_test_user1', '---', 'tttzhang2000@yahoo.com', 
                '1000-0001', 'api_test_user_appId1', 'api_test_user_secrets1', login):
                raise ValueError('failed to create test user')
            if not create_user('api_test_user2', '---', 'yingzhuu@yahoo.ca', 
                '1000-0002', 'api_test_user_appId2', 'api_test_user_secrets2', login):
                raise ValueError('failed to create test user')
    except ValueError:
        logger.error('Create test user has issue')
        return HttpResponse(content='error')
    return HttpResponse(content='ok')

