from django.test import TestCase, TransactionTestCase
from django.test import Client
from users.models import *
from views.models.orderitem import OrderItem
from controller import ordermanager

import sys, traceback

class PurchaseTestCase(TransactionTestCase):
    fixtures = ['fixture_for_tests.json']

    def test_create_sell_order(self):
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
           orderid = ordermanager.create_sell_order(order_item, 'taozhang')
           user_wallet.refresh_from_db()
           self.assertTrue(len(orderid) > 14)

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
           self.assertEqual(old_balance, user_wallet.balance)
           self.assertEqual(old_locked_balance + units, user_wallet.locked_balance )
           self.assertEqual(old_available_balance - units, user_wallet.available_balance )

           user_wallet_trans = UserWalletTransaction.objects.get(reference_order__order_id = order.order_id)
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
       except Exception as e:
           error_msg = 'test_create_sell_order() hit exception {0}'.format(
                  sys.exc_info()[0])
           print error_msg
           print traceback.format_exc()
           self.fail(error_msg)
