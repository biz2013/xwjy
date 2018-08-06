#!/usr/bin/python
# -*- coding: utf-8 -*-
import math
import logging
from django.test import TestCase
from django.contrib.auth.models import User

from tradeex.controllers.tradex import TradeExchangeManager
from trading.models import Order

logger = logging.getLogger('tradeex.apitests.test_redeem_price_decision')

class TestRedeemPriceDecision(TestCase):
    fixtures = ['fixture_test_tradeapi.json']

    def test_api_price_way_below_normal_price(self):
        orders = []
        admin = User.objects.get(username='admin')
        user = User.objects.get(username='tttzhang2000@yahoo.com')
        orders.append(Order.objects.create(
            order_id='order_1',
            user= user,
            units = 10,
            unit_price = 5.0,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_2',
            user = user,
            units = 10,
            unit_price = 5.0,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_3',
            user = user,
            units = 10,
            unit_price = 5.1,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_4',
            user = user,
            units = 10,
            unit_price = 3.5,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_5',
            user = user,
            units = 10,
            unit_price = 3.499,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        tradeex = TradeExchangeManager()

        suggested_price = tradeex.decide_sell_price(orders)
        print("suggesed price: {0} lowest api price {1}".format(suggested_price, orders[4].unit_price))
        self.assertTrue(suggested_price > orders[4].unit_price, "final price should be higher than lowest API sell order")
        self.assertTrue(suggested_price - orders[4].unit_price - 0.01 > 0, "final price should be at least 0.01 higher than lowest API sell order")
        self.assertTrue(math.fabs(suggested_price - orders[4].unit_price * 1.005) < 0.0001, "final price should be 0.5\% higher than lowest API sell order")

    def test_two_close_low_api_price(self):
        orders = []
        admin = User.objects.get(username='admin')
        user = User.objects.get(username='tttzhang2000@yahoo.com')
        orders.append(Order.objects.create(
            order_id='order_1',
            user= user,
            units = 10,
            unit_price = 1.0,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_2',
            user = user,
            units = 10,
            unit_price = 1.0,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_3',
            user = user,
            units = 10,
            unit_price = 1.1,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_4',
            user = user,
            units = 10,
            unit_price = 0.5,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_5',
            user = user,
            units = 10,
            unit_price = 0.499,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        tradeex = TradeExchangeManager()

        suggested_price = tradeex.decide_sell_price(orders)
        print("suggesed price: {0} lowest api price {1}".format(suggested_price, orders[4].unit_price))
        self.assertTrue(suggested_price > orders[4].unit_price, "final price should be higher than lowest API sell order")
        self.assertTrue(suggested_price - orders[4].unit_price - 0.01 > 0, "final price should be at least 0.01 higher than lowest API sell order")
        self.assertTrue(suggested_price - orders[4].unit_price * 1.005 > 0, "final price should be higher than lowest API sell order addi ng 5\%")
        self.assertTrue(suggested_price - orders[4].unit_price * 1.005 < 0.01, "final price should be less than 0.01 higher than the lowest API sell order adding 5\%")



    def test_normal_trade_price_is_lowest(self):
        orders = []
        admin = User.objects.get(username='admin')
        user = User.objects.get(username='tttzhang2000@yahoo.com')
        orders.append(Order.objects.create(
            order_id='order_1',
            user= user,
            units = 10,
            unit_price = 5.0,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_2',
            user = user,
            units = 10,
            unit_price = 5.0,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_3',
            user = user,
            units = 10,
            unit_price = 5.1,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_4',
            user = user,
            units = 10,
            unit_price = 3.5,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_5',
            user = user,
            units = 10,
            unit_price = 3.499,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        tradeex = TradeExchangeManager()

        suggested_price = tradeex.decide_sell_price(orders)
        print("suggesed price: {0} lowest api price {1}".format(suggested_price, orders[4].unit_price))
        self.assertTrue(suggested_price < orders[4].unit_price, "final price should be lower than lowest normal sell order")
        self.assertTrue(math.fabs(suggested_price - orders[4].unit_price * 0.95) < 0.0001, "final price should be 5\% lower than lowest normal sell order")


    def test_lowest_api_trade_price_is_close_to_lowest_normal(self):
        print("-------")
        orders = []
        admin = User.objects.get(username='admin')
        user = User.objects.get(username='tttzhang2000@yahoo.com')
        orders.append(Order.objects.create(
            order_id='order_1',
            user= user,
            units = 10,
            unit_price = 5.0,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_2',
            user = user,
            units = 10,
            unit_price = 5.0,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_3',
            user = user,
            units = 10,
            unit_price = 5.1,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_4',
            user = user,
            units = 10,
            unit_price = 3.8,
            order_source = 'API',
            created_by = user,
            lastupdated_by = user
        ))

        orders.append(Order.objects.create(
            order_id='order_5',
            user = user,
            units = 10,
            unit_price = 3.799,
            order_source = 'TRADESITE',
            created_by = user,
            lastupdated_by = user
        ))

        tradeex = TradeExchangeManager()

        suggested_price = tradeex.decide_sell_price(orders)
        print("suggesed price: {0} lowest api price {1}".format(suggested_price, orders[4].unit_price))
        self.assertTrue(suggested_price < orders[4].unit_price, "final price should be lower than lowest api sell order")
        self.assertTrue(math.fabs(suggested_price - orders[4].unit_price * 0.95) < 0.0001, "final price should be 5\% lower than lowest api sell order")
