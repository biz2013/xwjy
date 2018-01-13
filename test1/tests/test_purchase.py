#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase
from django.test import Client
from django.contrib.auth.models import User

from users.models import *

from controller.heepaymanager import HeePayManager
from views.models.orderitem import OrderItem
from views.models.userpaymentmethodview import UserPaymentMethodView
from controller import ordermanager, loginmanager
from controller import userpaymentmethodmanager
from controller.global_utils import *

from test1.forms import *

import sys, io, traceback, time, json, copy
from mock import Mock, MagicMock, patch, mock
from calendar import timegm
from datetime import datetime as dt
from setuptest import *

TEST_HY_BILL_NO='Test_heepay_bill_no'

heepay_reponse_template = json.load(io.open('tests/data/heepay_return_success.json', 'r', encoding='utf-8'))

#mock function
def send_buy_apply_request_side_effect(payload):
    json_payload = json.loads(payload)
    json_response = copy.copy(heepay_reponse_template)
    print 'copied response template is {0}'.format(json.dumps(json_response))
    biz_content = json.loads(json_payload['biz_content'])
    print 'biz_content json is {0}'.format(json.dumps(biz_content))
    json_response['out_trade_no'] = biz_content['out_trade_no']
    json_response['hy_bill_no'] = TEST_HY_BILL_NO
    json_response['to_account'] = '15811302702'
    print 'copied and templated response is {0}'.format(json.dumps(json_response))
    return 200, 'Ok', json.dumps(json_response)

#mock function
def get_buyer(request):
    buyer = User.objects.get(username='yingzhou')
    return 'yingzhou', buyer.id

