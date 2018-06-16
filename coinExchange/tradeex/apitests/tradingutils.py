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