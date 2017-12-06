from views.viewlistitems import *
from views.sellorderview import *
from views.userpaymentmethodview import *

class ModelManager(object):

   def query_active_sell_orders(self):
       orders= []
       orders.append(OrderViewListItem(
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
       if (userId == 'taozhang'):
           return [UserPaymentMethodView(1, 'weixin',
                   'taozhang_weixin_qrcode.jpg')]
       return [UserPaymentMethodView(2, 'alipay',
                   'yingzhou_alipay_qrcode.png')]
