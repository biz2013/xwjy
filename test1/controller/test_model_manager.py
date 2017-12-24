#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import datetime as dt
import pytz

from users.models import *
from views.models.orderitem import OrderItem
from views.models.useraccountinfo import UserAccountInfo
from views.models.userpaymentmethodview import UserPaymentMethodView
from controller.heepaymanager import HeePayManager

class ModelManager(object):
   def create_purchase_order(self, username, reference_order_id,
         units, unit_price, total_amount):
       order = Order()
       order.user = User()
       order.user.login = UserLogin()
       order.user.login.username = id_username
       order.reference_order = Order()
       order.reference_order.id = reference_order_id
       order.units = units
       order.unit_price = unit_price
       order.unit_price_currency = 'CNY'
       order.order_type ='BUY'
       return order

   def query_active_sell_orders(self):
       orders= []
       orders = []
       orders.append(OrderItem(1,1, 'taozhang', 1.011, 'CYN', 200.0,90.0,
              '2017-12-10 00:00:00 UTC', 'OPEN'))
       orders.append(OrderItem(2,1, 'taozhang', 1.05, 'CYN', 110.0, 100.0,
              '2017-12-10 00:00:00 UTC', 'OPEN'))
       return orders;

   def get_user_payment_methods(self, userId):
       payment_methods = []
       if (userId == 1):
           payment_method = UserPaymentMethod()
           user = User()
           user.id = 1
           provider = PaymentProvider()
           provider.code = 'heepay'
           provider.name = '汇钱包'
           payment_method.user = user
           payment_method.provider = provider
           payment_method.account_at_provider = '18600701961'
           payment_methods.append(payment_method)
       else:
           payment_method = UserPaymentMethod()
           user = User()
           user.id = 2
           provider = PaymentProvider()
           provider.code = 'heepay'
           provider.name = '汇钱包'
           payment_method.user = user
           payment_method.provider = provider
           payment_method.account_at_provider = '15811302702'
           payment_methods.append(payment_method)
       return payment_methods

   def register(self, user):
       if user.login.username=='failme':
           return -1, "系统故障，注册失败，稍后再试"
       else:
           return 0, "注册成功"

   def login(self, username, password):
       if username == 'taozhang' and password == '12345':
           user=User()
           user.login = UserLogin()
           user.id = 1
           user.login.username = 'taozhang'
           user.alias = 'Tao'
           return 0, '', user
       elif  username == 'yingzhou' and password == '12345':
           user=User()
           user.login = UserLogin()
           user.login.username = 'yingzhou'
           user.id = 2
           user.alias = 'Ying'
           return 0, '', user
       else :
           return -1, '密码或账号有错', None

   def get_user_accountInfo(self, username):
       user = User()
       user.login = UserLogin()
       user.id =1
       user.login.username = username
       payment_method = UserPaymentMethod()
       payment_provider = PaymentProvider()
       payment_provider.code = 'heepay'
       payment_provider.name = '汇钱包'
       payment_method.id = 1
       payment_method.provider = payment_provider
       payment_method.user = user
       payment_method.account_at_provider = '18600701961'

       payment_methods= []
       payment_methods.append(UserPaymentMethodView(payment_method.id, payment_provider.code,
            payment_provider.name,payment_method.account_at_provider,
            payment_method.provider_qrcode_image))
       payment_method.provider_qrcode_image = ''
       userInfo = UserAccountInfo(user.login, user.id, 1999, 0, 1999,
              'AHeeMMr4CqzxFTy3WGRgZnmE5ZoeyiA6vg',
              'AeALA1zBbzWCTsrbAzaEfLeLG6Q5ZEGfeD',
              '',
              payment_methods)
       return userInfo

   def get_user_address(self, userid):
       user_address = UserExternalWalletAddress()
       user = User()
       user.id = userid
       user_address.user = user
       user_address.address = 'AcQwZEx36Ru3gqkkgQiSJt6TngSnTQYFF8'
       user_address.alias = 'first'
       return user_address

   def upsert_user_external_address(self, userid, address, alias):
       return 0, ''

   def upsert_user_payment_method(self, userid, payment_provider, account):
       return 0, ''

   def create_sell_order(self, username, units, unit_price,
                  unit_price_currency, crypto):
       return 0, ''

   def get_open_sell_orders_by_user(self, username):
       orders = []
       orders.append(OrderItem(1,1, '', 1.011, 'CYN', 200.0,90.0,
              '2017-12-10 00:00:00 UTC', 'OPEN'))
       orders.append(OrderItem(2,1, '', 1.05, 'CYN', 110.0, 100.0,
              '2017-12-10 00:00:00 UTC', 'OPEN'))
       orders.append(OrderItem(3,1, '', 1.06, 'CYN', 120.0, 105.0,
              '2017-12-10 00:00:00 UTC', 'LOCKED'))
       orders.append(OrderItem(4,1, '', 1.07, 'CYN', 130.0, 108.0,
              '2017-12-10 00:00:00 UTC', 'LOCKED'))
       return orders;

   def get_pending_incoming_buy_orders_by_user(self, username):
       orders = []
       orders.append(OrderItem(1,1,'',1.011, 'CYN', 10.0, 0,
              '2017-12-10 00:00:00 UTC', 'OPEN'))
       orders.append(OrderItem(2,1,'', 1.05, 'CYN', 5.0, 0,
              '2017-12-10 00:00:00 UTC', 'PAID'))
       return orders;
   def confirm_payment(self, username, orderid):
       return 0

   def create_purchase_order(self, username, reference_order_id,
          quantity, unit_price, unit_price_currency, total_amount, cryptocurrency):
       userlogin = UserLogin()
       userlogin.username = username
       order = Order()
       order.order_type ='BUY'
       order.user = User()
       order.user.login= userlogin
       order.reference_order = Order()
       order.reference_order.order_id = reference_order_id
       frmt_date = dt.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y%m%d%H%M%S_%f")
       order.order_id = frmt_date
       order.cryptocurrency = Cryptocurrency()
       order.cryptocurrency.code = cryptocurrency
       order.units = quantity
       order.unit_price = unit_price
       order.unit_price_currency = unit_price_currency
       order.total_amount = total_amount
       return order
