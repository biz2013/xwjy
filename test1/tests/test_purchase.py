#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase
from django.test import Client
from users.models import *
from views.models.orderitem import OrderItem
from controller import ordermanager

import sys, traceback, time

class PurchaseTestCase(TransactionTestCase):
    fixtures = ['fixture_for_tests.json']

    def test_create_purchase_order(self):
        print 'run test_create_purchase_order()'
        self.create_sell_order()
        print 'out of create_sell_order()'
        found_seller_order = False
        sell_order = None
        wait_count = 0
        while not found_seller_order and wait_count < 60:
            try:
                sell_order = Order.objects.get(units=100.0, unit_price=1.01)
                found_seller_order = True
            except Order.DoesNotExist:
                print 'test_create_purchase_order(): expected sell order does not exist wait for one second'
                wait_count = wait_count + 1
                time.sleep(1)
                continue
        try:
            print 'about to create buy order'
            buyer = User.objects.get(login__username='yingzhou')
            user_wallet = UserWallet.objects.get(user__login__username = 'yingzhou',
                  wallet__cryptocurrency__currency_code = 'AXFund')
            old_balance = user_wallet.balance
            old_locked_balance = user_wallet.locked_balance
            old_available_balance = user_wallet.available_balance
            units = 1.1
            available_units = 0
            unit_price = sell_order.unit_price
            unit_price_currency = sell_order.unit_price_currency
            total_amount = round(units * unit_price, 2)
            buyorder = OrderItem('', buyer.id, buyer.login.username,
                unit_price, unit_price_currency,
                # total units
                units,
                # available units
                available_units, total_amount ,
                'AXFund', None, None)
            print 'issue command to create buy order for sell order {0}'.format(sell_order.order_id)
            orderid = ordermanager.create_purchase_order(buyorder,
                          sell_order.order_id, 'yingzhou')
            print 'buy order created and start validate it'
            self.assertTrue(orderid is not None)
            order = Order.objects.get(pk=orderid)
            self.assertEqual('BUY', order.order_type)
            self.assertEqual(sell_order.order_id, order.reference_order.order_id)
            self.assertEqual('BUY_ON_ASK', order.sub_type)
            self.assertEqual('OPEN', order.status)
            self.assertEqual('AXFund', order.cryptocurrency.currency_code)
            self.assertEqual(units, order.units)
            self.assertEqual(0.0, order.units_available_to_trade)
            self.assertEqual(0.0, order.units_balance)
            self.assertEqual('yingzhou', order.created_by.username)
            self.assertEqual('yingzhou', order.lastupdated_by.username)

            print 'validate buyer user wallet balance after purchase order, there should be no changes'
            self.assertEqual(old_balance, user_wallet.balance)
            self.assertEqual(old_locked_balance, user_wallet.locked_balance )
            self.assertEqual(old_available_balance, user_wallet.available_balance )

            print 'validate purchase order user_wallet_trans'
            user_wallet_trans = UserWalletTransaction.objects.get(reference_order__order_id = order.order_id)
            self.assertEqual('CREDIT', user_wallet_trans.balance_update_type)
            self.assertEqual(user_wallet.id, user_wallet_trans.user_wallet.id)
            self.assertEqual(0.0, user_wallet_trans.balance_begin)
            self.assertEqual(0.0, user_wallet_trans.balance_end)
            self.assertEqual(0.0, user_wallet_trans.locked_balance_begin)
            self.assertEqual(0.0, user_wallet_trans.locked_balance_end)
            self.assertEqual(0.0, user_wallet_trans.available_to_trade_begin)
            self.assertEqual(0.0, user_wallet_trans.available_to_trade_end)
            self.assertEqual(u'', user_wallet_trans.reference_wallet_trxId)
            self.assertEqual(total_amount, user_wallet_trans.amount)
            self.assertEqual('OPEN BUY ORDER', user_wallet_trans.transaction_type)
            self.assertEqual('PENDING', user_wallet_trans.status)
            self.assertEqual('yingzhou', user_wallet_trans.created_by.username)
            self.assertEqual('yingzhou', user_wallet_trans.lastupdated_by.username)

        except UserWalletTransaction.DoesNotExist:
            fail('There should be one user_wallet_transaction record for the new purchase order')
        except UserWalletTransaction.MultipleObjectsReturned:
            fail('There should ONLY be one user_wallet_transaction record for the new purchase order')
        except Exception as e:
            error_msg = 'test_create_purchase_order() hit exception {0}'.format(
                  sys.exc_info()[0])
            print error_msg
            print traceback.format_exc()
            self.fail(error_msg)

    def create_sell_order(self):
       print 'run create_sell_order()'
       try:
           user = User.objects.get(login__username='taozhang')
           user_wallet = UserWallet.objects.get(user__id = user.id,
                  wallet__cryptocurrency__currency_code = 'AXFund')
           old_balance = user_wallet.balance
           old_locked_balance = user_wallet.locked_balance
           old_available_balance = user_wallet.available_balance
           unit_price = 1.01
           units = 100.0
           amount = units * unit_price
           order_item = OrderItem('', user.id, user.login.username,
               unit_price, 'CNY',
               # total units
               units,
               # available units
               units, amount,
               'AXFund', None, None)
           print 'ready to create sell order'
           orderid = ordermanager.create_sell_order(order_item, 'taozhang')
           print 'create sell order finished'
           user_wallet.refresh_from_db()
           self.assertTrue(len(orderid) > 14)

           print 'validate sell order'
           order = Order.objects.get(pk=orderid)
           self.assertEqual('SELL', order.order_type)
           self.assertEqual('taozhang', order.user.login.username)
           self.assertEqual(None, order.reference_order)
           self.assertEqual('AXFund', order.cryptocurrency.currency_code)
           self.assertEqual(None, order.payment_bill_no)
           self.assertEqual(u'', order.payment_status)
           self.assertEqual(units, order.units)
           self.assertEqual(unit_price, order.unit_price)
           self.assertEqual(units, order.units_balance)
           self.assertEqual(units, order.units_available_to_trade)
           self.assertEqual(amount, order.total_amount)
           self.assertEqual('OPEN', order.status)
           self.assertEqual('taozhang', order.created_by.username)
           self.assertEqual('taozhang', order.lastupdated_by.username)

           print 'validate seller user_wallet record'
           self.assertEqual(old_balance, user_wallet.balance)
           self.assertEqual(old_locked_balance + units, user_wallet.locked_balance )
           self.assertEqual(old_available_balance - units, user_wallet.available_balance )

           print 'validate sell order user_wallet_trans'
           user_wallet_trans = UserWalletTransaction.objects.get(reference_order__order_id = order.order_id)
           print 'get the user_wallet_trans record of the sell order'
           self.assertEqual('DEBT', user_wallet_trans.balance_update_type)
           self.assertEqual(user_wallet.id, user_wallet_trans.user_wallet.id)
           self.assertEqual(user_wallet_trans.balance_begin, user_wallet_trans.balance_end)
           self.assertEqual(user_wallet.balance, user_wallet_trans.balance_end)
           self.assertEqual(user_wallet.locked_balance, user_wallet_trans.locked_balance_end)
           self.assertEqual(user_wallet.available_balance, user_wallet_trans.available_to_trade_end)
           self.assertEqual(u'', user_wallet_trans.reference_wallet_trxId)
           self.assertEqual(amount, user_wallet_trans.amount)
           self.assertEqual('OPEN SELL ORDER', user_wallet_trans.transaction_type)
           self.assertEqual('PROCESSED', user_wallet_trans.status)
           self.assertEqual('taozhang', user_wallet_trans.created_by.username)
           self.assertEqual('taozhang', user_wallet_trans.lastupdated_by.username)
           print 'done '
       except Exception as e:
           error_msg = 'test_create_sell_order() hit exception {0}'.format(
                  sys.exc_info()[0])
           print error_msg
           print traceback.format_exc()
           self.fail(error_msg)
