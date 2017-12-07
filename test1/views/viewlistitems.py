
class OrderViewListItem(object):
   def __init__(self, id, order_owner_login, userid, status, units, unit_price,
       unit_price_currency, unit_balance,
       available_units, lastupdated_at):
       self.order_id = id,
       self.id = id
       self.owner_login = order_owner_login
       self.owner_user_id = userid
       self.status = status
       self.units = units
       self.unit_price = unit_price
       self.unit_price_currency= unit_price_currency
       self.unit_balance = unit_balance
       self.available_units = available_units
       self.lastupdated_at = lastupdated_at