class PurchaseTestCase(TransactionTestCase):
    fixtures = ['fixture_for_tests.json']

    def setUp(self):
        try:
            User.objects.get(username='taozhang')
        except User.DoesNotExist:
            setup_test()

    def test_1_create_purchase_order(self):
        print 'run test_create_purchase_order()'
        sell_order_id = self.create_sell_order()
        print 'out of create_sell_order()'
        found_seller_order = False
        sell_order = None
        wait_count = 0
        while not found_seller_order and wait_count < 60:
            try:
                sell_order = Order.objects.get(pk=sell_order_id)
                found_seller_order = True
            except Order.DoesNotExist:
                print 'test_create_purchase_order(): expected sell order does not exist wait for one second'
                wait_count = wait_count + 1
                time.sleep(1)
                continue
            except Order.MultipleObjectsReturned:
                fail('There should ONLY be one sell order created')
        try:
            print 'about to create buy order'
            buyer = User.objects.get(username='yingzhou')
            user_wallet = UserWallet.objects.get(user__username = 'yingzhou',
                  wallet__cryptocurrency__currency_code = 'AXFund')
            # remember old buyer user wallet balance
            old_balance = user_wallet.balance
            old_locked_balance = user_wallet.locked_balance
            old_available_balance = user_wallet.available_balance

            # remember old sell order's balance
            old_sell_order_units_locked = sell_order.units_locked
            old_sell_order_units = sell_order.units
            old_sell_order_units_available = sell_order.units_available_to_trade

            units = 1.1
            available_units = 0
            unit_price = sell_order.unit_price
            unit_price_currency = sell_order.unit_price_currency
            total_amount = round(units * unit_price, 2)
            buyorder = OrderItem('', buyer.id, buyer.username,
                unit_price, unit_price_currency,
                # total units
                units,
                # available units
                available_units, total_amount ,
                'AXFund', None, None)
            print 'issue command to create buy order for sell order {0}'.format(sell_order.order_id)
            orderid = ordermanager.create_purchase_order(buyorder,
                          sell_order.order_id, 'yingzhou')
            ltimestamp_now = timegm(dt.utcnow().utctimetuple())
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
            self.assertEqual(0.0, order.units_locked)
            self.assertEqual('yingzhou', order.created_by.username)
            self.assertEqual('yingzhou', order.lastupdated_by.username)
            llastupdated_timestamp = timegm(order.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print 'validate buyer user wallet balance after purchase order, there should be no changes'
            user_wallet.refresh_from_db()
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
            self.assertEqual(units, user_wallet_trans.amount)
            self.assertEqual('OPEN BUY ORDER', user_wallet_trans.transaction_type)
            self.assertEqual('PENDING', user_wallet_trans.status)
            self.assertEqual('yingzhou', user_wallet_trans.created_by.username)
            self.assertEqual('yingzhou', user_wallet_trans.lastupdated_by.username)
            lcreated_timestamp = timegm(user_wallet_trans.created_at.utctimetuple())
            self.assertTrue(abs(lcreated_timestamp - ltimestamp_now) < 120)
            llastupdated_timestamp = timegm(user_wallet_trans.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print 'validate sell order change'
            sell_order.refresh_from_db()
            self.assertEqual('LOCKED', sell_order.status)
            self.assertEqual(old_sell_order_units, sell_order.units)
            self.assertEqual(old_sell_order_units_locked + buyorder.total_units, sell_order.units_locked)
            self.assertEqual(old_sell_order_units_available - buyorder.total_units, sell_order.units_available_to_trade)
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
           user = User.objects.get(username='taozhang')
           user_wallet = UserWallet.objects.get(user__id = user.id,
                  wallet__cryptocurrency__currency_code = 'AXFund')
           old_balance = user_wallet.balance
           old_locked_balance = user_wallet.locked_balance
           old_available_balance = user_wallet.available_balance
           unit_price = 1.01
           units = 100.0
           amount = units * unit_price
           order_item = OrderItem('', user.id, user.username,
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
           self.assertEqual('taozhang', order.user.username)
           self.assertEqual(None, order.reference_order)
           self.assertEqual('AXFund', order.cryptocurrency.currency_code)
           self.assertEqual(None, order.payment_bill_no)
           self.assertEqual(u'', order.payment_status)
           self.assertEqual(units, order.units)
           self.assertEqual(unit_price, order.unit_price)
           self.assertTrue(order.selected_payment_provider is None)
           self.assertEqual(0, order.units_locked)
           self.assertEqual(units, order.units_available_to_trade)
           self.assertEqual(amount, order.total_amount)
           self.assertEqual('OPEN', order.status)
           self.assertEqual('taozhang', order.created_by.username)
           self.assertEqual('taozhang', order.lastupdated_by.username)

           print 'validate seller user_wallet record'
           self.assertEqual(old_balance, user_wallet.balance)
           self.assertEqual(old_locked_balance + units, user_wallet.locked_balance )
           self.assertEqual(old_available_balance - units, user_wallet.available_balance )

           try:
               # should no transaction for sell order for now
               UserWalletTransaction.objects.get(reference_order__order_id = sell_order.order_id, )
               self.fail("There should be no user wallet transaction after creating sell order")
           except UserWalletTransaction.DoesNotExist:
               print 'create_sell_order(): Good! no extra user wallet transaction after creating sell order'
           except UserWalletTransaction.MultipleObjectsReturned:
               self.fail("There should be no user wallet transaction, not to mention multiple, after creating sell order")
           return orderid
       except Exception as e:
           error_msg = 'test_create_sell_order() hit exception {0}'.format(
                  sys.exc_info()[0])
           print error_msg
           print traceback.format_exc()
           self.fail(error_msg)

    @mock.patch('controller.heepaymanager.HeePayManager.send_buy_apply_request', side_effect=send_buy_apply_request_side_effect)
    #@mock.patch('controller.global_utils.user_session_is_valid', return_value=True)
    #@mock.patch('controller.global_utils.get_user_session_value', side_effect=get_buyer)
    def test_2_purchase_view(self, send_buy_apply_request_function):
        print 'test_2_purchase_view():...'
        try:
            # get seller initial info
            seller = User.objects.get(username='taozhang')
            seller_wallet = UserWallet.objects.get(user__id = seller.id,
                  wallet__cryptocurrency__currency_code = 'AXFund')
            old_seller_balance = seller_wallet.balance
            old_seller_locked_balance = seller_wallet.locked_balance
            old_seller_available_balance = seller_wallet.available_balance

            # get buyer initial info
            buyer = User.objects.get(username='yingzhou')
            buyer_wallet = UserWallet.objects.get(user__id = buyer.id,
                  wallet__cryptocurrency__currency_code = 'AXFund')
            old_buyer_balance = buyer_wallet.balance
            old_buyer_locked_balance = buyer_wallet.locked_balance
            old_buyer_available_balance = buyer_wallet.available_balance

            print 'test_2_purchase_view(): create sell order...'
            sell_order_id = self.create_sell_order()
            sell_order = Order.objects.get(pk=sell_order_id)
            old_sell_order_units = sell_order.units
            old_sell_order_units_locked = sell_order.units_locked
            old_sell_order_units_available = sell_order.units_available_to_trade

            print 'test_2_purchase_view(): create buyer order based on sell order through client call...'
            purchase_units = 2.1
            total_amount = round(sell_order.unit_price * purchase_units,2)
            total_amount_str = str(total_amount)
            buyorder_dict = { 'reference_order_id': sell_order_id,
                    'owner_user_id': str(seller.id),
                    'quantity': purchase_units,
                    'available_units': str(sell_order.units_available_to_trade),
                    'unit_price' : str(sell_order.unit_price),
                    'seller_payment_provider': 'heepay',
                    'crypto': 'AXFund',
                    'total_amount': total_amount_str }
            c = Client()
            c.login(username='yingzhou', password='user@123')
            response = c.post('/purchase/createorder2/', buyorder_dict
                )
            print 'test_2_purchase_view(): purchase view return {0}'.format(response.content)
            #print 'purchase view template {0}'.format(response.templates)
            self.assertEqual(200, response.status_code)

            print 'test_2_purchase_view(): verify sell_order balance change...'
            sell_order.refresh_from_db()
            self.assertEqual(old_sell_order_units, sell_order.units)
            self.assertEqual(old_sell_order_units_locked + purchase_units, sell_order.units_locked)
            self.assertEqual(old_sell_order_units_available - purchase_units, sell_order.units_available_to_trade)
            self.assertEqual('OPEN', sell_order.status)

            print 'test_2_purchase_view(): verify seller wallet balance change...'
            seller_wallet.refresh_from_db()
            self.assertEqual(old_seller_balance, seller_wallet.balance)
            self.assertEqual(old_seller_locked_balance + sell_order.units, seller_wallet.locked_balance)
            self.assertEqual(old_seller_available_balance - sell_order.units, seller_wallet.available_balance)

            wallet_trans = UserWalletTransaction.objects.all()
            count_of_wallet_trans = len(wallet_trans)
            if (count_of_wallet_trans != 1):
                self.fail('There should be 1 wallet trans but we hit {0}'.format(count_of_wallet_trans))

            try:
                # should no transaction for sell order for now
                UserWalletTransaction.objects.get(reference_order__order_id = sell_order.order_id, )
                self.fail("There should be no user wallet transaction for the sell order at this point")
            except UserWalletTransaction.DoesNotExist:
                print 'test_2_purchase_view(): Good! no extra user wallet transaction for sell order yet'

            print 'test_2_purchase_view(): verify purchase order ...'
            purchase_order = Order.objects.get(reference_order__order_id = sell_order.order_id)
            self.assertEqual('')
            self.assertEqual('BUY', purchase_order.order_type)
            self.assertEqual('BUY_ON_ASK', purchase_order.sub_type)
            self.assertEqual('PAYING', purchase_order.status)
            self.assertEqual('UNKNOWN', purchase_order.payment_status)
            self.assertEqual('AXFund', purchase_order.cryptocurrency.currency_code)
            self.assertEqual(TEST_HY_BILL_NO, purchase_order.payment_bill_no)
            self.assertEqual('heepay', purchase_order.payment_provider.code)
            self.assertEqual(purchase_units, purchase_order.units)
            self.assertEqual(0.0, purchase_order.units_available_to_trade)
            self.assertEqual(0.0, purchase_order.units_locked)
            self.assertEqual('yingzhou', purchase_order.created_by.username)
            self.assertEqual('yingzhou', purchase_order.lastupdated_by.username)
            llastupdated_timestamp = timegm(purchase_order.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print 'test_2_purchase_view(): verify purchase order user wallet trans ...'
            user_wallet_trans = UserWalletTransaction.objects.get(reference_order__order_id = purchase_order.order_id)
            self.assertEqual('CREDIT', user_wallet_trans.balance_update_type)
            self.assertEqual(user_wallet.id, user_wallet_trans.user_wallet.id)
            self.assertEqual(0.0, user_wallet_trans.balance_begin)
            self.assertEqual(0.0, user_wallet_trans.balance_end)
            self.assertEqual(0.0, user_wallet_trans.locked_balance_begin)
            self.assertEqual(0.0, user_wallet_trans.locked_balance_end)
            self.assertEqual(0.0, user_wallet_trans.available_to_trade_begin)
            self.assertEqual(0.0, user_wallet_trans.available_to_trade_end)
            self.assertEqual(u'', user_wallet_trans.reference_wallet_trxId)
            self.assertEqual('CREDIT', user_wallet_trans.balance_update_type)
            self.assertEqual(purchase_units, user_wallet_trans.amount)
            self.assertEqual('OPEN BUY ORDER', user_wallet_trans.transaction_type)
            self.assertEqual('PENDING', user_wallet_trans.status)
            self.assertEqual('yingzhou', user_wallet_trans.created_by.username)
            self.assertEqual('yingzhou', user_wallet_trans.lastupdated_by.username)
            lcreated_timestamp = timegm(user_wallet_trans.created_at.utctimetuple())
            self.assertTrue(abs(lcreated_timestamp - ltimestamp_now) < 120)
            llastupdated_timestamp = timegm(user_wallet_trans.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

        except Exception as e:
            error_msg = 'test_2_purchase_view(): hit exception {0}'.format(
                  sys.exc_info()[0])
            print error_msg
            print traceback.format_exc()
            self.fail(error_msg)

    def test_3_payconfirmation(self):
        try:
            seller_wallet = UserWallet.objects.get(user__username='taozhang',
                   wallet__cryptocurrency__currency_code = 'AXFund')
            seller_old_balance = seller_wallet.balance
            seller_old_locked_balance = seller_wallet.locked_balance
            seller_old_available_balance = seller_wallet.available_balance

            buyer_wallet = UserWallet.objects.get(user__username='yingzhou',
                   wallet__cryptocurrency__currency_code = 'AXFund')
            buyer_old_balance = seller_wallet.balance
            buyer_old_locked_balance = seller_wallet.locked_balance
            buyer_old_available_balance = seller_wallet.available_balance

            unit_price = 1.01
            unit_price_currency = 'CNY'
            units = 100.0
            amount = units * unit_price
            order_item = OrderItem('', seller_wallet.user.id,
               seller_wallet.user.username,
               unit_price, unit_price_currency,
               # total units
               units,
               # available units
               units, amount,
               'AXFund', None, None)
            print 'ready to create sell order'
            sell_order_id = ordermanager.create_sell_order(order_item, 'taozhang')

            buy_units = 1.1
            available_units = 0
            total_amount = round(buy_units * unit_price, 2)
            buyorder = OrderItem('', buyer_wallet.id,
                buyer_wallet.user.username,
                unit_price, unit_price_currency,
                # total units
                units,
                # available units
                available_units, total_amount ,
                'AXFund', None, None)
            print 'issue command to create buy order for sell order {0}'.format(sell_order_id)
            buy_order_id = ordermanager.create_purchase_order(buyorder,
                          sell_order_id, 'yingzhou')

            sell_order_begin = Order.objects.get(pk=sell_order_id)
            buy_order_begin = Order.objects.get(pk=buy_order_id)
            confirmation_json = None
            with open('tests/data/test_heepay_confirm.json', 'r') as myfile:
                confirmation_json=myfile.read()
            confirmation_json = confirmation_json.replace('__ORDER_ID__', buy_order_id)
            json_data = json.loads(confirmation_json)
            hmgr = HeePayManager()
            signed_str = hmgr.create_confirmation_sign(json_data,'4AE4583FD4D240559F80ED39')
            confirmation_json = confirmation_json.replace('__SIGN__', signed_str)
            print 'the confirmation about to send to confirmation payment is {0}'.format(confirmation_json)
            c = Client()
            response = c.post('/heepay/confirm_payment/',
                                confirmation_json,
                                content_type="application/json; charset=utf-8")
            print 'confirmation response is {0}'.format(response.content)
            self.assertEqual('OK', response.content.decode('utf-8'))



        except Exception as e:
            error_msg = 'test_3_payconfirmation() hit exception {0}'.format(
                  sys.exc_info()[0])
            print error_msg
            print traceback.format_exc()
            self.fail(error_msg)
