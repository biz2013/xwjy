
class OrderViewListItem(object):
   def __init__(login, userid, status, units, unit_price, 
       unit_price, unit_price_currency, unit_balance, 
       unit_avaiable, lastupdated_at):
       self.user_login = login
       self.user_id = userid
       self.status = status
       self.units = units
       self.unit_price = unit_price
       self.unit_price_currency= unit_price_currency       
       self.unit_balance = unit_balance
       self.unit_available = unit_available
       self.lastupdated_at = lastupdated_at 
