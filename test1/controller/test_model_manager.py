#!/usr/bin/python
# -*- coding: utf-8 -*-
from views.viewlistitems import *
from views.sellorderview import *
from views.userpaymentmethodview import *

class ModelManager(object):

   def query_active_sell_orders(self):
       orders= []
       orders.append(OrderViewListItem(
          #order_id
          1,
          #owner_login
          'taozhang',
          #onwer_user_id
          1,
          #status
          'OPEN',
          #units
          100.0,
          #unit_price =
          1.02,
          #unit_price_currency=
          'CYN',
          #unit_balance =
          50.0,
          #available_units =
          50.0,
          #lastupdated_at =
          '2017/12/1 10:22:33.000 CST'))
       orders.append(OrderViewListItem(
          #order_id
          2,
          #owner_login =
          'taozhang',
          #owner_user_id =
          1,
          #status =
          'LOCKED',
          #units =
          100.0,
          #unit_price =
          1.01,
          #unit_price_currency=
          'CYN',
          #unit_balance =
          50.0,
          #available_units =
          30.0,
          #lastupdated_at =
          '2017/11/30 10:22:33.000 CST'))
       return orders;

   def get_user_payment_methods(self, userId):
       payment = []
       if (userId == 'taozhang'):
           payment.append(UserPaymentMethodView(1, '微信支付',
                   'taozhang_weixin_qrcode.jpg'))
       else:
           payment.append(UserPaymentMethodView(2, '支付宝',
                   'yingzhou_alipay_qrcode.png'))
       return payment

   def register(self, user):
       if user.username=='failme':
           return -1, "系统故障，注册失败，稍后再试"
       else:
           return 0, "注册成功"

   def login(self, username, password):
       if (username == 'taozhang' and password == '12345') or (username == 'yingzhou' and password == '12345'):
           return 0, '', User() 
