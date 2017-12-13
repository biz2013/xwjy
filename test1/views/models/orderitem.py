class OrderItem(object):
   def __init__(self, order_id, owner_user_id, unit_price, unit_price_currency,
       total_units, available_units, lastmodified_at, status):
       self.order_id=order_id
       self.owner_user_id = owner_user_id
       self.unit_price = unit_price
       self.unit_price_currency= unit_price_currency
       self.total_units = total_units
       self.available_units = available_units
       self.lastmodified_at = lastmodified_at
       self.status = status
