class SellOrderView(object):
   def __init__(self, order_id, owner_user_id, unit_price, unit_price_currency,
       available_units, owner_payment_methods):
       self.order_id=order_id
       self.owner_user_id = owner_user_id
       self.unit_price = unit_price
       self.units_price_currency= unit_price_currency
       self.available_units = available_units
       self.owner_payment_methods = owner_payment_methods
