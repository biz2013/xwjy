#!/usr/bin/python
# -*- coding: utf-8 -*-
from users.models import *
from views.models.useraccountinfo import *

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
       payment_method = UserPaymentMethod()
       payment_provider = PaymentProvider()
       payment_provider.code = 'heepay'
       payment_provider.name = '汇钱包'
       payment_method.id = 1
       payment_method.provider = payment_provider
       payment_method.user = User()
       payment_method.account_at_provider = '18600701961'

       payment_method.provider_qrcode_image = ''
       userInfo = UserAccountInfo(username, 1999, 0, 1999,
              'AHeeMMr4CqzxFTy3WGRgZnmE5ZoeyiA6vg',
              'AeALA1zBbzWCTsrbAzaEfLeLG6Q5ZEGfeD',
              {payment_method})
       return userInfo
