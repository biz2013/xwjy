from views.viewlistitems import *

class ModelManager(object):

   def query_active_sell_orders():
       orders= []
       opened_order = OrderViewListItem(
          owner_login = 'taozhang',
          onwer_user_id = 1,
          status = 'OPEN',
          units = 100.0,
          unit_price = 1.02,
          unit_price_currency='CYN',
          unit_balance = 50.0,
          available_units = 50.0,
          lastupdated_at = '2017/12/1 10:22:33.000 CST')
       locked_order =  OrderViewListItem(
          owner_login = 'taozhang',
          owner_user_id = 1,
          status = 'LOCKED',
          units = 100.0,
          unit_price = 1.02,
          unit_price_currency='CYN',
          unit_balance = 50.0,
          available_units = 30.0,
          lastupdated_at = '2017/11/30 10:22:33.000 CST')
