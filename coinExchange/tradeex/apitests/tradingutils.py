#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.test import Client
from trading.models import *

def create_axfund_sell_order(username, passwd, units, unit_price, unit_price_currency):

    sellorder_dict = { 
            'request_source': 'sellorder',
            'quantity': units,
            'unit_price' : unit_price,
            'unit_price_currency': unit_price_currency,
            'crypto': 'AXFund',
            'total_amount': round(units * unit_price, 8) }
    c = Client()
    if not c.login(username=username, password='user@123'):
        raise ValueError('{0}:{1} cannot login'.format(username, passwd))
    response = c.post('/trading/mysellorder/', sellorder_dict, follow=True)
    print('create_axfund_sell_order({0},{1},{2},{3}) purchase view return {4}'.format(
          username, units, unit_price, unit_price_currency, response.status_code))
    #print 'purchase view template {0}'.format(response.templates)
    return response

def show_order_overview():
    print('------ show_order_overview ---- ')
    for order in Order.objects.all().order_by('lastupdated_at'):
        #print('{0}'.format(order.__class__.__name__)))
        print('order: {0}|type: {1},{2},{3} {4}=@{5}*{6} status:{7} payment:{8}/{9} from user {10}:{11}'.format(
            order.order_id, order.order_type, order.sub_type, order.order_source,
            order.total_amount, order.unit_price, order.units, order.status,
            order.selected_payment_provider.code if order.selected_payment_provider else 'N/A', 
            order.account_at_selected_payment_provider,
            order.user.id, order.user.username
            ))

def dump_userwallet(wallet):
    if not wallet:
        print('encounter none wallet')
        return
    print('wallet {0}|{1}, user {2} {3}, balance {4}/{5}/{6}, address {7}'.format(
        wallet.id, wallet.wallet.cryptocurrency.currency_code, 
        wallet.user.id, wallet.user.username, 
        wallet.balance, wallet.locked_balance, wallet.available_balance,
        wallet.wallet_addr
    ))

def dump_userwallet_trans(trans):
    if not trans:
        print('encounter none user_wallet_tran')
        return
    print('wallet_trans: {0}|{1} status:{2} type:{3}: {4} ({5}/{6}/{7})->({8}/{9}/{10}) payment:{11}:{12}:{13}'.format(
        trans.id, trans.user_wallet.wallet.cryptocurrency.currency_code,
        trans.status, 
        trans.transaction_type, trans.units,
        trans.balance_begin, trans.locked_balance_begin, trans.available_to_trade_begin,
        trans.balance_end, trans.locked_balance_end, trans.available_to_trade_end,
        trans.payment_provider.code, trans.payment_bill_no, trans.payment_status
    )) 
def show_user_wallet_overview(selected_users = None):
    if not selected_users:
        print('------ show all user wallets and their transactions --------')
        active_wallets = UserWallet.objects.filter(user__isnull = False)
        for wallet in active_wallets:
            dump_userwallet(wallet)
            axf_trans = UserWalletTransaction.objects.filter(user_wallet__id=wallet.id).order_by("lastupdated_at")
            if len(axf_trans) > 0:
                print('{0} has {1} trans'.format(wallet.user.username, len(axf_trans)))
                for tran in axf_trans:
                    dump_userwallet_trans(tran)
    else:
        print('------ show user wallets and their transactions of {0} --------'.format(
            selected_users
        ))
        for user in selected_users:
            wallet = UserWallet.objects.get(user__username=user)
            axf_trans = UserWalletTransaction.objects.filter(user_wallet__id=wallet.id).order_by("lastupdated_at")
            if len(axf_trans) > 0:
                print('{0} has {1} trans'.format(wallet.user.username, len(axf_trans)))
                for tran in axf_trans:
                    dump_userwallet_trans(tran)


def show_user_wallet_trans(buyer, seller):
    print('---------show buyer {0} and seller {1} transaction overview ------'.format(buyer, seller))
    print('**** buyer {0} *******'.format(buyer))
    axf_wallet = UserWallet.objects.get(user__username=buyer, wallet__cryptocurrency__currency_code='AXFund')
    dump_userwallet(axf_wallet)
    axf_trans = UserWalletTransaction.objects.filter(user_wallet__id=axf_wallet.id).order_by("lastupdated_at")
    if len(axf_trans) > 0:
        print('???? has {0} trans'.format(len(axf_trans)))
        for tran in axf_trans:
            dump_userwallet_trans(tran)
    else:
        print('no axf_wallet_trans for buyer {0}'.format(buyer))
    
    try:
        cny_wallet = UserWallet.objects.get(user__username=buyer, wallet__cryptocurrency__currency_code='CNY')    
        dump_userwallet(cny_wallet)
        cny_trans = UserWalletTransaction.objects.filter(user_wallet__id=cny_wallet.id).order_by("lastupdated_at")
        if len(cny_trans) > 0:
            for tran in cny_trans:
                dump_userwallet_trans(tran)
        else:
            print('no cyn_wallet_trans for buyer {0}'.format(buyer))
    except UserWallet.DoesNotExist:
        print('no cny wallet for buyer {0}'.format(buyer))

    print('**** seller {0} *******'.format(seller))
    axf_wallet = UserWallet.objects.get(user__username=seller, wallet__cryptocurrency__currency_code='AXFund')
    dump_userwallet(axf_wallet)
    axf_trans = UserWalletTransaction.objects.filter(user_wallet__id=axf_wallet.id).order_by("lastupdated_at")
    if len(axf_trans) > 0:
        for tran in axf_trans:
            dump_userwallet_trans(tran)
    else:
        print('no axf_wallet_trans for seller {0}'.format(seller))
    
    cny_wallet = UserWallet.objects.get(user__username=seller, wallet__cryptocurrency__currency_code='CNY')
    dump_userwallet(cny_wallet)
    cny_trans = UserWalletTransaction.objects.filter(user_wallet__id=cny_wallet.id).order_by("lastupdated_at")
    if len(cny_trans) > 0:
        for tran in cny_trans:
            dump_userwallet_trans(tran)
    else:
        print('no cyn_wallet_trans for seller {0}'.format(seller))

def show_api_trans(api_trans):
    print('Trans:{0} from user {1}, action: {2} order:{3} payment_status:{4} trade_status: {5}'.format(
        api_trans.transactionId, api_trans.api_user.user.username,
        api_trans.action, api_trans.reference_order.order_id if api_trans.reference_order else 'N/A',
        api_trans.payment_status, api_trans.trade_status
    ))