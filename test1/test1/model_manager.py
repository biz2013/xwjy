from users.models import *
from views.viewlistitems import *
class ModelManager(object):

   def __init__():

   def create_sell_order(order):
      
   def query_active_sell_order_by_user(username):
       orders= []
       opened_order = OrderViewListItem(
          user_login = 'taozhang',
          user_id = 1,
          status = 'OPEN',
          units = 100.0,
          unit_price = 1.02,
          unit_price_currency='CYN'
          unit_balance = 50.0,
          unit_available = 50.0,
          lastupdated_at = '2017/12/1 10:22:33.000 CST')        
       locked_order =  OrderViewListItem(
          user_login = 'taozhang',
          user_id = 1,
          status = 'LOCKED',
          units = 100.0,
          unit_price = 1.02,
          unit_price_currency='CYN'       
          unit_balance = 50.0,
          unit_available = 30.0,
          lastupdated_at = '2017/11/30 10:22:33.000 CST')              
