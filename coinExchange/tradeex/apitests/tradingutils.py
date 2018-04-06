#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.test import Client

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
          username, units, unit_price, unit_price_currency, response.content.decode('utf-8')))
    #print 'purchase view template {0}'.format(response.templates)
    return response