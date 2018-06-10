#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase
from django.test import Client
from django.utils import timezone
from django.contrib.auth.models import User

from trading.models import *

from trading.controller.heepaymanager import HeePayManager
from trading.views.models.orderitem import OrderItem
from trading.views.models.userpaymentmethodview import UserPaymentMethodView
from trading.controller import ordermanager
from trading.controller import userpaymentmethodmanager
from trading.controller.global_utils import *
from trading.tests.setuptest import *

#from trading.forms import *

import sys, io, traceback, time, json, copy, math
from unittest.mock import Mock, MagicMock, patch
from calendar import timegm
from datetime import datetime as dt


# match the hy_bill_no in test data test_heepay_confirm.json
TEST_HY_BILL_NO='180102122300364021000081666'

heepay_reponse_template = json.load(io.open('trading/tests/data/heepay_return_success.json', 'r', encoding='utf-8'))

#mock function
def send_buy_apply_request_side_effect(payload):
    json_payload = json.loads(payload)
    json_response = copy.copy(heepay_reponse_template)
    print('copied response template is {0}'.format(json.dumps(json_response)))
    biz_content = json.loads(json_payload['biz_content'])
    print('biz_content json is {0}'.format(json.dumps(biz_content)))
    json_response['out_trade_no'] = biz_content['out_trade_no']
    json_response['hy_bill_no'] = TEST_HY_BILL_NO
    json_response['to_account'] = '15811302702'
    print('copied and templated response is {0}'.format(json.dumps(json_response)))
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
        print('run test_create_purchase_order()')
        sell_order_id = self.create_sell_order()
        print('out of create_sell_order()')
        found_seller_order = False
        sell_order = None
        wait_count = 0
        while not found_seller_order and wait_count < 60:
            try:
                sell_order = Order.objects.get(pk=sell_order_id)
                found_seller_order = True
            except Order.DoesNotExist:
                print('test_create_purchase_order(): expected sell order does not exist wait for one second')
                wait_count = wait_count + 1
                time.sleep(1)
                continue
            except Order.MultipleObjectsReturned:
                self.fail('There should ONLY be one sell order created')
        try:
            self.assertEqual('OPEN', sell_order.status)
            print('about to create buy order')
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
                'AXFund', None, None,'BUY')
            print('issue command to create buy order for sell order {0}'.format(sell_order.order_id))
            orderid = ordermanager.create_purchase_order(buyorder,
                          sell_order.order_id, 'heepay', 'yingzhou')
            ltimestamp_now = timegm(dt.utcnow().utctimetuple())
            print('buy order created and start validate it')
            self.assertTrue(orderid is not None)
            order = Order.objects.get(pk=orderid)
            self.assertEqual('BUY', order.order_type)
            self.assertEqual(sell_order.order_id, order.reference_order.order_id)
            self.assertEqual('BUY_ON_ASK', order.sub_type)
            self.assertEqual('OPEN', order.status)
            self.assertEqual('AXFund', order.cryptocurrency.currency_code)
            self.assertEqual(units, order.units)
            self.assertEqual(total_amount, order.total_amount)
            self.assertEqual(0.0, order.units_available_to_trade)
            self.assertEqual(0.0, order.units_locked)
            self.assertEqual('yingzhou', order.created_by.username)
            self.assertEqual('yingzhou', order.lastupdated_by.username)
            llastupdated_timestamp = timegm(order.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print('validate buyer user wallet balance after purchase order, there should be no changes')
            user_wallet.refresh_from_db()
            self.assertEqual(old_balance, user_wallet.balance)
            self.assertEqual(old_locked_balance, user_wallet.locked_balance )
            self.assertEqual(old_available_balance, user_wallet.available_balance )

            print('validate purchase order user_wallet_trans')
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
            self.assertEqual(units, user_wallet_trans.units)
            self.assertEqual(total_amount, user_wallet_trans.fiat_money_amount)
            self.assertEqual('heepay', user_wallet_trans.payment_provider.code)
            self.assertEqual(None, user_wallet_trans.payment_bill_no)
            self.assertEqual('UNKNOWN', user_wallet_trans.payment_status)
            self.assertEqual('OPEN BUY ORDER', user_wallet_trans.transaction_type)
            self.assertEqual('PENDING', user_wallet_trans.status)
            self.assertEqual('yingzhou', user_wallet_trans.created_by.username)
            self.assertEqual('yingzhou', user_wallet_trans.lastupdated_by.username)
            lcreated_timestamp = timegm(user_wallet_trans.created_at.utctimetuple())
            self.assertTrue(abs(lcreated_timestamp - ltimestamp_now) < 120)
            llastupdated_timestamp = timegm(user_wallet_trans.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print('validate sell order change')
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
            print(error_msg)
            print(traceback.format_exc())
            self.fail(error_msg)

    def post_payment_confirmation(self, buy_order_id):
        confirmation_json = None
        with io.open('trading/tests/data/test_heepay_confirm.json', mode='r', encoding='utf-8') as myfile:
            confirmation_json=myfile.read()
        confirmation_json = confirmation_json.replace('__ORDER_ID__', buy_order_id)
        json_data = json.loads(confirmation_json)
        hmgr = HeePayManager()
        signed_str = hmgr.create_confirmation_sign(json_data,'4AE4583FD4D240559F80ED39')
        confirmation_json = confirmation_json.replace('__SIGN__', signed_str)
        print(u'the confirmation about to send to confirmation payment is {0}'.format(confirmation_json))
        c = Client()
        response = c.post('/trading/heepay/confirm_payment/',
                            confirmation_json,
                            content_type="application/json; charset=utf-8")
        print('confirmation response is {0}'.format(response.content))
        self.assertEqual('OK', response.content.decode('utf-8'))

    def create_sell_order(self):
       print('run create_sell_order()')
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
               'AXFund', None, None,'SELL')
           print('ready to create sell order')
           orderid = ordermanager.create_sell_order(order_item, 'taozhang')
           print('create sell order finished')
           user_wallet.refresh_from_db()
           self.assertTrue(len(orderid) > 14)

           print('validate sell order')
           order = Order.objects.get(pk=orderid)
           self.assertEqual('SELL', order.order_type)
           self.assertEqual('taozhang', order.user.username)
           self.assertEqual(None, order.reference_order)
           self.assertEqual('AXFund', order.cryptocurrency.currency_code)
           self.assertEqual(units, order.units)
           self.assertEqual(unit_price, order.unit_price)
           self.assertTrue(order.selected_payment_provider is None)
           self.assertEqual(0, order.units_locked)
           self.assertEqual(units, order.units_available_to_trade)
           self.assertEqual(amount, order.total_amount)
           self.assertEqual('OPEN', order.status)
           self.assertEqual('taozhang', order.created_by.username)
           self.assertEqual('taozhang', order.lastupdated_by.username)

           print('validate seller user_wallet record')
           self.assertEqual(old_balance, user_wallet.balance)
           self.assertEqual(old_locked_balance + units, user_wallet.locked_balance )
           self.assertEqual(old_available_balance - units, user_wallet.available_balance )

           try:
               # should no transaction for sell order for now
               UserWalletTransaction.objects.get(reference_order__order_id = orderid, )
               self.fail("There should be no user wallet transaction after creating sell order")
           except UserWalletTransaction.DoesNotExist:
               print('create_sell_order(): Good! no extra user wallet transaction after creating sell order')
           except UserWalletTransaction.MultipleObjectsReturned:
               self.fail("There should be no user wallet transaction, not to mention multiple, after creating sell order")
           return orderid
       except Exception as e:
           error_msg = 'test_create_sell_order() hit exception {0}'.format(
                  sys.exc_info()[0])
           print(error_msg)
           print(traceback.format_exc())
           self.fail(error_msg)

    @patch('trading.controller.heepaymanager.HeePayManager.send_buy_apply_request', side_effect=send_buy_apply_request_side_effect)
    #@mock.patch('controller.global_utils.user_session_is_valid', return_value=True)
    #@mock.patch('controller.global_utils.get_user_session_value', side_effect=get_buyer)
    def test_2_purchase_view(self, send_buy_apply_request_function):
        print('test_2_purchase_view():...')
        ltimestamp_now = timegm(dt.utcnow().utctimetuple())
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

            print('test_2_purchase_view(): create sell order...')
            sell_order_id = self.create_sell_order()
            sell_order = Order.objects.get(pk=sell_order_id)
            old_sell_order_units = sell_order.units
            old_sell_order_units_locked = sell_order.units_locked
            old_sell_order_units_available = sell_order.units_available_to_trade
            old_sell_order_amount = sell_order.total_amount
            old_sell_order_unit_price = sell_order.unit_price
            old_sell_order_unit_price_currency = sell_order.unit_price_currency

            print('test_2_purchase_view(): create buyer order based on sell order through client call...')
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
            response = c.post('/trading/purchase/createorder2/', buyorder_dict
                )
            print('test_2_purchase_view(): purchase view return {0}'.format(response.content))
            #print 'purchase view template {0}'.format(response.templates)
            self.assertEqual(200, response.status_code)

            print('test_2_purchase_view(): verify sell_order balance change...')
            sell_order.refresh_from_db()
            self.assertEqual(old_sell_order_units, sell_order.units)
            self.assertEqual(old_sell_order_units_locked + purchase_units, sell_order.units_locked)
            self.assertEqual(old_sell_order_units_available - purchase_units, sell_order.units_available_to_trade)
            self.assertEqual('OPEN', sell_order.status)

            print('test_2_purchase_view(): verify seller wallet balance change...')
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
                print('test_2_purchase_view(): Good! no extra user wallet transaction for sell order yet')

            print('test_2_purchase_view(): verify purchase order ...')
            purchase_order = Order.objects.get(reference_order__order_id = sell_order.order_id)
            self.assertEqual('PAYING', purchase_order.status)
            self.assertEqual('BUY', purchase_order.order_type)
            self.assertEqual('BUY_ON_ASK', purchase_order.sub_type)
            self.assertEqual('PAYING', purchase_order.status)
            self.assertEqual('heepay', purchase_order.selected_payment_provider.code)
            self.assertEqual('AXFund', purchase_order.cryptocurrency.currency_code)
            self.assertEqual(purchase_units, purchase_order.units)
            self.assertEqual(0.0, purchase_order.units_available_to_trade)
            self.assertEqual(0.0, purchase_order.units_locked)
            self.assertEqual(old_sell_order_unit_price, purchase_order.unit_price)
            self.assertEqual(old_sell_order_unit_price_currency, purchase_order.unit_price_currency)
            self.assertEqual('yingzhou', purchase_order.created_by.username)
            self.assertEqual('yingzhou', purchase_order.lastupdated_by.username)
            llastupdated_timestamp = timegm(purchase_order.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print('test_2_purchase_view(): verify purchase order {0} user wallet trans ...'.format(purchase_order.order_id))
            buyer_wallet_trans = UserWalletTransaction.objects.get(reference_order__order_id = purchase_order.order_id)
            self.assertEqual('CREDIT', buyer_wallet_trans.balance_update_type)
            self.assertEqual(buyer_wallet.id, buyer_wallet_trans.user_wallet.id)
            self.assertEqual(0.0, buyer_wallet_trans.balance_begin)
            self.assertEqual(0.0, buyer_wallet_trans.balance_end)
            self.assertEqual(0.0, buyer_wallet_trans.locked_balance_begin)
            self.assertEqual(0.0, buyer_wallet_trans.locked_balance_end)
            self.assertEqual(0.0, buyer_wallet_trans.available_to_trade_begin)
            self.assertEqual(0.0, buyer_wallet_trans.available_to_trade_end)
            self.assertEqual(u'', buyer_wallet_trans.reference_wallet_trxId)
            self.assertEqual('CREDIT', buyer_wallet_trans.balance_update_type)
            self.assertEqual(purchase_units, buyer_wallet_trans.units)
            self.assertEqual(total_amount, buyer_wallet_trans.fiat_money_amount)
            self.assertEqual(TEST_HY_BILL_NO, buyer_wallet_trans.payment_bill_no)
            self.assertEqual('heepay', buyer_wallet_trans.payment_provider.code)
            self.assertEqual('UNKNOWN', buyer_wallet_trans.payment_status)
            self.assertEqual('OPEN BUY ORDER', buyer_wallet_trans.transaction_type)
            self.assertEqual('PENDING', buyer_wallet_trans.status)
            self.assertEqual('yingzhou', buyer_wallet_trans.created_by.username)
            self.assertEqual('yingzhou', buyer_wallet_trans.lastupdated_by.username)
            lcreated_timestamp = timegm(buyer_wallet_trans.created_at.utctimetuple())
            self.assertTrue(abs(lcreated_timestamp - ltimestamp_now) < 120)
            llastupdated_timestamp = timegm(buyer_wallet_trans.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print('test_2_purchase_view(): verify buyer wallet balance ...')
            buyer_wallet.refresh_from_db()
            self.assertEqual(old_buyer_balance, buyer_wallet.balance)
            self.assertEqual(old_buyer_locked_balance, buyer_wallet.locked_balance)
            self.assertEqual(old_buyer_available_balance, buyer_wallet.available_balance)

            #-----------------------------------------------------------------
            print('test_2_purchase_view(): create confirmation ...')
            self.post_payment_confirmation(purchase_order.order_id)

            print('test_2_purchase_view(): there should be just 2 trans ...')
            wallet_trans = UserWalletTransaction.objects.all()
            self.assertEqual(1, len(wallet_trans), 'There should be 1 wallet trans after receiving confirmation')

            #After heepay notification, only update the purchase order and its purchase trans, so we
            #verify that first.
            print('test_2_purchase_view(): verify buyer wallet after heepay notifiction ...')
            buyer_wallet_trans.refresh_from_db()
            self.assertEqual('CREDIT', buyer_wallet_trans.balance_update_type)
            self.assertEqual(purchase_order.order_id, buyer_wallet_trans.reference_order.order_id)
            self.assertEqual(buyer_wallet.id, buyer_wallet_trans.user_wallet.id)
            self.assertEqual(old_buyer_balance, buyer_wallet_trans.balance_begin)
            self.assertEqual(buyer_wallet.balance, buyer_wallet_trans.balance_end)
            self.assertEqual(old_buyer_locked_balance, buyer_wallet_trans.locked_balance_begin)
            self.assertEqual(buyer_wallet.locked_balance, buyer_wallet_trans.locked_balance_end)
            self.assertEqual(old_buyer_available_balance, buyer_wallet_trans.available_to_trade_begin)
            self.assertEqual(buyer_wallet.available_balance, buyer_wallet_trans.available_to_trade_end)
            self.assertEqual(u'', buyer_wallet_trans.reference_wallet_trxId)
            self.assertEqual(purchase_units, buyer_wallet_trans.units)
            self.assertEqual(total_amount, buyer_wallet_trans.fiat_money_amount)
            self.assertEqual(TEST_HY_BILL_NO, buyer_wallet_trans.payment_bill_no)
            self.assertEqual('heepay', buyer_wallet_trans.payment_provider.code)
            self.assertEqual('SUCCESS', buyer_wallet_trans.payment_status)
            self.assertEqual('OPEN BUY ORDER', buyer_wallet_trans.transaction_type)
            self.assertEqual('PENDING', buyer_wallet_trans.status)
            self.assertEqual('yingzhou', buyer_wallet_trans.created_by.username)
            self.assertEqual('admin', buyer_wallet_trans.lastupdated_by.username)
            lcreated_timestamp = timegm(buyer_wallet_trans.created_at.utctimetuple())
            self.assertTrue(abs(lcreated_timestamp - ltimestamp_now) < 120)
            llastupdated_timestamp = timegm(buyer_wallet_trans.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print('test_2_purchase_view(): verify purchase after heepay notification ...')
            purchase_order.refresh_from_db()
            self.assertEqual('PAID', purchase_order.status)
            self.assertEqual('BUY', purchase_order.order_type)
            self.assertEqual('BUY_ON_ASK', purchase_order.sub_type)
            self.assertEqual('heepay', purchase_order.selected_payment_provider.code)
            self.assertEqual('AXFund', purchase_order.cryptocurrency.currency_code)
            self.assertEqual(old_sell_order_unit_price, purchase_order.unit_price)
            self.assertEqual(old_sell_order_unit_price_currency, purchase_order.unit_price_currency)
            self.assertEqual(purchase_units, purchase_order.units)
            self.assertEqual(0.0, purchase_order.units_available_to_trade)
            self.assertEqual(0.0, purchase_order.units_locked)
            self.assertEqual('yingzhou', purchase_order.created_by.username)
            self.assertEqual('admin', purchase_order.lastupdated_by.username)
            llastupdated_timestamp = timegm(purchase_order.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            #----------------------------------------------------------------------------
            # now run the order batch process to create the update seller order/trans
            # and update both buyer/seller's wallet

            # turn the confirmation timeout out for now, otherwise the order batch process
            # won't commit the change
            sitesettings = SiteSettings.objects.all()[0]
            sitesettings.confirmation_timeout_insec = 0
            sitesettings.save()

            c = Client()
            c.login(username='yingzhou', password='user@123')
            response = c.get('/trading/account/cron/order_batch_process/')
            print('test_2_purchase_view(): order batch process return {0}'.format(response.content))
            #print 'purchase view template {0}'.format(response.templates)
            self.assertEqual(200, response.status_code)

            wallet_trans = UserWalletTransaction.objects.all()
            self.assertEqual(2, len(wallet_trans), 'There should be 2 wallet trans after receiving confirmation')

            print('test_2_purchase_view(): verify seller wallet balance ...')
            seller_wallet.refresh_from_db()
            self.assertEqual(old_seller_balance  - purchase_units, seller_wallet.balance)
            self.assertEqual(old_seller_locked_balance + sell_order.units - purchase_units , seller_wallet.locked_balance)
            self.assertEqual(old_seller_available_balance - sell_order.units, seller_wallet.available_balance)
            self.assertTrue(math.fabs(seller_wallet.balance - seller_wallet.locked_balance
                              - seller_wallet.available_balance) < 0.00000001)

            print('test_2_purchase_view(): verify seller wallet trans at the end ...')
            seller_wallet_trans = UserWalletTransaction.objects.get(reference_order__order_id = sell_order.order_id)
            self.assertEqual('DEBT', seller_wallet_trans.balance_update_type)
            self.assertEqual(sell_order.order_id, seller_wallet_trans.reference_order.order_id)
            self.assertEqual(seller_wallet.id, seller_wallet_trans.user_wallet.id)
            self.assertEqual(old_seller_balance, seller_wallet_trans.balance_begin)
            self.assertEqual(seller_wallet.balance, seller_wallet_trans.balance_end)
            self.assertEqual(old_seller_locked_balance + sell_order.units, seller_wallet_trans.locked_balance_begin)
            self.assertEqual(seller_wallet.locked_balance, seller_wallet_trans.locked_balance_end)
            self.assertTrue(math.fabs(seller_wallet_trans.locked_balance_begin - seller_wallet_trans.units
                   - seller_wallet_trans.locked_balance_end)<0.00000001)
            self.assertEqual(old_seller_available_balance - sell_order.units, seller_wallet_trans.available_to_trade_begin)
            self.assertEqual(seller_wallet.available_balance, seller_wallet_trans.available_to_trade_end)
            self.assertTrue(math.fabs(seller_wallet_trans.available_to_trade_begin - seller_wallet_trans.available_to_trade_end)<0.00000001)
            self.assertEqual(u'', seller_wallet_trans.reference_wallet_trxId)
            self.assertEqual(purchase_units, seller_wallet_trans.units)
            self.assertEqual(total_amount, seller_wallet_trans.fiat_money_amount)
            self.assertEqual(TEST_HY_BILL_NO, seller_wallet_trans.payment_bill_no)
            self.assertEqual('heepay', seller_wallet_trans.payment_provider.code)
            self.assertEqual('SUCCESS', seller_wallet_trans.payment_status)
            self.assertEqual('DELIVER ON PURCHASE', seller_wallet_trans.transaction_type)
            self.assertEqual('PROCESSED', seller_wallet_trans.status)
            self.assertEqual('admin', seller_wallet_trans.created_by.username)
            self.assertEqual('admin', seller_wallet_trans.lastupdated_by.username)
            lcreated_timestamp = timegm(seller_wallet_trans.created_at.utctimetuple())
            self.assertTrue(abs(lcreated_timestamp - ltimestamp_now) < 120)
            llastupdated_timestamp = timegm(seller_wallet_trans.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print('test_2_purchase_view(): verify sell order change ...')
            sell_order.refresh_from_db()
            self.assertEqual('PARTIALFILLED', sell_order.status)
            self.assertEqual(old_sell_order_units, sell_order.units)
            self.assertEqual(old_sell_order_units_locked + purchase_units - purchase_order.units, sell_order.units_locked)
            self.assertEqual(old_sell_order_units_available - purchase_units, sell_order.units_available_to_trade)
            self.assertEqual('SELL', sell_order.order_type)
            self.assertEqual('taozhang', sell_order.user.username)
            self.assertEqual(None, sell_order.reference_order)
            self.assertEqual('AXFund', sell_order.cryptocurrency.currency_code)
            self.assertEqual(old_sell_order_unit_price, sell_order.unit_price)
            self.assertEqual(old_sell_order_unit_price_currency,sell_order.unit_price_currency)
            self.assertTrue(sell_order.selected_payment_provider is None)
            self.assertEqual(old_sell_order_amount, sell_order.total_amount)
            self.assertEqual('taozhang', sell_order.created_by.username)
            self.assertEqual('admin', sell_order.lastupdated_by.username)
            llastupdated_timestamp = timegm(sell_order.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print('test_2_purchase_view(): verify buyer wallet balance ...')
            buyer_wallet.refresh_from_db()
            self.assertEqual(old_buyer_balance + purchase_units, buyer_wallet.balance)
            self.assertEqual(old_buyer_locked_balance, buyer_wallet.locked_balance)
            self.assertEqual(old_buyer_available_balance + purchase_units, buyer_wallet.available_balance)
            self.assertTrue(math.fabs(buyer_wallet.balance - buyer_wallet.locked_balance
                              - buyer_wallet.available_balance)<0.00000001)

            print('test_2_purchase_view(): verify buyer wallet trans at the end ...')
            buyer_wallet_trans.refresh_from_db()
            self.assertEqual('CREDIT', buyer_wallet_trans.balance_update_type)
            self.assertEqual(purchase_order.order_id, buyer_wallet_trans.reference_order.order_id)
            self.assertEqual(buyer_wallet.id, buyer_wallet_trans.user_wallet.id)
            self.assertEqual(old_buyer_balance, buyer_wallet_trans.balance_begin)
            self.assertEqual(buyer_wallet.balance, buyer_wallet_trans.balance_end)
            self.assertEqual(old_buyer_locked_balance, buyer_wallet_trans.locked_balance_begin)
            self.assertEqual(buyer_wallet.locked_balance, buyer_wallet_trans.locked_balance_end)
            self.assertEqual(old_buyer_available_balance, buyer_wallet_trans.available_to_trade_begin)
            self.assertEqual(buyer_wallet.available_balance, buyer_wallet_trans.available_to_trade_end)
            self.assertEqual(u'', buyer_wallet_trans.reference_wallet_trxId)
            self.assertEqual(purchase_units, buyer_wallet_trans.units)
            self.assertEqual(total_amount, buyer_wallet_trans.fiat_money_amount)
            self.assertEqual(TEST_HY_BILL_NO, buyer_wallet_trans.payment_bill_no)
            self.assertEqual('heepay', buyer_wallet_trans.payment_provider.code)
            self.assertEqual('SUCCESS', buyer_wallet_trans.payment_status)
            self.assertEqual('OPEN BUY ORDER', buyer_wallet_trans.transaction_type)
            self.assertEqual('PROCESSED', buyer_wallet_trans.status)
            self.assertEqual('yingzhou', buyer_wallet_trans.created_by.username)
            self.assertEqual('admin', buyer_wallet_trans.lastupdated_by.username)
            lcreated_timestamp = timegm(buyer_wallet_trans.created_at.utctimetuple())
            self.assertTrue(abs(lcreated_timestamp - ltimestamp_now) < 120)
            llastupdated_timestamp = timegm(buyer_wallet_trans.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

            print('test_2_purchase_view(): verify purchase  order changes ...')
            purchase_order.refresh_from_db()
            self.assertEqual('FILLED', purchase_order.status)
            self.assertEqual('BUY', purchase_order.order_type)
            self.assertEqual('BUY_ON_ASK', purchase_order.sub_type)
            self.assertEqual('heepay', purchase_order.selected_payment_provider.code)
            self.assertEqual('AXFund', purchase_order.cryptocurrency.currency_code)
            self.assertEqual(old_sell_order_unit_price, purchase_order.unit_price)
            self.assertEqual(old_sell_order_unit_price_currency, purchase_order.unit_price_currency)
            self.assertEqual(purchase_units, purchase_order.units)
            self.assertEqual(0.0, purchase_order.units_available_to_trade)
            self.assertEqual(0.0, purchase_order.units_locked)
            self.assertEqual('yingzhou', purchase_order.created_by.username)
            self.assertEqual('admin', purchase_order.lastupdated_by.username)
            llastupdated_timestamp = timegm(purchase_order.lastupdated_at.utctimetuple())
            self.assertTrue(abs(llastupdated_timestamp - ltimestamp_now) < 120)

        except Exception as e:
            error_msg = 'test_2_purchase_view(): hit exception {0}'.format(
                  sys.exc_info()[0])
            print(error_msg)
            print(traceback.format_exc())
            self.fail(error_msg)

    def test_record_datetime_operation(self):
        sell_order_id = self.create_sell_order()
        found_seller_order = False
        sell_order = None
        wait_count = 0
        while not found_seller_order and wait_count < 60:
            try:
                sell_order = Order.objects.get(pk=sell_order_id)
                found_seller_order = True
            except Order.DoesNotExist:
                print('test_create_purchase_order(): expected sell order does not exist wait for one second')
                wait_count = wait_count + 1
                time.sleep(1)
                continue
            except Order.MultipleObjectsReturned:
                self.fail('There should ONLY be one sell order created')
        try:

            print('order lastupdated at {0}'.format(sell_order.lastupdated_at))
            now_aware = timezone.now()
            print('now aware is {0}'.format(now_aware))
            timediff = now_aware - sell_order.lastupdated_at
            print('the order and now\'s difference is {0}'.format(timediff.total_seconds()))
        except Exception as e:
            error_msg = 'test_create_purchase_order() hit exception {0}'.format(
                  sys.exc_info()[0])
            print(error_msg)
            print(traceback.format_exc())
            self.fail(error_msg)
